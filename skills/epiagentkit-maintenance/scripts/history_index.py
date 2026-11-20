#!/usr/bin/env python3
"""Incremental, local-only SQLite FTS5 index for Claude Code, Codex, and Antigravity histories.

Source history JSONL files are strictly read-only. The derived SQLite cache is
disposable, rebuildable, redacted for common secrets, and never stored inside a
skills directory or Git repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = 1
APPLICATION_ID = 0x45504948  # "EPIH"
SCRIPT = Path(__file__).resolve()
DEFAULT_CACHE_DIR = Path.home() / ".epiagentkit" / "cache"
DB_NAME = "history-index.sqlite"

SKIP_EXACT = {
    "继续", "好的", "好", "可以", "行", "ok", "yes", "y", "n", "no",
    "1", "2", "3", "同意", "确认", "执行", "开始", "提交", "push", "commit",
    "谢谢", "thanks", "thx", "收到", "明白",
}

PASTE_NOISE_RE = re.compile(
    r"(```|https?://localhost:\d+|net::ERR_|Traceback \(most recent call last\)|<system-reminder>|<USER_REQUEST>)",
    re.I,
)

REPO_MAINT_RE = re.compile(
    r"(EpiAgentKit|epiagentkit-maintenance|audit_workflow_contracts|audit_skill_contracts|build_release|sync --target|doctor --target|\$skill-creator)",
    re.I,
)

DOMAINS: list[tuple[str, re.Pattern[str]]] = [
    ("writing_paper", re.compile(r"(论文|正文|摘要|引言|方法学|结果部分|讨论|审稿|返修|投稿|润色|去ai|ai味|口吻|学术|文献综述|word|docx|范文|期刊|manuscript|discussion|introduction|methods|abstract|cover letter)", re.I)),
    ("opening_report", re.compile(r"(开题|开题报告|学位论文|答辩书|技术路线|研究方案|protocol|sap)", re.I)),
    ("ppt_slides", re.compile(r"(ppt|pptx|幻灯片|汇报|组会|答辩|中大模板|sysu|封面|页数|目录页|过渡页|排版|母版)", re.I)),
    ("figures_stats", re.compile(r"(森林图|生存曲线|km|roc|热图|散点图|箱线图|小提琴|柱状图|ggplot|matplotlib|出图|配图|图注|图例|dpi|坐标轴|统计图|画图|重画)", re.I)),
    ("visuals_diagram", re.compile(r"(流程图|机制图|框架图|结构图|图形摘要|imagegen|svg|示意图|插图|架构图|主视觉|概念图|视觉)", re.I)),
    ("r_python_analysis", re.compile(r"(r脚本|r语言|r代码|python|cox|回归|logistic|生存分析|队列|清洗|缺失|多重插补|中介|meta|倾向性|psm|敏感性分析|基线表|table ?1|table1|三线表|rds|results\.yaml|建模|模型)", re.I)),
    ("xlsx_office", re.compile(r"(xlsx|xlsm|excel|csv|tsv|冻结窗格|筛选|单元格|工作表|批注|pdf|ocr|word|修订)", re.I)),
    ("web_ui", re.compile(r"(网页|网站|前端|web|ui|html|css|react|vue|按钮|页面|移动端|响应式|浏览器|部署|接口|后台|看板|dashboard)", re.I)),
    ("literature_evidence", re.compile(r"(文献|doi|pmid|pubmed|引文|参考文献|指南|检索|核验|引用|chatgpt)", re.I)),
    ("report_consulting", re.compile(r"(报告|交付|咨询|备忘录|纪要|总结|汇报材料|述职)", re.I)),
]

SIGNALS: list[tuple[str, re.Pattern[str]]] = [
    ("overcomplete_bloat", re.compile(r"(不需要|不用|没必要|不要加|不要自动|不要追加|太长|太多|太复杂|太啰嗦|太繁琐|别搞|别建|别写|精简|简化|压缩|砍掉|删掉|去掉|多余|过度|臃肿|太满|太重|只要|只改|只需要|只做|局部|轻量|简单点|简洁)", re.I)),
    ("unneeded_asking_slow", re.compile(r"(别问|不用问|不要问|直接做|直接改|直接给|直接运行|直接执行|怎么这么慢|太慢|磨蹭|浪费时间|绕弯|直接一点|一步到位|不要停|别停)", re.I)),
    ("wrong_fit_style", re.compile(r"(不符合|不像|太假|ai味|ai感|太生硬|太机械|模板感|套话|太丑|不好看|不自然|不合适|不贴合|不对味|偏题|答非所问|理解错|不是我要的|跟我要的不一样)", re.I)),
    ("over_defensive_process", re.compile(r"(防备|解释太多|过程痕迹|不要解释|别解释|别写过程|不要自述|不要交代|别铺垫|别总结|别列清单|不要检查清单|少废话)", re.I)),
    ("visual_layout_issue", re.compile(r"(遮挡|重叠|溢出|挤|太小|看不清|居中|对齐|留白|乱码|字太小|比例|拉伸|裁切|颜色|配色|太花|太杂|丑|模糊|变形|错字)", re.I)),
    ("data_method_mismatch", re.compile(r"(数字不对|不一致|口径|变量|漏了|少算|算错|没跑|报错|失败|未更新|旧版|没同步|乱改|改坏|别动|不要改其他)", re.I)),
    ("efficiency_reuse", re.compile(r"(高效|长久|增量|缓存|索引|复用|硬来|重复扫描|每次都读)", re.I)),
    ("preference_directive", re.compile(r"(我希望|我需要|我要的是|以后|记住|原则上|默认|核心是|重点是|符合我的|适合|合适|按我说的|按这个来|风格要|工作风格)", re.I)),
]

SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<![A-Za-z0-9_])(sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{16,}|gho_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,})(?![A-Za-z0-9_])"), "[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(?<![A-Za-z0-9_])(Bearer\s+)[A-Za-z0-9._-]{12,}"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(?<![A-Za-z0-9_])(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*['\"]?[^\s'\",;]{6,}['\"]?"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)https?://[^/\s:@]+:[^/\s@]+@"), "https://[REDACTED]@"),
    (re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+\\"), "~/"),
    (re.compile(r"/Users/[^/\s]+/|/home/[^/\s]+/"), "~/"),
]


def is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def tokenize_terms(text: str) -> str:
    """Tokenize ASCII words and overlapping Chinese bigrams for FTS5 without external packages."""
    result: list[str] = []
    for token in re.findall(r"[\u3400-\u9fff]+|[a-z0-9_]+", text.lower()):
        if "\u3400" <= token[0] <= "\u9fff":
            result.extend(token[i:i + 2] for i in range(max(1, len(token) - 1)))
        else:
            result.append(token)
    return " ".join(dict.fromkeys(result))


def redact_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    for pattern, repl in SECRET_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    return cleaned


def parse_timestamp(value: object) -> int:
    if isinstance(value, (int, float)):
        return int(value / 1000.0) if value > 1e12 else int(value)
    if isinstance(value, str) and value.strip():
        try:
            return int(datetime.fromisoformat(value.strip().replace("Z", "+00:00")).timestamp())
        except ValueError:
            return 0
    return 0


def format_iso(ts_epoch: int) -> str:
    if ts_epoch <= 0:
        return "1970-01-01"
    return datetime.fromtimestamp(ts_epoch, tz=timezone.utc).astimezone().strftime("%Y-%m-%d")


def parse_since_arg(value: str) -> int:
    text = value.strip()
    try:
        if len(text) == 10:
            dt = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError as exc:
        raise SystemExit(f"Invalid --since date/timestamp: {value!r} (expected YYYY-MM-DD or ISO-8601)") from exc


def classify_domain(text: str) -> str:
    if REPO_MAINT_RE.search(text):
        return "epiagentkit_meta"
    for name, pattern in DOMAINS:
        if pattern.search(text):
            return name
    return "other"


def classify_signals(text: str) -> list[str]:
    return [name for name, pattern in SIGNALS if pattern.search(text)]


def is_noise_entry(redacted: str, raw_len: int) -> int:
    if not redacted or len(redacted) < 8 or raw_len > 450:
        return 1
    if redacted.startswith("/") or redacted.lower() in SKIP_EXACT:
        return 1
    if PASTE_NOISE_RE.search(redacted):
        return 1
    return 0


def hash_project(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:10]


def resolve_sources(args: argparse.Namespace) -> dict[str, Path]:
    home = Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
    mapping = {
        "cc": Path(args.claude_history).expanduser() if args.claude_history else home / ".claude" / "history.jsonl",
        "codex": Path(args.codex_history).expanduser() if args.codex_history else home / ".codex" / "history.jsonl",
        "agy": Path(args.agy_history).expanduser() if args.agy_history else home / ".gemini" / "antigravity-cli" / "history.jsonl",
    }
    return mapping


def resolve_db_path(cache_dir_arg: str | None) -> Path:
    cache_dir = Path(cache_dir_arg).expanduser().resolve() if cache_dir_arg else DEFAULT_CACHE_DIR.resolve()
    parts_lower = {p.lower() for p in cache_dir.parts}
    if "skills" in parts_lower and (cache_dir.name.lower() == "skills" or "epiagentkit-maintenance" in parts_lower):
        raise SystemExit(f"Refusing to place derived history cache inside a skills directory: {cache_dir}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / DB_NAME


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA application_id={APPLICATION_ID}")
    conn.execute(f"PRAGMA user_version={SCHEMA}")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            client TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            byte_offset INTEGER NOT NULL,
            line_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            line_no INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            ts_epoch INTEGER NOT NULL,
            ts_iso TEXT NOT NULL,
            project_hash TEXT NOT NULL,
            char_len INTEGER NOT NULL,
            domain TEXT NOT NULL,
            signals TEXT NOT NULL,
            is_noise INTEGER NOT NULL,
            text_redacted TEXT NOT NULL,
            UNIQUE(client, line_no)
        );

        CREATE INDEX IF NOT EXISTS idx_entries_ts ON entries(ts_epoch);
        CREATE INDEX IF NOT EXISTS idx_entries_domain ON entries(domain, is_noise, ts_epoch);
        CREATE INDEX IF NOT EXISTS idx_entries_client ON entries(client, ts_epoch);

        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            entry_id UNINDEXED,
            client UNINDEXED,
            domain UNINDEXED,
            terms,
            tokenize='unicode61'
        );

        CREATE TABLE IF NOT EXISTS checkpoints (
            name TEXT PRIMARY KEY,
            ts_epoch INTEGER NOT NULL,
            ts_iso TEXT NOT NULL,
            note TEXT NOT NULL
        );
        """
    )


def open_db(db_path: Path, rebuild: bool = False) -> sqlite3.Connection:
    if rebuild and db_path.exists():
        for suffix in ("", "-wal", "-shm"):
            target = Path(str(db_path) + suffix)
            if target.exists():
                target.unlink()
    try:
        conn = sqlite3.connect(str(db_path))
        app_id = conn.execute("PRAGMA application_id").fetchone()[0]
        user_ver = conn.execute("PRAGMA user_version").fetchone()[0]
        if app_id not in (0, APPLICATION_ID) or (app_id == APPLICATION_ID and user_ver != SCHEMA):
            conn.close()
            if rebuild:
                db_path.unlink(missing_ok=True)
                conn = sqlite3.connect(str(db_path))
            else:
                raise SystemExit(
                    f"Incompatible history cache schema at {db_path}; run with --rebuild to recreate."
                )
        init_schema(conn)
        return conn
    except sqlite3.DatabaseError as exc:
        if rebuild:
            db_path.unlink(missing_ok=True)
            conn = sqlite3.connect(str(db_path))
            init_schema(conn)
            return conn
        raise SystemExit(f"Corrupted history cache at {db_path}: {exc}. Re-run with --rebuild.") from exc


def parse_client_record(client: str, data: dict) -> tuple[str, int, str, str] | None:
    if client == "cc":
        raw_text = str(data.get("display") or "").strip()
        ts_epoch = parse_timestamp(data.get("timestamp", 0))
        session_id = str(data.get("sessionId") or "")
        project = str(data.get("project") or "")
    elif client == "codex":
        raw_text = str(data.get("text") or "").strip()
        ts_epoch = parse_timestamp(data.get("ts", 0))
        session_id = str(data.get("session_id") or "")
        project = str(data.get("cwd") or data.get("project") or "")
    else:
        raw_text = str(data.get("display") or data.get("text") or "").strip()
        ts_epoch = parse_timestamp(data.get("timestamp", data.get("ts", 0)))
        session_id = str(data.get("conversationId") or data.get("session_id") or "")
        project = str(data.get("workspace") or data.get("project") or "")
    if not raw_text:
        return None
    return raw_text, ts_epoch, session_id, project


def sync_sources(conn: sqlite3.Connection, sources: dict[str, Path], rebuild: bool = False) -> dict:
    started = time.perf_counter()
    stats = {
        "clients": {},
        "bytes_read": 0,
        "new_entries": 0,
        "total_entries": 0,
        "elapsed_ms": 0.0,
    }
    now_iso = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with conn:
        for client, path in sources.items():
            if not path.is_file() or is_link(path):
                stats["clients"][client] = {"status": "missing", "bytes_read": 0, "new_entries": 0}
                continue

            st = path.stat()
            prev = None if rebuild else conn.execute(
                "SELECT path, size, mtime_ns, byte_offset, line_count FROM sources WHERE client = ?",
                (client,),
            ).fetchone()

            path_str = str(path.resolve())
            if prev and prev[0] == path_str and prev[1] == st.st_size and prev[2] == st.st_mtime_ns:
                stats["clients"][client] = {"status": "unchanged", "bytes_read": 0, "new_entries": 0}
                continue

            start_offset = 0
            line_no = 0
            reset_client = True
            if prev and prev[0] == path_str and st.st_size >= prev[3]:
                start_offset = prev[3]
                line_no = prev[4]
                reset_client = False

            if reset_client:
                conn.execute("DELETE FROM entries_fts WHERE client = ?", (client,))
                conn.execute("DELETE FROM entries WHERE client = ?", (client,))

            bytes_read = 0
            new_entries = 0
            new_offset = start_offset

            with path.open("rb") as handle:
                handle.seek(start_offset)
                while True:
                    raw_line = handle.readline()
                    if not raw_line:
                        break
                    # Avoid indexing a partially written trailing line without newline unless at EOF with valid JSON.
                    if not raw_line.endswith(b"\n"):
                        try:
                            json.loads(raw_line.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            break
                    new_offset = handle.tell()
                    bytes_read += len(raw_line)
                    line_no += 1

                    stripped = raw_line.decode("utf-8", errors="replace").strip()
                    if not stripped:
                        continue
                    try:
                        payload = json.loads(stripped)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(payload, dict):
                        continue

                    parsed = parse_client_record(client, payload)
                    if not parsed:
                        continue
                    raw_text, ts_epoch, session_id, project = parsed
                    redacted = redact_text(raw_text)
                    if not redacted:
                        continue

                    domain = classify_domain(redacted)
                    signals = classify_signals(redacted)
                    noise = is_noise_entry(redacted, len(raw_text))
                    stored_text = redacted if len(redacted) <= 600 else redacted[:599] + "…"

                    cursor = conn.execute(
                        """
                        INSERT OR REPLACE INTO entries (
                            client, line_no, session_id, ts_epoch, ts_iso, project_hash,
                            char_len, domain, signals, is_noise, text_redacted
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            client,
                            line_no,
                            session_id[:64],
                            ts_epoch,
                            format_iso(ts_epoch),
                            hash_project(project),
                            len(raw_text),
                            domain,
                            ",".join(signals),
                            noise,
                            stored_text,
                        ),
                    )
                    entry_id = cursor.lastrowid
                    fts_terms = tokenize_terms(stored_text)
                    if fts_terms:
                        conn.execute(
                            "INSERT INTO entries_fts(entry_id, client, domain, terms) VALUES (?, ?, ?, ?)",
                            (entry_id, client, domain, fts_terms),
                        )
                    new_entries += 1

            conn.execute(
                """
                INSERT OR REPLACE INTO sources(client, path, size, mtime_ns, byte_offset, line_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (client, path_str, st.st_size, st.st_mtime_ns, new_offset, line_no, now_iso),
            )
            stats["bytes_read"] += bytes_read
            stats["new_entries"] += new_entries
            stats["clients"][client] = {
                "status": "rebuilt" if reset_client else "incremental",
                "bytes_read": bytes_read,
                "new_entries": new_entries,
            }

    stats["total_entries"] = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    stats["elapsed_ms"] = round((time.perf_counter() - started) * 1000.0, 2)
    return stats


def resolve_time_cutoff(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    if getattr(args, "since_last", False):
        row = conn.execute(
            "SELECT ts_epoch FROM checkpoints WHERE name = ?",
            (getattr(args, "checkpoint", "default"),),
        ).fetchone()
        return int(row[0]) + 1 if row else 0
    if getattr(args, "since", None):
        return parse_since_arg(args.since)
    days = getattr(args, "days", None)
    if days is not None:
        max_ts = conn.execute("SELECT COALESCE(MAX(ts_epoch), 0) FROM entries").fetchone()[0]
        return max(0, max_ts - int(days) * 86400)
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.cache_dir)
    conn = open_db(db_path, rebuild=args.rebuild)
    try:
        stats = sync_sources(conn, resolve_sources(args), rebuild=args.rebuild)
    finally:
        conn.close()

    if args.as_json:
        print(json.dumps({"db": str(db_path), **stats}, ensure_ascii=False, indent=2))
    else:
        print(
            f"History index synced ({stats['elapsed_ms']} ms): "
            f"+{stats['new_entries']} entries ({stats['bytes_read']} bytes read), "
            f"{stats['total_entries']} total -> {db_path}"
        )
        for client, info in stats["clients"].items():
            print(f"  {client:6s}: {info['status']:11s} +{info['new_entries']} entries ({info['bytes_read']} B)")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.cache_dir)
    conn = open_db(db_path)
    try:
        sync_stats = sync_sources(conn, resolve_sources(args))
        cutoff = resolve_time_cutoff(conn, args)
        where = ["ts_epoch >= ?"]
        params: list[object] = [cutoff]
        if args.client:
            where.append("client = ?")
            params.append(args.client)
        clause = " AND ".join(where)

        by_client = dict(conn.execute(f"SELECT client, COUNT(*) FROM entries WHERE {clause} GROUP BY client", params).fetchall())
        by_domain = conn.execute(
            f"SELECT domain, COUNT(*) AS n FROM entries WHERE {clause} AND is_noise = 0 GROUP BY domain ORDER BY n DESC",
            params,
        ).fetchall()
        sig_counts: dict[str, int] = {}
        for (raw_sig,) in conn.execute(
            f"SELECT signals FROM entries WHERE {clause} AND is_noise = 0 AND signals != ''",
            params,
        ):
            for s in raw_sig.split(","):
                sig_counts[s] = sig_counts.get(s, 0) + 1
        sig_sorted = sorted(sig_counts.items(), key=lambda kv: -kv[1])
        signal_entries = conn.execute(
            f"SELECT COUNT(*) FROM entries WHERE {clause} AND is_noise = 0 AND signals != ''",
            params,
        ).fetchone()[0]
        last_cp = conn.execute("SELECT name, ts_iso, note FROM checkpoints ORDER BY ts_epoch DESC LIMIT 1").fetchone()
    finally:
        conn.close()

    payload = {
        "sync": {"bytes_read": sync_stats["bytes_read"], "new_entries": sync_stats["new_entries"], "elapsed_ms": sync_stats["elapsed_ms"]},
        "cutoff_iso": format_iso(cutoff) if cutoff else None,
        "by_client": by_client,
        "concise_feedback_entries": signal_entries,
        "by_domain_non_noise": [{"domain": d, "count": c} for d, c in by_domain],
        "by_signal": [{"signal": s, "count": c} for s, c in sig_sorted],
        "last_checkpoint": {"name": last_cp[0], "ts_iso": last_cp[1], "note": last_cp[2]} if last_cp else None,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"Sync: +{sync_stats['new_entries']} entries ({sync_stats['bytes_read']} B, {sync_stats['elapsed_ms']} ms) | "
            f"Window: >= {payload['cutoff_iso'] or 'all-time'} | Concise feedback: {signal_entries}"
        )
        print("Clients: " + ", ".join(f"{k}={v}" for k, v in sorted(by_client.items())))
        print("Domains (non-noise): " + ", ".join(f"{d}={c}" for d, c in by_domain[:10]))
        print("Signals: " + ", ".join(f"{s}={c}" for s, c in sig_sorted))
        if last_cp:
            print(f"Last checkpoint: {last_cp[0]} @ {last_cp[1]} ({last_cp[2]})")
    return 0


def cmd_feedback(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.cache_dir)
    conn = open_db(db_path)
    try:
        sync_sources(conn, resolve_sources(args))
        cutoff = resolve_time_cutoff(conn, args)
        where = ["ts_epoch >= ?"]
        params: list[object] = [cutoff]
        if not args.include_noise:
            where.append("is_noise = 0")
            where.append("signals != ''")
        if args.domain:
            where.append("domain = ?")
            params.append(args.domain)
        if args.client:
            where.append("client = ?")
            params.append(args.client)
        if args.signal:
            where.append("(',' || signals || ',') LIKE ?")
            params.append(f"%,{args.signal},%")
        clause = " AND ".join(where)
        rows = conn.execute(
            f"""
            SELECT client, ts_iso, domain, signals, text_redacted
            FROM entries
            WHERE {clause}
            ORDER BY ts_epoch DESC, id DESC
            LIMIT ?
            """,
            (*params, args.limit * 2),
        ).fetchall()
    finally:
        conn.close()

    deduped: list[dict] = []
    seen: set[str] = set()
    for client, ts_iso, domain, signals, text in rows:
        key = text[:80]
        if key in seen:
            continue
        seen.add(key)
        deduped.append({
            "client": client,
            "date": ts_iso,
            "domain": domain,
            "signals": signals.split(",") if signals else [],
            "text": text,
        })
        if len(deduped) >= args.limit:
            break

    if args.as_json:
        print(json.dumps(deduped, ensure_ascii=False, indent=2))
    else:
        for item in deduped:
            sigs = ",".join(item["signals"][:2])
            print(f"[{item['date']} {item['client']} {item['domain']} | {sigs}] {item['text']}")
        if not deduped:
            print("(no matching feedback entries)")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    query_tokens = tokenize_terms(args.query).split()
    if not query_tokens:
        raise SystemExit("Search query contains no searchable terms.")
    fts_expr = " AND ".join(f'"{tok}"' for tok in query_tokens)

    db_path = resolve_db_path(args.cache_dir)
    conn = open_db(db_path)
    try:
        sync_sources(conn, resolve_sources(args))
        cutoff = resolve_time_cutoff(conn, args)
        where = ["entries_fts MATCH ?", "e.ts_epoch >= ?"]
        params: list[object] = [fts_expr, cutoff]
        if not args.include_noise:
            where.append("e.is_noise = 0")
        if args.domain:
            where.append("e.domain = ?")
            params.append(args.domain)
        if args.client:
            where.append("e.client = ?")
            params.append(args.client)
        clause = " AND ".join(where)
        rows = conn.execute(
            f"""
            SELECT e.client, e.ts_iso, e.domain, e.signals, e.text_redacted, bm25(entries_fts) AS rank
            FROM entries_fts
            JOIN entries e ON e.id = entries_fts.entry_id
            WHERE {clause}
            ORDER BY rank ASC, e.ts_epoch DESC
            LIMIT ?
            """,
            (*params, args.limit),
        ).fetchall()
    finally:
        conn.close()

    items = [
        {
            "client": r[0],
            "date": r[1],
            "domain": r[2],
            "signals": r[3].split(",") if r[3] else [],
            "text": r[4],
        }
        for r in rows
    ]
    if args.as_json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        for item in items:
            sigs = ",".join(item["signals"][:2])
            print(f"[{item['date']} {item['client']} {item['domain']} | {sigs}] {item['text']}")
        if not items:
            print("(no matches)")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.cache_dir)
    conn = open_db(db_path)
    try:
        sync_sources(conn, resolve_sources(args))
        max_ts = conn.execute("SELECT COALESCE(MAX(ts_epoch), 0) FROM entries").fetchone()[0]
        ts_epoch = max_ts or int(time.time())
        ts_iso = format_iso(ts_epoch)
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints(name, ts_epoch, ts_iso, note) VALUES (?, ?, ?, ?)",
                (args.name, ts_epoch, ts_iso, args.note),
            )
    finally:
        conn.close()
    print(f"Checkpoint '{args.name}' recorded at {ts_iso} (epoch={ts_epoch}): {args.note}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="history_index.py",
        description="Incremental local SQLite FTS5 index for Claude Code, Codex, and Antigravity histories.",
    )
    parser.add_argument("--home", help="Override user home directory for source history discovery")
    parser.add_argument("--claude-history", help="Explicit path to Claude Code history.jsonl")
    parser.add_argument("--codex-history", help="Explicit path to Codex history.jsonl")
    parser.add_argument("--agy-history", help="Explicit path to Antigravity history.jsonl")
    parser.add_argument("--cache-dir", help="Directory for derived SQLite cache (default: ~/.epiagentkit/cache)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="Incrementally index newly appended history lines")
    p_sync.add_argument("--rebuild", action="store_true", help="Drop and rebuild cache from scratch")
    p_sync.add_argument("--json", dest="as_json", action="store_true")
    p_sync.set_defaults(func=cmd_sync)

    p_sum = sub.add_parser("summary", help="Show compact counts by client, domain, and friction signals")
    p_sum.add_argument("--days", type=int, help="Limit to last N days from latest entry")
    p_sum.add_argument("--since", help="Limit to entries on or after YYYY-MM-DD")
    p_sum.add_argument("--since-last", action="store_true", help="Limit to entries since last checkpoint")
    p_sum.add_argument("--checkpoint", default="default", help="Checkpoint name for --since-last")
    p_sum.add_argument("--client", choices=("cc", "codex", "agy"))
    p_sum.add_argument("--json", dest="as_json", action="store_true")
    p_sum.set_defaults(func=cmd_summary)

    p_fb = sub.add_parser("feedback", help="List concise, deduplicated user-authored feedback")
    p_fb.add_argument("--domain", help="Filter by domain")
    p_fb.add_argument("--signal", help="Filter by friction signal")
    p_fb.add_argument("--client", choices=("cc", "codex", "agy"))
    p_fb.add_argument("--days", type=int)
    p_fb.add_argument("--since")
    p_fb.add_argument("--since-last", action="store_true")
    p_fb.add_argument("--checkpoint", default="default")
    p_fb.add_argument("--limit", type=int, default=25)
    p_fb.add_argument("--include-noise", action="store_true")
    p_fb.add_argument("--json", dest="as_json", action="store_true")
    p_fb.set_defaults(func=cmd_feedback)

    p_search = sub.add_parser("search", help="Full-text search across indexed histories (CJK + English)")
    p_search.add_argument("query")
    p_search.add_argument("--domain")
    p_search.add_argument("--client", choices=("cc", "codex", "agy"))
    p_search.add_argument("--days", type=int)
    p_search.add_argument("--since")
    p_search.add_argument("--since-last", action="store_true")
    p_search.add_argument("--checkpoint", default="default")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--include-noise", action="store_true")
    p_search.add_argument("--json", dest="as_json", action="store_true")
    p_search.set_defaults(func=cmd_search)

    p_mark = sub.add_parser("mark", help="Record a local distillation checkpoint timestamp")
    p_mark.add_argument("--name", default="default")
    p_mark.add_argument("--note", default="distilled")
    p_mark.set_defaults(func=cmd_mark)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
