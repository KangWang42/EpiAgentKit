#!/usr/bin/env python3
"""Search derived skill metadata; Markdown remains the authoritative source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit


SCHEMA = 1
APPLICATION_ID = 0x4550494B
DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def terms(text: str) -> list[str]:
    """Tokenize English words and overlapping Chinese bigrams without packages."""
    result = []
    for token in re.findall(r"[\u3400-\u9fff]+|[a-z0-9_]+", text.lower()):
        if "\u3400" <= token[0] <= "\u9fff":
            result.extend(token[i:i + 2] for i in range(max(1, len(token) - 1)))
        else:
            result.append(token)
    return list(dict.fromkeys(result))


def compact(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def metadata(text: str, relative: str) -> dict:
    lines = text.lstrip("\ufeff").splitlines()
    description = ""
    if lines and lines[0] == "---" and "---" in lines[1:]:
        end = lines.index("---", 1)
        header = lines[1:end]
        for index, line in enumerate(header):
            if line.startswith("description:"):
                value = line.partition(":")[2].strip()
                continuation = []
                for following in header[index + 1:]:
                    if following and not following[0].isspace():
                        break
                    continuation.append(following.strip())
                if value in {">", "|", ">-", "|-", ""}:
                    value = " ".join(continuation)
                elif continuation and not value.startswith(('"', "'")):
                    value += " " + " ".join(continuation)
                if value.startswith('"') and value.endswith('"'):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1].replace("''", "'")
                description = value
                break
        lines = lines[end + 1:]
    headings = []
    paragraph = []
    opening = ""
    fence = None
    for number, line in enumerate(lines):
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            headings.append(compact(heading[1], 160))
        elif stripped and not opening:
            paragraph.append(stripped)
        if (not stripped or heading or number == len(lines) - 1) and paragraph and not opening:
            opening = " ".join(paragraph)
    return {
        "title": headings[0] if headings else Path(relative).stem,
        "summary": compact(description or opening, 300),
        "summary_source": "description" if description else "opening_paragraph",
        "headings": headings,
    }


def is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def discover(root: Path) -> dict[str, Path]:
    """Only immediate skills and their references; never crawl arbitrary roots."""
    files = {}
    for skill in sorted(root.iterdir()):
        if skill.name.startswith(".") or is_link(skill) or not skill.is_dir():
            continue
        entry = skill / "SKILL.md"
        if not entry.is_file() or is_link(entry):
            continue
        files[entry.relative_to(root).as_posix()] = entry
        references = skill / "references"
        if not references.is_dir() or is_link(references):
            continue
        for directory, dirs, names in os.walk(references, followlinks=False):
            dirs[:] = sorted(name for name in dirs if not name.startswith(".")
                             and not is_link(Path(directory) / name))
            for name in sorted(names):
                path = Path(directory) / name
                if name.startswith(".") or path.suffix.lower() != ".md" or is_link(path):
                    continue
                files[path.relative_to(root).as_posix()] = path
    return files


def initialize(connection: sqlite3.Connection, root: Path) -> None:
    connection.executescript(f"""
        PRAGMA application_id = {APPLICATION_ID};
        PRAGMA user_version = {SCHEMA};
        CREATE TABLE metadata (root TEXT NOT NULL);
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL,
            skill TEXT NOT NULL, kind TEXT NOT NULL,
            mtime INTEGER NOT NULL, ctime INTEGER NOT NULL, size INTEGER NOT NULL,
            sha256 TEXT NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL,
            summary_source TEXT NOT NULL, headings TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE search USING fts5(path, title, summary, headings);
    """)
    connection.execute("INSERT INTO metadata VALUES (?)", (str(root),))
    connection.commit()


def refresh(connection: sqlite3.Connection, files: dict[str, Path], verify: bool = False) -> dict:
    previous = {row["path"]: row for row in connection.execute("SELECT * FROM documents")}
    updated = 0
    removed = sorted(previous.keys() - files.keys())
    with connection:
        for relative in removed:
            connection.execute("DELETE FROM search WHERE rowid = ?", (previous[relative]["id"],))
            connection.execute("DELETE FROM documents WHERE path = ?", (relative,))
        for relative, path in files.items():
            stat = path.stat()
            stamp = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
            old = previous.get(relative)
            if old and not verify and stamp == (old["mtime"], old["ctime"], old["size"]):
                continue
            data = path.read_bytes()
            after = path.stat()
            if stamp != (after.st_mtime_ns, after.st_ctime_ns, after.st_size):
                raise ValueError(f"文件在索引期间变化，请重试：{relative}")
            checksum = hashlib.sha256(data).hexdigest()
            if old and checksum == old["sha256"]:
                connection.execute("UPDATE documents SET mtime=?, ctime=?, size=? WHERE path=?",
                                   (*stamp, relative))
                continue
            info = metadata(data.decode("utf-8-sig"), relative)
            if old:
                connection.execute("DELETE FROM search WHERE rowid = ?", (old["id"],))
                connection.execute("DELETE FROM documents WHERE path = ?", (relative,))
            cursor = connection.execute(
                "INSERT INTO documents(path,skill,kind,mtime,ctime,size,sha256,title,summary,summary_source,headings) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (relative, relative.split("/")[0], "skill" if path.name == "SKILL.md" else "reference",
                 *stamp, checksum, info["title"], info["summary"], info["summary_source"],
                 json.dumps(info["headings"], ensure_ascii=False)),
            )
            connection.execute("INSERT INTO search(rowid,path,title,summary,headings) VALUES (?,?,?,?,?)",
                               (cursor.lastrowid, " ".join(terms(relative)), " ".join(terms(info["title"])),
                                " ".join(terms(info["summary"])), " ".join(terms(" ".join(info["headings"])))))
            updated += 1
    return {"documents": len(files), "updated": updated, "removed": len(removed)}


class Catalog:
    def __init__(self, root: Path, cache_dir: Path | None = None):
        self.root = root.expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("--root 必须是包含各技能目录的 skills 目录")
        key = hashlib.sha256(str(self.root).encode("utf-8")).hexdigest()[:16]
        self.cache_dir = (cache_dir or self.root.parent / ".epiagentkit-cache").expanduser().resolve()
        if self.cache_dir == self.root or self.root in self.cache_dir.parents:
            raise ValueError("缓存目录必须位于 skills 目录之外，避免随技能分发")
        self.path = self.cache_dir / f"skills-{key}.sqlite3"

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def prepare(self, rebuild: bool = False, verify: bool = False) -> tuple[sqlite3.Connection, dict]:
        files = discover(self.root)
        if not files:
            raise ValueError("指定目录没有可索引的 SKILL.md；请核对 --root")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if rebuild or not self.path.exists():
            descriptor, temporary = tempfile.mkstemp(prefix=".skills-", suffix=".sqlite3", dir=self.cache_dir)
            os.close(descriptor)
            temporary_path = Path(temporary)
            try:
                connection = sqlite3.connect(temporary_path)
                connection.row_factory = sqlite3.Row
                try:
                    initialize(connection, self.root)
                    stats = refresh(connection, files)
                finally:
                    connection.close()
                os.replace(temporary_path, self.path)
            finally:
                temporary_path.unlink(missing_ok=True)
            return self.connect(), stats
        connection = self.connect()
        try:
            application = connection.execute("PRAGMA application_id").fetchone()[0]
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if application != APPLICATION_ID or version != SCHEMA:
                raise ValueError("索引格式不兼容；用 build --rebuild 重建派生缓存")
            if connection.execute("SELECT root FROM metadata").fetchone()[0] != str(self.root):
                raise ValueError("索引来源目录不匹配；用 build --rebuild 重建派生缓存")
            stats = refresh(connection, files, verify)
            return connection, stats
        except Exception:
            connection.close()
            raise

    def search(self, connection: sqlite3.Connection, query: str, skill: str | None,
               kind: str | None, limit: int) -> list[dict]:
        query_terms = terms(query)
        if not query_terms:
            raise ValueError("请提供中文或英文检索词")
        if len(query_terms) > 64 or len(query) > 500:
            raise ValueError("检索词过长；请提炼任务、方法或文件术语")
        groups = re.findall(r"[\u3400-\u9fff]+|[a-z0-9_]+", query.lower())
        expression = " OR ".join("(" + " AND ".join('"' + item + '"' for item in terms(group)) + ")"
                                 for group in groups)
        rows = connection.execute(
            "SELECT d.*, bm25(search, 6, 5, 3, 1) AS score FROM search "
            "JOIN documents d ON d.id = search.rowid WHERE search MATCH ? "
            "AND (? IS NULL OR d.skill = ?) AND (? IS NULL OR d.kind = ?) "
            "ORDER BY score, d.path LIMIT ?",
            (expression, skill, skill, kind, kind, limit),
        )
        return [{"path": row["path"], "skill": row["skill"], "kind": row["kind"],
                 "title": row["title"], "summary": row["summary"],
                 "headings": [heading for heading in json.loads(row["headings"])
                              if set(terms(heading)) & set(query_terms)][:3]}
                for row in rows]

    def peek(self, connection: sqlite3.Connection, relative: str, lines: int) -> dict:
        row = connection.execute("SELECT * FROM documents WHERE path = ?", (relative,)).fetchone()
        allowed = discover(self.root)
        if row is None or relative not in allowed:
            raise ValueError("文件不在当前技能索引中；请先 search 并使用返回的相对路径")
        data = allowed[relative].read_bytes()
        checksum = hashlib.sha256(data).hexdigest()
        text = data.decode("utf-8-sig")
        if checksum != row["sha256"]:
            raise ValueError("文件已变化，索引与原文不一致；先 build --verify 再读取")
        linked = []
        for destination in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            url = urlsplit(destination.strip("<>"))
            if url.scheme or url.netloc or not url.path:
                continue
            target = (allowed[relative].parent / unquote(url.path)).resolve()
            if not target.is_relative_to(self.root):
                continue
            key = target.relative_to(self.root).as_posix()
            if key in allowed and key != relative and key not in linked:
                linked.append(key)
        head = "\n".join(text.splitlines()[:lines])
        return {"path": relative, "absolute_path": str(allowed[relative]), "sha256": checksum,
                "summary_source": row["summary_source"], "head": head[:8000],
                "truncated": len(head) > 8000 or len(text.splitlines()) > lines,
                "linked_documents": linked[:20], "links_truncated": len(linked) > 20}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="按技能查询 Markdown 元数据，再核对原文文件头；不保存会话记忆。")
    result.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="实际 skills 目录；默认使用脚本所属目录")
    result.add_argument("--cache-dir", type=Path, help="可重建缓存目录；必须位于 skills 之外")
    commands = result.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="增量更新索引")
    build.add_argument("--rebuild", action="store_true", help="原子重建专用派生数据库，处理损坏或格式升级")
    build.add_argument("--verify", action="store_true", help="读取全部索引源并核对哈希")
    search = commands.add_parser("search", help="自动增量更新后检索候选元数据")
    search.add_argument("query")
    search.add_argument("--skill", help="按已确认的任务技能缩小范围")
    search.add_argument("--kind", choices=("skill", "reference"))
    search.add_argument("--limit", type=int, default=6, choices=range(1, 21), metavar="1..20")
    peek = commands.add_parser("peek", help="核对源文件哈希并返回真实文件头及库内链接")
    peek.add_argument("path", help="search 返回的相对路径")
    peek.add_argument("--lines", type=int, default=40, choices=range(1, 201), metavar="1..200")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    connection = None
    try:
        catalog = Catalog(args.root, args.cache_dir)
        connection, stats = catalog.prepare(getattr(args, "rebuild", False), getattr(args, "verify", False))
        output = {"root": str(catalog.root), "refresh": stats}
        if args.command == "search":
            output["candidates"] = catalog.search(connection, args.query, args.skill, args.kind, args.limit)
            output["next"] = ("核对候选与当前任务，再 peek 或直接读取原文；技能必读要求仍然适用。"
                              if output["candidates"] else "元数据无匹配不代表没有要求；改用技能正文链接或 rg 搜索。")
        elif args.command == "peek":
            output["document"] = catalog.peek(connection, args.path, args.lines)
        else:
            output["database"] = str(catalog.path)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error),
                          "next": "核对目录和权限；缓存损坏时用 build --rebuild。工具不可用时按技能链接或 rg 查找，不安装运行时。"},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
