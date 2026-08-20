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
from unittest import mock
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
REVISION_INVARIANTS = load_module(
    "revision_invariants",
    ROOT / "skills/academic-humanizer/scripts/check_revision_invariants.py",
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
REPORT_BUILDER = load_module(
    "report_builder",
    ROOT / "skills/report-writing/references/build_report.py",
)
ARCHIVE = load_module(
    "archive_deliverables",
    ROOT / "skills/project-init/scripts/archive_deliverables.py",
)
FINAL_CHECK = load_module(
    "final_project_check",
    ROOT / "hooks/final_project_check.py",
)
SOFFICE = load_module(
    "soffice_helper",
    ROOT / "skills/docx/scripts/office/soffice.py",
)


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""


def paragraph(text: str, para_id: str | None = None) -> str:
    identifier = f' w14:paraId="{para_id}"' if para_id else ""
    return f"<w:p{identifier}><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"


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
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
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
    def test_revision_invariant_fixtures_cover_preservation_and_drift(self) -> None:
        fixture = json.loads(
            (ROOT / "scripts/tests/fixtures/academic_guards.json").read_text(
                encoding="utf-8"
            )
        )
        for case in fixture["revision_cases"]:
            with self.subTest(case=case["id"]):
                result = REVISION_INVARIANTS.compare_texts(
                    case["original"],
                    case["revised"],
                    case["protected_terms"],
                )
                changed = {
                    name
                    for name, detail in result["categories"].items()
                    if detail["changed"]
                }
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(changed, set(case["expected_changed_categories"]))
                if case["id"] == "bilingual_tokens_preserved":
                    citations = REVISION_INVARIANTS.extract_citations(case["original"])
                    self.assertIn("doi:10.1000/test.01", citations)
                    self.assertNotIn("doi:10.1000/test.01。the", citations)

    def test_revision_invariant_cli_distinguishes_review_from_input_error(self) -> None:
        script = ROOT / "skills/academic-humanizer/scripts/check_revision_invariants.py"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            original = base / "original.md"
            revised = base / "revised.md"
            original.write_text("Result: 0.17 [1].", encoding="utf-8")
            revised.write_text("Result: 0.21 [1].", encoding="utf-8")
            review = subprocess.run(
                [sys.executable, str(script), str(original), str(revised), "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(review.returncode, 1, review.stdout + review.stderr)
            self.assertEqual(json.loads(review.stdout)["status"], "REVIEW_REQUIRED")

            original.write_bytes(b"\xff\xfe\x00\x00")
            invalid = subprocess.run(
                [sys.executable, str(script), str(original), str(revised), "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(invalid.returncode, 2, invalid.stdout + invalid.stderr)
            self.assertEqual(json.loads(invalid.stdout)["status"], "ERROR")

    def test_soffice_shim_is_never_probed_on_windows(self) -> None:
        with mock.patch.object(SOFFICE.sys, "platform", "win32"), mock.patch.object(
            SOFFICE.socket,
            "socket",
            side_effect=AssertionError("AF_UNIX must not be probed on Windows"),
        ):
            self.assertFalse(SOFFICE._needs_shim())
        copies = [
            ROOT / "skills/docx/scripts/office/soffice.py",
            ROOT / "skills/pptx/scripts/office/soffice.py",
        ]
        self.assertEqual(len({path.read_bytes() for path in copies}), 1)

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

    def test_scope_comparison_allows_only_explicit_paragraph_insertions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            original = base / "original.docx"
            inserted = base / "inserted.docx"
            changed = base / "changed.docx"
            make_docx(original, ["Anchor.", "Protected."])
            make_docx(inserted, ["Anchor.", "Reference A.", "Reference B.", "Protected."])
            make_docx(changed, ["Anchor.", "Reference A.", "Protected changed."])

            unauthorized = COMPARE_DOCX.compare_scope(
                COMPARE_DOCX.read_zip(original),
                COMPARE_DOCX.read_zip(inserted),
                set(),
            )
            self.assertIn("scope.paragraph_inserted", {item["rule"] for item in unauthorized})

            authorized = COMPARE_DOCX.compare_scope(
                COMPARE_DOCX.read_zip(original),
                COMPARE_DOCX.read_zip(inserted),
                set(),
                {"paragraph:0"},
            )
            self.assertEqual(authorized, [])

            protected = COMPARE_DOCX.compare_scope(
                COMPARE_DOCX.read_zip(original),
                COMPARE_DOCX.read_zip(changed),
                set(),
                {"paragraph:0"},
            )
            self.assertIn("scope.paragraph_changed", {item["rule"] for item in protected})

    def test_revision_locator_prefers_stable_paragraph_id(self) -> None:
        document = f'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"><w:body>
 {paragraph("First.", "00A1B2C3")}{paragraph("Second.", "00D4E5F6")}<w:sectPr/>
 </w:body></w:document>'''
        root = REVISE_DOCX.etree.fromstring(document.encode("utf-8"))
        selected = REVISE_DOCX.locate_paragraph(
            root,
            {"kind": "paragraph", "para_id": "00d4e5f6", "index": 1},
        )
        self.assertEqual(REVISE_DOCX.visible_text(selected), "Second.")
        with self.assertRaisesRegex(REVISE_DOCX.RevisionError, "different targets"):
            REVISE_DOCX.locate_paragraph(
                root,
                {"kind": "paragraph", "para_id": "00D4E5F6", "index": 0},
            )

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

    def test_revision_state_persists_interaction_contract_without_extra_files(self) -> None:
        previous = valid_state()
        previous["interaction_contract"] = {
            "answer_only": True,
            "create_document": False,
            "one_issue_at_a_time": True,
            "response_style": "direct",
            "highlight_policy": "specified_items_only",
        }
        current = valid_state()
        current["interaction_contract"] = dict(previous["interaction_contract"])
        current["interaction_contract"]["create_document"] = True
        findings = REVISION_STATE.validate_state(current, previous)
        self.assertIn("interaction.silent_change", {item["rule"] for item in findings})
        self.assertIn("interaction.conflict", {item["rule"] for item in findings})

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
                    '<wp:docPr id="1" name="Figure 1" descr="两组效应量比较"/>'
                    '<a:graphic><a:graphicData><a:blip r:embed="rIdImage"/></a:graphicData></a:graphic>'
                    "</wp:inline></w:drawing></w:r></w:p>"
                    '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
                    '<w:r><w:t>图1 两组效应量比较</w:t></w:r></w:p>'
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
            figure_requirements = {
                "schema_version": 1,
                "require_all_figures_listed": True,
                "figures": [
                    {
                        "id": "figure-1",
                        "role": "compare effect estimates",
                        "source": "verified-forest.png",
                        "placement": "body",
                        "caption": "图1 两组效应量比较",
                        "alignment": "center",
                        "references": ["见图1"],
                        "alt_text": "两组效应量比较",
                    }
                ],
                "required_text": ["见图1"],
            }
            figure_with_reference = base / "figure-with-reference.docx"
            make_docx(
                figure_with_reference,
                ["主要结果见图1。"],
                body_extra=(
                    '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="1828800" cy="1828800"/>'
                    '<wp:docPr id="1" name="Figure 1" descr="两组效应量比较"/>'
                    '<a:graphic><a:graphicData><a:blip r:embed="rIdImage"/></a:graphicData></a:graphic>'
                    "</wp:inline></w:drawing></w:r></w:p>"
                    '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
                    '<w:r><w:t>图1 两组效应量比较</w:t></w:r></w:p>'
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
            figure_errors = {
                item["rule"]
                for item in AUDIT_DOCX.audit(
                    figure_with_reference,
                    requirements=figure_requirements,
                )
                if item["level"] == "ERROR"
            }
            self.assertEqual(figure_errors, set())

            wrong_figure_requirements = json.loads(json.dumps(figure_requirements))
            wrong_figure_requirements["figures"][0]["alignment"] = "left"
            wrong_figure_requirements["figures"][0]["alt_text"] = "错误替代文字"
            wrong_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(
                    figure_with_reference,
                    requirements=wrong_figure_requirements,
                )
                if item["level"] == "ERROR"
            }
            self.assertIn("requirements.figure_caption_alignment", wrong_rules)
            self.assertIn("requirements.figure_alt_text", wrong_rules)

    def test_docx_audit_applies_task_specific_report_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            valid = base / "valid-report.docx"
            invalid = base / "invalid-report.docx"
            left_template = base / "left-template-report.docx"
            table_xml = (
                '<w:tbl><w:tblPr><w:tblBorders>'
                '<w:top w:val="single" w:color="000000"/>'
                '<w:bottom w:val="single" w:color="000000"/>'
                "</w:tblBorders></w:tblPr>"
                '<w:tr><w:tc><w:tcPr><w:shd w:val="clear" w:fill="FFFFFF"/></w:tcPr>'
                '<w:p><w:r><w:t>结果</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
            )
            valid_caption = (
                '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr>'
                '<w:color w:val="000000"/></w:rPr><w:t>表1 描述性统计</w:t></w:r></w:p>'
            )
            make_docx(
                valid,
                ["主要结果见表1。"],
                body_extra=valid_caption + table_xml,
            )
            invalid_table = table_xml.replace("FFFFFF", "D9EAF7").replace(
                'w:color="000000"', 'w:color="666666"'
            )
            invalid_caption = valid_caption.replace("center", "left").replace(
                "000000", "2E74B5"
            )
            make_docx(
                invalid,
                ["主要结果见表1。", "报告状态：最近一次成功生成。"],
                body_extra=(
                    invalid_caption
                    + "<w:p><w:r><w:t>题注与目标表之间的非空段落</w:t></w:r></w:p>"
                    + invalid_table
                ),
            )
            left_caption = valid_caption.replace("center", "left").replace(
                "表1 描述性统计", "表1 缺失概况"
            )
            make_docx(
                left_template,
                ["缺失情况见表1。"],
                body_extra=left_caption + table_xml,
            )

            requirements = {
                "schema_version": 1,
                "allowed_text_colors": ["000000"],
                "allowed_fill_colors": ["FFFFFF", "AUTO"],
                "allowed_border_colors": ["000000", "AUTO"],
                "require_all_tables_listed": True,
                "forbidden_text": ["报告状态："],
                "tables": [
                    {
                        "id": "table-1",
                        "role": "describe the study population",
                        "source": "verified-table.xlsx",
                        "placement": "body",
                        "caption": "表1 描述性统计",
                        "alignment": "center",
                        "references": ["见表1"],
                    }
                ],
            }
            valid_errors = {
                item["rule"]
                for item in AUDIT_DOCX.audit(valid, requirements=requirements)
                if item["level"] == "ERROR"
            }
            self.assertEqual(valid_errors, set())

            missing_kind = json.loads(json.dumps(requirements))
            missing_kind["schema_version"] = 2
            missing_kind["tables"][0].pop("table_kind", None)
            missing_kind_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(valid, requirements=missing_kind)
                if item["level"] == "ERROR"
            }
            self.assertIn("requirements.schema", missing_kind_rules)
            requirements_path = base / "docx-requirements.json"
            requirements_path.write_text(
                json.dumps(requirements, ensure_ascii=False), encoding="utf-8"
            )
            cli = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills/docx/scripts/audit_docx.py"),
                    str(valid),
                    "--requirements",
                    str(requirements_path),
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(cli.returncode, 0, cli.stdout + cli.stderr)
            self.assertTrue(json.loads(cli.stdout)["ok"])

            invalid_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(invalid, requirements=requirements)
                if item["level"] == "ERROR"
            }
            for rule in (
                "requirements.text_color",
                "requirements.fill_color",
                "requirements.border_color",
                "requirements.forbidden_text",
                "requirements.caption_alignment",
                "requirements.caption_target",
            ):
                self.assertIn(rule, invalid_rules)

            left_requirements = dict(requirements)
            left_requirements["tables"] = [
                {
                    "id": "table-1",
                    "role": "describe missingness",
                    "source": "verified-missingness.xlsx",
                    "placement": "body",
                    "caption": "表1 缺失概况",
                    "alignment": "left",
                    "references": ["见表1"],
                }
            ]
            left_errors = {
                item["rule"]
                for item in AUDIT_DOCX.audit(
                    left_template, requirements=left_requirements
                )
                if item["level"] == "ERROR"
            }
            self.assertEqual(left_errors, set())

    def test_docx_audit_rejects_pandoc_hyperlink_theme_color_for_black_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            document = base / "pandoc-hyperlink-theme.docx"
            hyperlink = (
                '<w:p><w:hyperlink w:anchor="doi">'
                '<w:r><w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>'
                '<w:t>doi:10.1000/test</w:t></w:r>'
                "</w:hyperlink></w:p>"
            )
            styles = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:style w:type="character" w:styleId="Hyperlink">'
                '<w:name w:val="Hyperlink"/><w:rPr><w:color w:themeColor="accent1"/></w:rPr>'
                "</w:style></w:styles>"
            )
            make_docx(document, ["正文"], body_extra=hyperlink, extra_parts={"word/styles.xml": styles})
            black_requirements = {"schema_version": 1, "allowed_text_colors": ["000000"]}
            black_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(document, requirements=black_requirements)
                if item["level"] == "ERROR"
            }
            self.assertIn("requirements.text_color", black_rules)

            template_requirements = {
                "schema_version": 1,
                "allowed_text_colors": ["000000", "THEME:ACCENT1"],
            }
            template_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(document, requirements=template_requirements)
                if item["level"] == "ERROR"
            }
            self.assertEqual(template_rules, set())

    def test_report_candidate_promotion_preserves_locked_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            candidate = base / "report-candidate.docx"
            target = base / "report.docx"
            target.write_bytes(b"stable-current-version")

            report = REPORT_BUILDER.Report()
            report.para("已核对的报告正文。")
            saved = report.save_candidate(candidate)
            self.assertEqual(saved[0], candidate)
            candidate_errors = {
                item["rule"]
                for item in AUDIT_DOCX.audit(
                    candidate,
                    requirements={
                        "schema_version": 1,
                        "allowed_text_colors": ["000000"],
                        "allowed_fill_colors": ["FFFFFF", "AUTO"],
                        "allowed_border_colors": ["000000", "AUTO"],
                    },
                )
                if item["level"] == "ERROR"
            }
            self.assertEqual(candidate_errors, set())
            promoted = REPORT_BUILDER.Report.promote_candidate(candidate, target)
            self.assertEqual(promoted, target)
            self.assertFalse(candidate.exists())
            self.assertTrue(target.is_file())
            self.assertNotEqual(target.read_bytes(), b"stable-current-version")

            locked_candidate = base / "report-candidate-locked.docx"
            report.save_candidate(locked_candidate)
            stable_bytes = target.read_bytes()
            with mock.patch.object(
                REPORT_BUILDER.os, "replace", side_effect=PermissionError("locked")
            ):
                with self.assertRaisesRegex(RuntimeError, "候选文件已保留"):
                    REPORT_BUILDER.Report.promote_candidate(locked_candidate, target)
            self.assertTrue(locked_candidate.is_file())
            self.assertEqual(target.read_bytes(), stable_bytes)

    def test_docx_audit_checks_academic_table_topology_and_row_hierarchy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            valid = base / "hierarchical-three-line.docx"
            report = REPORT_BUILDER.Report()
            report.table_caption("表1 分层统计")
            report.three_line_table(
                ["指标", "结果"],
                [
                    {
                        "row_key": "domain",
                        "row_role": "parent",
                        "display_label": "指标类别",
                        "indent_level": 0,
                        "values": [""],
                    },
                    {
                        "row_key": "domain.metric",
                        "row_role": "level",
                        "parent_key": "domain",
                        "display_label": "指标A",
                        "indent_level": 1,
                        "values": ["1.23"],
                    },
                    {
                        "row_key": "domain.metric.next",
                        "row_role": "continuation",
                        "parent_key": "domain.metric",
                        "display_label": "",
                        "indent_level": 1,
                        "values": ["2.34"],
                    },
                ],
            )
            report.save(valid)

            hierarchy = {
                "header_rows": 1,
                "label_column_index": 0,
                "indent_twips_per_level": 200,
                "rows": [
                    {
                        "row_key": "domain",
                        "row_role": "parent",
                        "display_label": "指标类别",
                        "indent_level": 0,
                    },
                    {
                        "row_key": "domain.metric",
                        "row_role": "level",
                        "parent_key": "domain",
                        "display_label": "指标A",
                        "indent_level": 1,
                    },
                    {
                        "row_key": "domain.metric.next",
                        "row_role": "continuation",
                        "parent_key": "domain.metric",
                        "display_label": "",
                        "indent_level": 1,
                    },
                ],
            }
            requirements = {
                "schema_version": 2,
                "require_all_tables_listed": True,
                "tables": [
                    {
                        "id": "table-1",
                        "role": "show hierarchical estimates",
                        "source": "verified-display-matrix.csv",
                        "placement": "body",
                        "table_kind": "academic_display",
                        "caption": "表1 分层统计",
                        "alignment": "center",
                        "references": [],
                        "row_hierarchy": hierarchy,
                    }
                ],
            }
            valid_errors = {
                item["rule"]
                for item in AUDIT_DOCX.audit(valid, requirements=requirements)
                if item["level"] == "ERROR"
            }
            self.assertEqual(valid_errors, set())

            def border_xml(top: str, bottom: str, side: str = "nil") -> str:
                return (
                    "<w:tcBorders>"
                    f'<w:top w:val="{top}" w:color="000000"/>'
                    f'<w:left w:val="{side}" w:color="000000"/>'
                    f'<w:bottom w:val="{bottom}" w:color="000000"/>'
                    f'<w:right w:val="{side}" w:color="000000"/>'
                    f'<w:insideH w:val="{side}" w:color="000000"/>'
                    f'<w:insideV w:val="{side}" w:color="000000"/>'
                    "</w:tcBorders>"
                )

            def cell_xml(text: str, borders: str, indent: int = 0) -> str:
                indent_xml = f'<w:pPr><w:ind w:left="{indent}"/></w:pPr>'
                return (
                    f"<w:tc><w:tcPr>{borders}</w:tcPr><w:p>{indent_xml}"
                    f"<w:r><w:t>{escape(text)}</w:t></w:r></w:p></w:tc>"
                )

            def table_xml(*, grid: bool, parent_label: str, child_indent: int) -> str:
                side = "single" if grid else "nil"
                middle = "single" if grid else "nil"
                header = "<w:tr>" + "".join(
                    cell_xml(text, border_xml("single", "single", side))
                    for text in ("指标", "结果")
                ) + "</w:tr>"
                parent = "<w:tr>" + cell_xml(
                    parent_label, border_xml(middle, middle, side)
                ) + cell_xml("", border_xml(middle, middle, side)) + "</w:tr>"
                child = "<w:tr>" + cell_xml(
                    "指标A", border_xml(middle, middle, side), child_indent
                ) + cell_xml("1.23", border_xml(middle, middle, side)) + "</w:tr>"
                continuation = "<w:tr>" + cell_xml(
                    "", border_xml(middle, "single", side), child_indent
                ) + cell_xml("2.34", border_xml(middle, "single", side)) + "</w:tr>"
                return f"<w:tbl>{header}{parent}{child}{continuation}</w:tbl>"

            caption = (
                '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
                '<w:r><w:t>表1 分层统计</w:t></w:r></w:p>'
            )
            grid = base / "grid.docx"
            make_docx(
                grid,
                body_extra=caption
                + table_xml(grid=True, parent_label="指标类别", child_indent=200),
            )
            grid_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(grid, requirements=requirements)
                if item["level"] == "ERROR"
            }
            self.assertIn("requirements.table_border_topology", grid_rules)

            flattened = base / "flattened.docx"
            make_docx(
                flattened,
                body_extra=caption
                + table_xml(
                    grid=False,
                    parent_label="指标类别：指标A",
                    child_indent=0,
                ),
            )
            flattened_rules = {
                item["rule"]
                for item in AUDIT_DOCX.audit(flattened, requirements=requirements)
                if item["level"] == "ERROR"
            }
            self.assertIn("requirements.table_row_label", flattened_rules)
            self.assertIn("requirements.table_row_indent", flattened_rules)

            form_requirements = json.loads(json.dumps(requirements))
            form_requirements["tables"][0]["table_kind"] = "official_form"
            form_requirements["tables"][0].pop("row_hierarchy")
            form_errors = {
                item["rule"]
                for item in AUDIT_DOCX.audit(grid, requirements=form_requirements)
                if item["level"] == "ERROR"
            }
            self.assertEqual(form_errors, set())

    def test_archive_plan_execute_manifest_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "中文 项目"
            backup = project / "09_backup"
            archive = backup / "archive"
            reports = project / "05_reports"
            archive.mkdir(parents=True)
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
            self.assertTrue(batch_rel.startswith("09_backup/archive/"))

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
            archive = backup / "archive"
            target = project / "05_reports/report.docx"
            archive.mkdir(parents=True)
            target.parent.mkdir()
            target.write_bytes(b"rollback")
            (backup / "INDEX.md").write_text("invalid index\n", encoding="utf-8")
            batch = archive / "2026-01-02_0304_topic_stage"
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

            manifest["entries"].append(
                layout_entry("09_backup/workbench/old_batch/missing.log", "file")
            )
            (project / ".epiagentkit-layout.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            findings = []
            FINAL_CHECK.layout_check(
                project, [], FINAL_CHECK.DEFAULT_CONTRACT, findings
            )
            self.assertNotIn(
                "09_backup/workbench/old_batch/missing.log",
                {item.get("path") for item in findings},
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

    def test_final_check_validates_declared_data_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "results/derived").mkdir(parents=True)
            layout = {
                "schema_version": 2,
                "policy": "directory-and-artifact-types",
                "profile": "analysis",
                "categories": [],
                "artifact_classes": [
                    {
                        "class": "data_readiness",
                        "pattern": "results/derived/data-readiness.json",
                        "producer": "formal data preparation script",
                        "consumers": ["run_pipeline"],
                    }
                ],
            }
            (project / ".epiagentkit-layout.json").write_text(
                json.dumps(layout), encoding="utf-8"
            )
            findings: list[dict[str, str]] = []
            FINAL_CHECK.data_readiness_check(project, findings)
            self.assertIn("readiness.state_missing", {item["check"] for item in findings})

            (project / "01_data").mkdir()
            (project / "02_code").mkdir()
            authoritative = project / "01_data/analysis.csv"
            producer = project / "02_code/01_data_cleaning.py"
            authoritative.write_text("id,value\n1,2\n", encoding="utf-8")
            producer.write_text("# producer\n", encoding="utf-8")
            state = {
                "schema_version": 1,
                "status": "analysis_ready",
                "authoritative_input": "01_data/analysis.csv",
                "input_format": "csv",
                "input_locator": "file",
                "unresolved_issues": 0,
                "producer": "02_code/01_data_cleaning.py",
                "decision_source": None,
                "run_id": "run-1",
                "hash_algorithm": "sha256",
                "input_hash": hashlib.sha256(authoritative.read_bytes()).hexdigest(),
                "generated_at": "2026-08-10T12:00:00+08:00",
            }
            (project / "results/derived/data-readiness.json").write_text(
                json.dumps(state), encoding="utf-8"
            )
            findings = []
            FINAL_CHECK.data_readiness_check(project, findings)
            self.assertEqual(findings, [])

            authoritative.write_text("id,value\n1,3\n", encoding="utf-8")
            findings = []
            FINAL_CHECK.data_readiness_check(project, findings)
            self.assertIn("readiness.hash_mismatch", {item["check"] for item in findings})


if __name__ == "__main__":
    unittest.main()
