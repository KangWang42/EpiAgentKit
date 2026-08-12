from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACT_VALIDATOR = load_module(
    "manuscript_contract_validator",
    ROOT
    / "skills"
    / "academic-publishing"
    / "scripts"
    / "validate_manuscript_contract.py",
)
TABLE_RECONCILER = load_module(
    "table_field_reconciler",
    ROOT
    / "skills"
    / "academic-publishing"
    / "scripts"
    / "reconcile_table_fields.py",
)
DOCX_AUDITOR = load_module(
    "docx_delivery_auditor",
    ROOT / "skills" / "docx" / "scripts" / "audit_docx.py",
)


def base_contract() -> dict:
    return {
        "schema_version": 1,
        "mode": "complete_manuscript",
        "status": "complete",
        "artifacts": [
            {
                "id": "manuscript",
                "audience": "journal readers",
                "purpose": "report the verified study",
                "output": "paper/manuscript.docx",
                "allowed_information": ["final scientific methods", "verified results"],
                "forbidden_information": ["debug history", "internal paths"],
            }
        ],
        "modules": [
            {
                "id": "cohort",
                "kind": "design",
                "source": ["PROTOCOL.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["time zero", "follow-up", "censoring"],
            },
            {
                "id": "survival",
                "kind": "method",
                "source": ["SAP.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["time scale", "events", "risk set", "HR and CI"],
            },
        ],
        "sections": [
            {
                "id": "methods",
                "function": "define the cohort and survival analysis",
                "evidence_sources": ["PROTOCOL.md", "SAP.md"],
                "modules": ["cohort", "survival"],
                "output": "Methods",
                "content_check": "passed",
            },
            {
                "id": "results",
                "function": "report follow-up and survival estimates",
                "evidence_sources": ["results/results.yaml"],
                "modules": ["cohort", "survival"],
                "output": "Results",
                "content_check": "passed",
            },
        ],
        "tables": [
            {
                "id": "association-table",
                "role": "report adjusted associations",
                "source": "results/results.yaml",
                "placement": "body",
                "caption": "Adjusted associations",
                "columns": [
                    {"field_id": "term", "label": "Term", "source_field": "term"},
                    {"field_id": "estimate", "label": "HR (95% CI)", "source_field": "estimate_display"},
                    {"field_id": "model_p", "label": "P value", "source_field": "p_display"},
                ],
            }
        ],
        "figures": [
            {
                "id": "survival-curve",
                "role": "show disease-free survival",
                "source": "04_figures/survival.png",
                "placement": "body",
                "caption": "Disease-free survival",
            }
        ],
        "checks": {
            "content": "passed",
            "field_reconciliation": "passed",
            "file_display": "passed",
        },
    }


class ManuscriptWorkflowContractTests(unittest.TestCase):
    def test_cohort_survival_contract_passes_without_cross_sectional_template(self) -> None:
        errors = CONTRACT_VALIDATOR.validate_contract(base_contract())

        self.assertEqual(errors, [])

    def test_cross_sectional_survey_mediation_requirements_compose(self) -> None:
        contract = base_contract()
        contract["modules"] = [
            {
                "id": "cross-sectional",
                "kind": "design",
                "source": ["PROTOCOL.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["same time window", "analysis denominator"],
            },
            {
                "id": "survey-weighting",
                "kind": "method",
                "source": ["SAP.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["weights", "strata", "clusters", "variance estimation"],
            },
            {
                "id": "mediation",
                "kind": "method",
                "source": ["SAP.md", "AGReMA"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["effect definition", "scale", "uncertainty", "interpretation boundary"],
            },
        ]
        for section in contract["sections"]:
            section["modules"] = [
                "cross-sectional",
                "survey-weighting",
                "mediation",
            ]

        errors = CONTRACT_VALIDATOR.validate_contract(contract)

        self.assertEqual(errors, [])

    def test_duplicate_visible_labels_pass_but_duplicate_field_ids_fail(self) -> None:
        contract = base_contract()
        columns = contract["tables"][0]["columns"]
        columns.extend(
            [
                {"field_id": "offline_p", "label": "P value", "source_field": "offline_p"},
                {"field_id": "online_p", "label": "P value", "source_field": "online_p"},
            ]
        )
        self.assertEqual(CONTRACT_VALIDATOR.validate_contract(contract), [])

        columns[-1]["field_id"] = "offline_p"
        errors = CONTRACT_VALIDATOR.validate_contract(contract)

        self.assertTrue(any("field_id 必须唯一" in error for error in errors))

    def test_complete_status_requires_all_three_checks(self) -> None:
        contract = base_contract()
        contract["checks"]["file_display"] = "blocked"

        errors = CONTRACT_VALIDATOR.validate_contract(contract)

        self.assertTrue(any("三项检查必须全部为 passed" in error for error in errors))

    def test_table_reconciliation_uses_position_for_repeated_visible_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            display = root / "display.csv"
            source.write_text(
                "term,offline_p,online_p,overall_p\nCognition,0.112,,0.021\n",
                encoding="utf-8",
            )
            display.write_text(
                "变量,P值,P值,P值\nCognition,0.112,,0.021\n",
                encoding="utf-8",
            )
            spec = {
                "schema_version": 1,
                "row_keys": [{"source_column": "term", "display_column": 0}],
                "fields": [
                    {"field_id": "offline_p", "source_column": "offline_p", "display_column": 1},
                    {"field_id": "online_p", "source_column": "online_p", "display_column": 2},
                    {"field_id": "overall_p", "source_column": "overall_p", "display_column": 3},
                ],
            }

            passed = TABLE_RECONCILER.reconcile(source, display, spec)
            self.assertEqual(passed["status"], "PASS")

            display.write_text(
                "变量,P值,P值,P值\nCognition,0.021,,0.021\n",
                encoding="utf-8",
            )
            failed = TABLE_RECONCILER.reconcile(source, display, spec)

            self.assertEqual(failed["status"], "FAIL")
            self.assertEqual(failed["mismatches"][0]["field_id"], "offline_p")
            self.assertEqual(failed["mismatches"][0]["source_value"], "0.112")
            self.assertEqual(failed["mismatches"][0]["display_value"], "0.021")

    def test_workflow_keeps_full_manuscript_contract_out_of_local_edits(self) -> None:
        publishing = (
            ROOT / "skills/academic-publishing/SKILL.md"
        ).read_text(encoding="utf-8")
        contract = (
            ROOT / "skills/academic-publishing/references/manuscript-contract.md"
        ).read_text(encoding="utf-8")
        report = (
            ROOT / "skills/report-writing/references/epidemiology-report-blueprint.md"
        ).read_text(encoding="utf-8")
        principles = (
            ROOT / "skills/biostat-principles/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("局部部件不因此建立整篇约定", publishing)
        self.assertIn("局部部件只锁定该部件及其直接关系", contract)
        self.assertIn("不规定固定章节数、表图数", contract)
        self.assertIn("含问卷变量不等于自动采用 CROSS", contract)
        self.assertIn("不把论文删短后改名为报告", report)
        self.assertIn("不为此给普通项目增加锁文件、PID 文件或新的状态机制", principles)

    def test_docx_inventory_rejects_duplicate_internal_field_ids(self) -> None:
        document_xml = f"""
        <w:document xmlns:w="{DOCX_AUDITOR.W_NS}">
          <w:body>
            <w:p><w:pPr><w:jc w:val="left"/></w:pPr><w:r><w:t>表1 关联结果</w:t></w:r></w:p>
            <w:tbl>
              <w:tr><w:tc><w:p><w:r><w:t>变量</w:t></w:r></w:p></w:tc>
              <w:tc><w:p><w:r><w:t>P 值</w:t></w:r></w:p></w:tc>
              <w:tc><w:p><w:r><w:t>P 值</w:t></w:r></w:p></w:tc></w:tr>
            </w:tbl>
          </w:body>
        </w:document>
        """.encode("utf-8")
        parts = {"word/document.xml": document_xml}
        document = etree.fromstring(document_xml)
        requirements = {
            "schema_version": 1,
            "tables": [
                {
                    "id": "table-1",
                    "role": "report associations",
                    "source": "display-source.csv",
                    "placement": "body",
                    "caption": "表1 关联结果",
                    "alignment": "left",
                    "references": [],
                    "columns": [
                        {"field_id": "term", "label": "变量", "source_field": "term", "column_index": 0},
                        {"field_id": "model_p", "label": "P 值", "source_field": "offline_p", "column_index": 1},
                        {"field_id": "model_p", "label": "P 值", "source_field": "overall_p", "column_index": 2},
                    ],
                    "reconciliation_evidence": "checks/table-1.json",
                }
            ],
            "figures": [],
        }

        findings = DOCX_AUDITOR.audit_delivery_requirements(
            parts, document, requirements
        )

        self.assertTrue(
            any(item["rule"] == "requirements.table_field_id" for item in findings)
        )


if __name__ == "__main__":
    unittest.main()
