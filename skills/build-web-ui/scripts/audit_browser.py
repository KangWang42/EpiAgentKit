#!/usr/bin/env python3
"""Audit rendered web pages with an existing Chromium browser and local CDP."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit


DEFAULT_VIEWPORTS = "desktop=1440x1000,mobile=390x844"
SENSITIVE_QUERY_PARTS = {"auth", "key", "password", "secret", "session", "token"}

PAGE_AUDIT_JS = r"""
(() => {
  const root = document.documentElement;
  const body = document.body;
  const ids = new Map();
  for (const element of document.querySelectorAll('[id]')) {
    const id = element.id;
    if (!id) continue;
    ids.set(id, (ids.get(id) || 0) + 1);
  }
  const duplicateIds = [...ids.entries()]
    .filter(([, count]) => count > 1)
    .map(([id, count]) => ({id, count}));
  const describe = (element) => ({
    tag: element.tagName.toLowerCase(),
    id: element.id || null,
    className: typeof element.className === 'string' ? element.className.slice(0, 160) : null,
    src: element.currentSrc || element.getAttribute('src') || null,
    alt: element.getAttribute('alt')
  });
  const images = [...document.images];
  const missingAlt = images.filter((image) => !image.hasAttribute('alt')).map(describe);
  const brokenImages = images
    .filter((image) => image.complete && image.naturalWidth === 0)
    .map(describe);
  const h1 = [...document.querySelectorAll('h1')];
  const maxScrollWidth = Math.max(
    root ? root.scrollWidth : 0,
    body ? body.scrollWidth : 0
  );
  const round = (value) => Math.round(value * 100) / 100;
  const label = (element) => {
    const tag = element.tagName.toLowerCase();
    const id = element.id ? `#${element.id}` : '';
    const classes = (element.getAttribute('class') || '')
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 3)
      .map((name) => `.${name}`)
      .join('');
    return `${tag}${id}${classes}`.slice(0, 200);
  };
  const visibleRect = (element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    if (
      style.display === 'none'
      || style.visibility === 'hidden'
      || style.visibility === 'collapse'
      || rect.width <= 0
      || rect.height <= 0
    ) return null;
    return {style, rect};
  };
  const viewportWidth = root ? root.clientWidth : window.innerWidth;
  const layoutNodes = [
    body,
    ...document.querySelectorAll(
      'body > :not(script):not(style), header, main, footer, nav, article, '
      + '[role="main"], main > section, main > article, main > div, '
      + '[role="main"] > section, [role="main"] > article, [role="main"] > div, '
      + '[data-audit-layout]'
    )
  ];
  const seenLayoutNodes = new Set();
  const layoutSamples = [];
  for (const element of layoutNodes) {
    if (!element || seenLayoutNodes.has(element)) continue;
    seenLayoutNodes.add(element);
    const visible = visibleRect(element);
    if (!visible) continue;
    const {style, rect} = visible;
    const inlineStartGap = rect.left;
    const inlineEndGap = viewportWidth - rect.right;
    layoutSamples.push({
      element: label(element),
      auditRole: element.getAttribute('data-audit-layout') || null,
      rect: {
        left: round(rect.left),
        right: round(rect.right),
        top: round(rect.top),
        width: round(rect.width),
        height: round(rect.height)
      },
      inlineGaps: {
        start: round(inlineStartGap),
        end: round(inlineEndGap),
        delta: round(inlineStartGap - inlineEndGap)
      },
      centerOffset: round((rect.left + rect.width / 2) - viewportWidth / 2),
      box: {
        display: style.display,
        position: style.position,
        marginInlineStart: style.marginInlineStart,
        marginInlineEnd: style.marginInlineEnd,
        paddingInlineStart: style.paddingInlineStart,
        paddingInlineEnd: style.paddingInlineEnd,
        minWidth: style.minWidth,
        maxWidth: style.maxWidth,
        overflowX: style.overflowX,
        transform: style.transform === 'none' ? null : style.transform
      }
    });
    if (layoutSamples.length >= 60) break;
  }
  const findHorizontalScroller = (element) => {
    for (let current = element.parentElement; current && current !== body; current = current.parentElement) {
      const style = getComputedStyle(current);
      if (
        ['auto', 'scroll'].includes(style.overflowX)
        && current.scrollWidth > current.clientWidth + 1
      ) return label(current);
    }
    return null;
  };
  const edgeClippedContent = [];
  for (const element of document.querySelectorAll(
    'h1, h2, h3, h4, p, li, a, button, input, select, textarea, label, table, img, video, canvas, svg'
  )) {
    const visible = visibleRect(element);
    if (!visible) continue;
    const {rect} = visible;
    if (rect.left >= -1 && rect.right <= viewportWidth + 1) continue;
    edgeClippedContent.push({
      element: label(element),
      rect: {
        left: round(rect.left),
        right: round(rect.right),
        top: round(rect.top),
        width: round(rect.width),
        height: round(rect.height)
      },
      interactive: element.matches('a, button, input, select, textarea'),
      horizontalScroller: findHorizontalScroller(element)
    });
    if (edgeClippedContent.length >= 40) break;
  }
  return {
    url: location.href,
    title: document.title,
    readyState: document.readyState,
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    devicePixelRatio: window.devicePixelRatio,
    clientWidth: root ? root.clientWidth : null,
    scrollWidth: root ? root.scrollWidth : null,
    bodyScrollWidth: body ? body.scrollWidth : null,
    horizontalOverflow: root ? maxScrollWidth > root.clientWidth + 1 : null,
    scrollX: window.scrollX,
    scrollY: window.scrollY,
    h1Count: h1.length,
    h1Text: h1.map((item) => item.textContent.trim().slice(0, 200)),
    duplicateIds,
    missingAlt,
    brokenImages,
    imageCount: images.length,
    fontStatus: document.fonts ? document.fonts.status : null,
    layoutGeometry: {
      viewportWidth,
      samples: layoutSamples,
      edgeClippedContent
    }
  };
})()
"""


class BrowserAuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int
    mobile: bool


def parse_viewports(value: str) -> list[Viewport]:
    viewports: list[Viewport] = []
    names: set[str] = set()
    for raw in value.split(","):
        match = re.fullmatch(
            r"\s*([a-zA-Z0-9_-]+)=(\d{2,5})x(\d{2,5})(?::(mobile|desktop))?\s*",
            raw,
        )
        if not match:
            raise argparse.ArgumentTypeError(
                f"Invalid viewport {raw!r}; expected name=WIDTHxHEIGHT[:mobile|desktop]"
            )
        name, width_text, height_text, mode = match.groups()
        if name in names:
            raise argparse.ArgumentTypeError(f"Duplicate viewport name: {name}")
        names.add(name)
        width = int(width_text)
        height = int(height_text)
        if width < 240 or height < 240:
            raise argparse.ArgumentTypeError(f"Viewport is too small: {name}={width}x{height}")
        mobile = mode == "mobile" or (mode is None and width <= 600)
        viewports.append(Viewport(name, width, height, mobile))
    if not viewports:
        raise argparse.ArgumentTypeError("At least one viewport is required")
    return viewports


def validate_urls(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise BrowserAuditError(f"Only absolute http/https URLs are supported: {value}")
        if parsed.username or parsed.password:
            raise BrowserAuditError("URLs containing embedded credentials are not accepted")
        sensitive = [
            key
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
            if any(part in key.lower() for part in SENSITIVE_QUERY_PARTS)
        ]
        if sensitive:
            raise BrowserAuditError(
                "URL query contains a credential-like key; use a safe local preview state instead: "
                + ", ".join(sorted(set(sensitive)))
            )
        result.append(value)
    return result


def browser_candidates() -> list[Path]:
    candidates: list[Path] = []
    for command in ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    if sys.platform == "win32":
        candidates.extend(Path(path) for path in (
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ))
    elif sys.platform == "darwin":
        candidates.extend(Path(path) for path in (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ))
    seen: set[Path] = set()
    available: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            available.append(candidate)
    return available


def find_browser(explicit: Path | None) -> Path:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_file():
            raise BrowserAuditError(f"Browser executable not found: {candidate}")
        return candidate
    candidates = browser_candidates()
    if not candidates:
        raise BrowserAuditError(
            "No Chromium browser found. Install nothing automatically; pass --browser for an existing executable."
        )
    return candidates[0]


def read_json_url(url: str, timeout: float = 2.0) -> object:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_devtools(profile: Path, process: subprocess.Popen[bytes], timeout: float) -> tuple[int, str]:
    marker = profile / "DevToolsActivePort"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise BrowserAuditError(f"Browser exited before CDP became ready (exit {process.returncode})")
        if marker.is_file():
            lines = marker.read_text(encoding="utf-8", errors="replace").splitlines()
            if len(lines) >= 2 and lines[0].isdigit():
                return int(lines[0]), lines[1]
        time.sleep(0.05)
    raise BrowserAuditError("Timed out waiting for the browser CDP endpoint")


def wait_for_page_target(port: int, timeout: float) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            targets = read_json_url(f"http://127.0.0.1:{port}/json/list")
            if isinstance(targets, list):
                for target in targets:
                    if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                        return target
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            last_error = error
        time.sleep(0.05)
    detail = f": {last_error}" if last_error else ""
    raise BrowserAuditError(f"No inspectable page target became available{detail}")


class WebSocket:
    def __init__(self, url: str, timeout: float = 10.0) -> None:
        parsed = urlsplit(url)
        if parsed.scheme != "ws" or not parsed.hostname:
            raise BrowserAuditError(f"Unsupported CDP WebSocket URL: {url}")
        port = parsed.port or 80
        self.socket = socket.create_connection((parsed.hostname, port), timeout=timeout)
        self.socket.settimeout(timeout)
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        self.socket.sendall(request)
        response = self._read_headers()
        status = response.split(b"\r\n", 1)[0]
        if b" 101 " not in status:
            self.socket.close()
            raise BrowserAuditError(f"CDP WebSocket handshake failed: {status.decode('ascii', 'replace')}")
        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        )
        headers = {
            line.split(b":", 1)[0].strip().lower(): line.split(b":", 1)[1].strip()
            for line in response.split(b"\r\n")[1:]
            if b":" in line
        }
        if headers.get(b"sec-websocket-accept") != expected:
            self.socket.close()
            raise BrowserAuditError("CDP WebSocket handshake returned an invalid accept key")

    def _read_headers(self) -> bytes:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise BrowserAuditError("CDP WebSocket closed during handshake")
            data.extend(chunk)
            if len(data) > 65536:
                raise BrowserAuditError("CDP WebSocket handshake headers are too large")
        return bytes(data)

    def _read_exact(self, size: int) -> bytes:
        data = bytearray()
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                raise BrowserAuditError("CDP WebSocket closed unexpectedly")
            data.extend(chunk)
        return bytes(data)

    def _send_frame(self, payload: bytes, opcode: int) -> None:
        mask = secrets.token_bytes(4)
        length = len(payload)
        header = bytearray([0x80 | opcode])
        if length < 126:
            header.append(0x80 | length)
        elif length <= 65535:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.socket.sendall(bytes(header) + mask + masked)

    def send_json(self, value: object) -> None:
        self._send_frame(json.dumps(value, separators=(",", ":")).encode("utf-8"), 0x1)

    def receive_text(self, timeout: float) -> str:
        self.socket.settimeout(timeout)
        fragments = bytearray()
        message_opcode: int | None = None
        while True:
            first, second = self._read_exact(2)
            final = bool(first & 0x80)
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else b""
            payload = self._read_exact(length)
            if masked:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x8:
                raise BrowserAuditError("CDP WebSocket closed")
            if opcode == 0x9:
                self._send_frame(payload, 0xA)
                continue
            if opcode == 0xA:
                continue
            if opcode in {0x1, 0x2}:
                message_opcode = opcode
                fragments = bytearray(payload)
            elif opcode == 0x0 and message_opcode is not None:
                fragments.extend(payload)
            else:
                continue
            if final:
                if message_opcode != 0x1:
                    raise BrowserAuditError("Unexpected binary CDP WebSocket message")
                return fragments.decode("utf-8")

    def close(self) -> None:
        try:
            self._send_frame(b"", 0x8)
        except OSError:
            pass
        self.socket.close()


class CDPClient:
    def __init__(self, url: str, timeout: float) -> None:
        self.websocket = WebSocket(url, timeout)
        self.timeout = timeout
        self.next_id = 1
        self.events: list[dict[str, object]] = []

    def _receive(self, timeout: float) -> dict[str, object]:
        message = json.loads(self.websocket.receive_text(timeout))
        if "method" in message:
            self.events.append(message)
        return message

    def call(self, method: str, params: dict[str, object] | None = None) -> dict[str, object]:
        identity = self.next_id
        self.next_id += 1
        self.websocket.send_json({"id": identity, "method": method, "params": params or {}})
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                message = self._receive(max(0.05, deadline - time.monotonic()))
            except socket.timeout as error:
                raise BrowserAuditError(f"CDP method timed out: {method}") from error
            if message.get("id") != identity:
                continue
            if "error" in message:
                raise BrowserAuditError(f"CDP method failed ({method}): {message['error']}")
            result = message.get("result", {})
            return result if isinstance(result, dict) else {}
        raise BrowserAuditError(f"CDP method timed out: {method}")

    def drain(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                self._receive(min(0.1, max(0.01, deadline - time.monotonic())))
            except socket.timeout:
                continue

    def close(self) -> None:
        self.websocket.close()


def evaluate_value(client: CDPClient, expression: str) -> object:
    result = client.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
            "userGesture": False,
        },
    )
    exception = result.get("exceptionDetails")
    if exception:
        raise BrowserAuditError(f"Page evaluation failed: {exception}")
    remote = result.get("result", {})
    return remote.get("value") if isinstance(remote, dict) else None


def wait_for_ready(client: CDPClient, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if evaluate_value(client, "document.readyState") == "complete":
            client.drain(0.35)
            return
        client.drain(0.05)
    raise BrowserAuditError("Page did not reach document.readyState=complete")


def format_remote_argument(argument: object) -> str:
    if not isinstance(argument, dict):
        return str(argument)
    if "value" in argument:
        value = argument["value"]
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    return str(argument.get("description") or argument.get("type") or "")


def collect_runtime_findings(events: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    requests: dict[str, str] = {}
    console: list[dict[str, object]] = []
    exceptions: list[dict[str, object]] = []
    log_entries: list[dict[str, object]] = []
    http_failures: list[dict[str, object]] = []
    network_failures: list[dict[str, object]] = []

    for event in events:
        method = event.get("method")
        params = event.get("params", {})
        if not isinstance(params, dict):
            continue
        if method == "Network.requestWillBeSent":
            request = params.get("request", {})
            if isinstance(request, dict):
                requests[str(params.get("requestId", ""))] = str(request.get("url", ""))
        elif method == "Network.responseReceived":
            response = params.get("response", {})
            if isinstance(response, dict) and int(response.get("status", 0)) >= 400:
                http_failures.append({
                    "status": response.get("status"),
                    "url": response.get("url"),
                    "type": params.get("type"),
                })
        elif method == "Network.loadingFailed":
            request_id = str(params.get("requestId", ""))
            network_failures.append({
                "url": requests.get(request_id),
                "type": params.get("type"),
                "errorText": params.get("errorText"),
                "canceled": bool(params.get("canceled", False)),
            })
        elif method == "Runtime.consoleAPICalled":
            console.append({
                "type": params.get("type"),
                "text": " ".join(format_remote_argument(item) for item in params.get("args", [])),
            })
        elif method == "Runtime.exceptionThrown":
            details = params.get("exceptionDetails", {})
            if isinstance(details, dict):
                exceptions.append({
                    "text": details.get("text"),
                    "url": details.get("url"),
                    "lineNumber": details.get("lineNumber"),
                    "columnNumber": details.get("columnNumber"),
                })
        elif method == "Log.entryAdded":
            entry = params.get("entry", {})
            if isinstance(entry, dict):
                log_entries.append({
                    "level": entry.get("level"),
                    "source": entry.get("source"),
                    "text": entry.get("text"),
                    "url": entry.get("url"),
                })

    return {
        "console": console,
        "exceptions": exceptions,
        "logEntries": log_entries,
        "httpFailures": http_failures,
        "networkFailures": network_failures,
    }


def scenario_issues(
    audit: dict[str, object],
    runtime: dict[str, list[dict[str, object]]],
    viewport: Viewport,
    strict: bool,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    def add(code: str, message: str) -> None:
        issues.append({"code": code, "message": message})

    inner_width = audit.get("innerWidth")
    client_width = audit.get("clientWidth")
    if not isinstance(inner_width, (int, float)) or abs(inner_width - viewport.width) > 1:
        add("viewport-inner-width", f"innerWidth={inner_width}, expected {viewport.width}")
    if viewport.mobile:
        client_mismatch = (
            not isinstance(client_width, (int, float))
            or abs(client_width - viewport.width) > 1
        )
    else:
        client_mismatch = (
            not isinstance(client_width, (int, float))
            or client_width > viewport.width + 1
            or client_width < viewport.width - 32
        )
    if client_mismatch:
        expectation = (
            str(viewport.width)
            if viewport.mobile
            else f"{viewport.width} minus at most a normal scrollbar"
        )
        add("viewport-client-width", f"clientWidth={client_width}, expected {expectation}")
    if audit.get("horizontalOverflow"):
        add(
            "horizontal-overflow",
            f"clientWidth={client_width}, scrollWidth={audit.get('scrollWidth')}, bodyScrollWidth={audit.get('bodyScrollWidth')}",
        )
    if audit.get("h1Count") != 1:
        add("h1-count", f"Expected one h1, found {audit.get('h1Count')}")
    for field, code in (
        ("duplicateIds", "duplicate-id"),
        ("missingAlt", "image-alt"),
        ("brokenImages", "broken-image"),
    ):
        values = audit.get(field)
        if isinstance(values, list) and values:
            add(code, f"Found {len(values)} item(s)")
    error_console = [item for item in runtime["console"] if item.get("type") in {"error", "assert"}]
    error_logs = [item for item in runtime["logEntries"] if item.get("level") == "error"]
    if error_console:
        add("console-error", f"Found {len(error_console)} console error/assert event(s)")
    if runtime["exceptions"]:
        add("runtime-exception", f"Found {len(runtime['exceptions'])} uncaught exception(s)")
    if error_logs:
        add("browser-log-error", f"Found {len(error_logs)} browser log error(s)")
    if runtime["httpFailures"]:
        add("http-failure", f"Found {len(runtime['httpFailures'])} HTTP response(s) with status >= 400")
    if runtime["networkFailures"]:
        add("network-failure", f"Found {len(runtime['networkFailures'])} failed request(s)")
    if strict:
        warnings = [item for item in runtime["console"] if item.get("type") == "warning"]
        warning_logs = [item for item in runtime["logEntries"] if item.get("level") == "warning"]
        if warnings or warning_logs:
            add("browser-warning", f"Found {len(warnings) + len(warning_logs)} browser warning(s) in strict mode")
    return issues


def slug_for_url(url: str, index: int) -> str:
    parsed = urlsplit(url)
    raw = f"{parsed.netloc}{parsed.path}-{parsed.fragment}".strip("-/") or "page"
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-").lower()[:60] or "page"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{index:02d}-{slug}-{digest}"


def capture_scenario(
    client: CDPClient,
    url: str,
    viewport: Viewport,
    output: Path,
    stem: str,
    timeout: float,
    strict: bool,
    full_page: bool,
) -> dict[str, object]:
    client.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": viewport.width,
            "height": viewport.height,
            "deviceScaleFactor": 1,
            "mobile": viewport.mobile,
            "screenWidth": viewport.width,
            "screenHeight": viewport.height,
        },
    )
    client.call(
        "Emulation.setTouchEmulationEnabled",
        {"enabled": viewport.mobile, "maxTouchPoints": 5 if viewport.mobile else 1},
    )
    event_start = len(client.events)
    navigation = client.call("Page.navigate", {"url": url})
    if navigation.get("errorText"):
        raise BrowserAuditError(f"Navigation failed: {navigation['errorText']}")
    wait_for_ready(client, timeout)
    evaluate_value(
        client,
        """
        (() => {
          if (!location.hash) { window.scrollTo(0, 0); return true; }
          const id = decodeURIComponent(location.hash.slice(1));
          const target = document.getElementById(id) || document.querySelector(`[name="${CSS.escape(id)}"]`);
          if (target) target.scrollIntoView({block: 'start', inline: 'nearest'});
          return Boolean(target);
        })()
        """,
    )
    client.drain(0.2)
    audit_value = evaluate_value(client, PAGE_AUDIT_JS)
    if not isinstance(audit_value, dict):
        raise BrowserAuditError("Rendered page audit did not return an object")
    screenshot_params: dict[str, object] = {
        "format": "png",
        "fromSurface": True,
        "captureBeyondViewport": full_page,
    }
    if full_page:
        metrics = client.call("Page.getLayoutMetrics")
        size = metrics.get("cssContentSize") or metrics.get("contentSize")
        if isinstance(size, dict):
            width = min(float(size.get("width", viewport.width)), 16384.0)
            height = min(float(size.get("height", viewport.height)), 16384.0)
            screenshot_params["clip"] = {"x": 0, "y": 0, "width": width, "height": height, "scale": 1}
    screenshot = client.call("Page.captureScreenshot", screenshot_params)
    data = screenshot.get("data")
    if not isinstance(data, str):
        raise BrowserAuditError("Browser did not return screenshot data")
    screenshot_name = f"{stem}-{viewport.name}.png"
    (output / screenshot_name).write_bytes(base64.b64decode(data))
    runtime = collect_runtime_findings(client.events[event_start:])
    issues = scenario_issues(audit_value, runtime, viewport, strict)
    return {
        "ok": not issues,
        "requestedUrl": url,
        "viewport": asdict(viewport),
        "screenshot": screenshot_name,
        "page": audit_value,
        "runtime": runtime,
        "issues": issues,
        "manualChecksRequired": [
            "visual hierarchy and optical balance across the page shell, sections, and components",
            "layoutGeometry inline gaps and center offsets, including intentional asymmetry and clipped content",
            "keyboard order, focus visibility, dialogs, errors, and back navigation",
            "touch-equivalent interaction and reduced-motion behavior",
            "WCAG contrast for real backgrounds and interactive states",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="Absolute http/https URLs; use query/hash for reproducible states")
    parser.add_argument("--output", type=Path, required=True, help="Directory for JSON and PNG evidence")
    parser.add_argument("--browser", type=Path, help="Existing Chrome, Edge, or Chromium executable")
    parser.add_argument("--viewports", type=parse_viewports, default=parse_viewports(DEFAULT_VIEWPORTS))
    parser.add_argument("--timeout", type=float, default=15.0, help="Browser and page timeout in seconds")
    parser.add_argument("--strict", action="store_true", help="Treat browser warnings as issues")
    parser.add_argument("--full-page", action="store_true", help="Capture a bounded full-page screenshot instead of the current viewport")
    parser.add_argument("--ignore-certificate-errors", action="store_true", help="Allow invalid certificates only for an explicitly trusted preview")
    return parser.parse_args()


def terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    args = parse_args()
    if args.timeout <= 0 or args.timeout > 120:
        print("ERROR: --timeout must be greater than 0 and no more than 120 seconds", file=sys.stderr)
        return 2
    try:
        urls = validate_urls(args.urls)
        browser = find_browser(args.browser)
    except BrowserAuditError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    profile = output / ".cdp-profile"
    if profile.exists():
        print(f"ERROR: Temporary browser profile already exists: {profile}", file=sys.stderr)
        return 2
    profile.mkdir()
    command = [
        str(browser),
        "--headless=new",
        "--remote-debugging-port=0",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-extensions",
        "about:blank",
    ]
    if args.ignore_certificate_errors:
        command.insert(-1, "--ignore-certificate-errors")

    process: subprocess.Popen[bytes] | None = None
    client: CDPClient | None = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port, _ = wait_for_devtools(profile, process, args.timeout)
        target = wait_for_page_target(port, args.timeout)
        client = CDPClient(str(target["webSocketDebuggerUrl"]), args.timeout)
        for domain in ("Page", "Runtime", "Network", "Log"):
            client.call(f"{domain}.enable")
        version = client.call("Browser.getVersion")

        scenarios: list[dict[str, object]] = []
        for index, url in enumerate(urls, start=1):
            stem = slug_for_url(url, index)
            for viewport in args.viewports:
                scenarios.append(
                    capture_scenario(
                        client,
                        url,
                        viewport,
                        output,
                        stem,
                        args.timeout,
                        args.strict,
                        args.full_page,
                    )
                )

        issue_count = sum(len(item["issues"]) for item in scenarios)
        report = {
            "ok": issue_count == 0,
            "browser": {
                "executable": str(browser),
                "product": version.get("product"),
                "userAgent": version.get("userAgent"),
                "protocolVersion": version.get("protocolVersion"),
            },
            "viewports": [asdict(item) for item in args.viewports],
            "scenarios": scenarios,
            "summary": {
                "scenarioCount": len(scenarios),
                "passed": sum(bool(item["ok"]) for item in scenarios),
                "failed": sum(not bool(item["ok"]) for item in scenarios),
                "issueCount": issue_count,
            },
        }
        report_path = output / "browser-audit.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"report={report_path}")
        print(f"scenarios={len(scenarios)} issues={issue_count}")
        return 0 if report["ok"] else 1
    except (BrowserAuditError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    finally:
        if client is not None:
            try:
                client.close()
            except (BrowserAuditError, OSError):
                pass
        if process is not None:
            try:
                terminate_process(process)
            except OSError:
                pass
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
