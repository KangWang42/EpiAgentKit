from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REVISION_STATE = load_module(
    "revision_state",
    ROOT / "skills/academic-humanizer/scripts/validate_revision_state.py",
)
REVISE_DOCX = load_module(
    "revise_docx",
    ROOT / "skills/docx/scripts/revise_docx.py",
)
COMPARE_DOCX = load_module(
    "compare_docx",
    ROOT / "skills/docx/scripts/compare_docx.py",
)
AUDIT_DOCX = load_module(
    "audit_docx",
    ROOT / "skills/docx/scripts/audit_docx.py",
)
ARCHIVE = load_module(
    "archive_deliverables",
    ROOT / "skills/project-init/scripts/archive_deliverables.py",
)
FINAL_CHECK = load_module(
    "final_project_check",
    ROOT / "hooks/final_project_check.py",
)


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""


def paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"


def make_docx(
    path: Path,
    paragraphs: list[str] | None = None,
    *,
    body_extra: str = "",
    core_creator: str = "",
    document_relationships: list[tuple[str, str, str]] | None = None,
    extra_parts: dict[str, bytes | str] | None = None,
) -> None:
    body = "".join(paragraph(value) for value in (paragraphs or [])) + body_extra
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <w:body>{body}<w:sectPr/></w:body>
</w:document>
"""
    root_relationships = [
        (
            "rIdDocument",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "word/document.xml",
        )
    ]
    parts: dict[str, bytes | str] = {
        "[Content_Types].xml": CONTENT_TYPES,
        "word/document.xml": document,
    }
    if core_creator:
        root_relationships.append(
            (
                "rIdCore",
                "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
                "docProps/core.xml",
            )
        )
        parts["docProps/core.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>{escape(core_creator)}</dc:creator><cp:lastModifiedBy>{escape(core_creator)}</cp:lastModifiedBy></cp:coreProperties>
"""
    root_xml = "".join(
        f'<Relationship Id="{rel_id}" Type="{rel_type}" Target="{target}"/>'
        for rel_id, rel_type, target in root_relationships
    )
    parts["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + root_xml
        + "</Relationships>"
    )
    document_xml = "".join(
        f'<Relationship Id="{rel_id}" Type="{rel_type}" Target="{target}"/>'
        for rel_id, rel_type, target in (document_relationships or [])
    )
    parts["word/_rels/document.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + document_xml
        + "</Relationships>"
    )
    parts.update(extra_parts or {})
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload.encode("utf-8") if isinstance(payload, str) else payload)


def valid_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "round": "round-1",
        "format_contract": "journal-template",
        "input_candidates": ["07_paper/manuscript.docx"],
        "selected_input": "07_paper/manuscript.docx",
        "allowed_scope": ["paragraph:0"],
        "forbidden_scope": ["references"],
        "pending_materials": [],
        "deliverables": {
            "clean": "07_paper/manuscript.docx",
            "marked": "07_paper/manuscript_marked.docx",
            "response": "07_paper/submission/response_to_reviewers.md",
        },
        "locked_decisions": {},
        "review_comments": [],
    }


def layout_entry(path: str, kind: str) -> dict[str, str]:
    return {
        "path": path,
        "kind": kind,
        "owner": "project-init",
        "purpose": "test contract",
        "producer": "test",
        "consumer": "audit",
        "lifecycle": "active",
    }


class RevisionWorkflowTests(unittest.TestCase):
    def test_clean_and_marked_docx_are_derived_from_one_exact_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "input.docx"
            clean = base / "manuscript.docx"
            marked = base / "manuscript_marked.docx"
            record = base / "revision.json"
            make_docx(source, ["Alpha old text.", "Protected paragraph."])
            record.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "locked_decisions": {},
                        "changes": [
                            {
                                "id": "change-1",
                                "locator": {"kind": "paragraph", "index": 0},
                                "old": "old",
                                "new": "revised",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills/docx/scripts/revise_docx.py"),
                    str(source),
                    str(record),
                    "--clean-out",
                    str(clean),
                    "--marked-out",
                    str(marked),
                    "--date",
                    "2026-01-02T03:04:00Z",
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["changes"], ["change-1"])
            scope = COMPARE_DOCX.compare_scope(
                COMPARE_DOCX.read_zip(source),
                COMPARE_DOCX.read_zip(clean),
                {"paragraph:0"},
            )
            equivalent = COMPARE_DOCX.compare_equivalence(
                COMPARE_DOCX.read_zip(clean),
                COMPARE_DOCX.read_zip(marked),
            )
            self.assertEqual(scope, [])
            self.assertEqual(equivalent, [])

    def test_scope_comparison_rejects_outside_and_package_part_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            original = base / "original.docx"
            changed = base / "changed.docx"
            make_docx(original, ["Allowed paragraph.", "Protected paragraph."])
            make_docx(
                changed,
                ["Allowed paragraph revised.", "Protected paragraph changed."],
                document_relationships=[
                    (
                        "rIdHeader",
                        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
                        "header1.xml",
                    )
                ],
                extra_parts={
                    "word/header1.xml": (
                        '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                        + paragraph("Unexpected header")
                        + "</w:hdr>"
                    )
                },
            )
            findings = COMPARE_DOCX.compare_scope(
                COMPARE_DOCX.read_zip(original),
                COMPARE_DOCX.read_zip(changed),
                {"paragraph:0"},
            )
            rules = {item["rule"] for item in findings}
            self.assertIn("scope.paragraph_changed", rules)
            self.assertIn("scope.package_part_changed", rules)

    def test_revision_records_reject_silent_locked_decision_changes(self) -> None:
        previous = {
            "locked_decisions": {
                "endpoint": {"value": "all-cause mortality", "source": "author round 1"}
            }
        }
        current = {
            "locked_decisions": {
                "endpoint": {"value": "disease mortality", "source": "draft text"}
            }
        }
        with self.assertRaisesRegex(REVISE_DOCX.RevisionError, "locked decision changed"):
            REVISE_DOCX.validate_previous_locks(current, previous)

    def test_revision_state_blocks_ambiguous_input_and_unclosed_review(self) -> None:
        ambiguous = valid_state()
        ambiguous["input_candidates"] = ["manuscript-a.docx", "manuscript-b.docx"]
        ambiguous["selected_input"] = ""
        findings = REVISION_STATE.validate_state(ambiguous)
        self.assertIn("input.ambiguous", {item["rule"] for item in findings})

        open_review = valid_state()
        open_review["review_comments"] = [
            {"id": "R1-C1", "status": "modified_pending_validation"}
        ]
        findings = REVISION_STATE.validate_state(open_review, signoff=True)
        self.assertIn("review.unclosed", {item["rule"] for item in findings})

    def test_docx_audit_checks_bookmarks_anonymity_and_raster_dpi(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            valid = base / "valid.docx"
            invalid = base / "invalid.docx"
            anonymous = base / "anonymous-risk.docx"
            image = base / "image.docx"
            make_docx(
                valid,
                body_extra=(
                    '<w:p><w:bookmarkStart w:id="1" w:name="Target"/>'
                    '<w:r><w:t>Target text</w:t></w:r><w:bookmarkEnd w:id="1"/></w:p>'
                    '<w:p><w:fldSimple w:instr=" REF Target "><w:r><w:t>1</w:t></w:r></w:fldSimple></w:p>'
                ),
            )
            make_docx(
                invalid,
                body_extra='<w:p><w:fldSimple w:instr=" REF Missing "><w:r><w:t>0</w:t></w:r></w:fldSimple></w:p>',
            )
            make_docx(
                anonymous,
                body_extra=(
                    '<w:p><w:ins w:id="1" w:author="Named Author" w:date="2026-01-02T03:04:00Z">'
                    '<w:r><w:t>changed</w:t></w:r></w:ins></w:p>'
                ),
                core_creator="Named Author",
            )
            png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(
                ">II", 600, 600
            )
            make_docx(
                image,
                body_extra=(
                    '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="1828800" cy="1828800"/>'
                    '<a:graphic><a:graphicData><a:blip r:embed="rIdImage"/></a:graphicData></a:graphic>'
                    "</wp:inline></w:drawing></w:r></w:p>"
                ),
                document_relationships=[
                    (
                        "rIdImage",
                        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                        "media/image1.png",
                    )
                ],
                extra_parts={"word/media/image1.png": png},
            )

            self.assertFalse(
                any(item["level"] == "ERROR" for item in AUDIT_DOCX.audit(valid))
            )
            self.assertIn(
                "references.bookmark_missing",
                {item["rule"] for item in AUDIT_DOCX.audit(invalid)},
            )
            anonymous_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(anonymous, anonymous=True)
                if item["level"] == "ERROR"
            }
            self.assertIn("anonymity.tracked_changes", anonymous_rules)
            self.assertIn("anonymity.core_property", anonymous_rules)
            dpi = [
                item
                for item in AUDIT_DOCX.audit(image)
                if item["rule"] == "images.effective_dpi"
            ]
            self.assertEqual(len(dpi), 1)
            self.assertIn("300dpi", dpi[0]["evidence"])

    def test_archive_plan_execute_manifest_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "中文 项目"
            backup = project / "09_backup"
            reports = project / "05_reports"
            backup.mkdir(parents=True)
            reports.mkdir()
            target = reports / "旧 稿.docx"
            current = reports / "当前稿.docx"
            payload = b"recoverable content"
            target.write_bytes(payload)
            current.write_bytes(b"current")
            command = [
                sys.executable,
                str(ROOT / "skills/project-init/scripts/archive_deliverables.py"),
                str(project),
                "--target",
                "05_reports/旧 稿.docx",
                "--current",
                "05_reports/当前稿.docx",
                "--topic",
                "论文",
                "--stage",
                "修订",
                "--reason",
                "被当前稿替代",
                "--timestamp",
                "2026-01-02_0304",
                "--json",
            ]
            environment = dict(os.environ)
            environment["PYTHONIOENCODING"] = "utf-8"
            plan = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            self.assertTrue(target.exists())
            batch_rel = json.loads(plan.stdout)["batch"]

            executed = subprocess.run(
                [*command[:-1], "--execute", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            archived = project / batch_rel / "05_reports/旧 稿.docx"
            self.assertFalse(target.exists())
            self.assertEqual(archived.read_bytes(), payload)
            manifest = (project / batch_rel / "MANIFEST.md").read_text(encoding="utf-8")
            self.assertIn(hashlib.sha256(payload).hexdigest(), manifest)
            self.assertIn("05_reports/旧 稿.docx", manifest)
            self.assertIn(batch_rel, (backup / "INDEX.md").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            backup = project / "09_backup"
            target = project / "05_reports/report.docx"
            backup.mkdir(parents=True)
            target.parent.mkdir()
            target.write_bytes(b"rollback")
            (backup / "INDEX.md").write_text("invalid index\n", encoding="utf-8")
            batch = backup / "2026-01-02_0304_topic_stage"
            with self.assertRaises(ARCHIVE.ArchiveError):
                ARCHIVE.execute_archive(
                    project,
                    backup,
                    batch,
                    [target],
                    [],
                    "test rollback",
                    "2026-01-02_0304",
                    "topic",
                    "stage",
                )
            self.assertTrue(target.is_file())
            self.assertFalse(batch.exists())

    def test_project_check_classifies_logs_and_rejects_undeclared_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            reports = project / "05_reports"
            reports.mkdir()
            (reports / "run.log").write_text(
                "warning: inspect convergence\nnan detected\nerror: model failed\n",
                encoding="utf-8",
            )
            findings: list[dict[str, str]] = []
            FINAL_CHECK.log_check(project, [], FINAL_CHECK.DEFAULT_CONTRACT, findings)
            levels = {
                item["key"].split("@", 1)[0]: item["level"]
                for item in findings
                if item["check"] == "logs.abnormal_term"
            }
            self.assertEqual(levels["warning"], "WARN")
            self.assertEqual(levels["nan"], "WARN")
            self.assertEqual(levels["error"], "ERROR")
            self.assertEqual(levels["failed"], "ERROR")

            manifest = {
                "schema_version": 1,
                "policy": "declare-before-create",
                "entries": [
                    layout_entry(".epiagentkit-layout.json", "file"),
                    layout_entry("05_reports", "dir"),
                ],
            }
            (project / ".epiagentkit-layout.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            findings = []
            FINAL_CHECK.layout_check(
                project, [], FINAL_CHECK.DEFAULT_CONTRACT, findings
            )
            self.assertIn(
                "layout.path_undeclared", {item["check"] for item in findings}
            )

            manifest["entries"].append(layout_entry("../outside", "file"))
            (project / ".epiagentkit-layout.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            findings = []
            FINAL_CHECK.layout_check(
                project, [], FINAL_CHECK.DEFAULT_CONTRACT, findings
            )
            self.assertIn("layout.path_escape", {item["check"] for item in findings})


if __name__ == "__main__":
    unittest.main()
