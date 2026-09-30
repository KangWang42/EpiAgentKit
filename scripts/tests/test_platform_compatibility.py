from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import INSTALL_MANIFEST, INSTALL_SCHEMA, LOCAL_RULES_PRESERVE_FILE, PROJECT_NAME
from epiagentkit import check_platform


class PlatformCompatibilityTests(unittest.TestCase):
    def test_doctor_reports_preserved_rule_drift_without_writing_or_failing(self) -> None:
        for platform, filename in [('claude', 'CLAUDE.md'), ('codex', 'AGENTS.md')]:
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                root = base / 'source'
                client = base / platform
                root.mkdir()
                client.mkdir()
                (root / LOCAL_RULES_PRESERVE_FILE).touch()
                (root / 'CLAUDE.md').write_text('current rules\n', encoding='utf-8')
                target = client / filename
                target.write_text('personal rules\n', encoding='utf-8')
                (client / INSTALL_MANIFEST).write_text(json.dumps({
                    'schema': INSTALL_SCHEMA, 'project': PROJECT_NAME,
                    'platform': platform, 'components': [],
                }), encoding='utf-8')
                before = {p.relative_to(base): p.read_bytes() for p in base.rglob('*') if p.is_file()}
                checks = check_platform(platform, root, client, [])
                preserved = [check for check in checks if check['item'] == f'{platform}.rules.preserved']
                self.assertEqual(len(preserved), 1)
                self.assertEqual(preserved[0]['status'], 'WARN')
                self.assertFalse(any(check['status'] == 'FAIL' for check in checks))
                self.assertNotIn('personal rules', preserved[0]['detail'])
                self.assertEqual(before, {p.relative_to(base): p.read_bytes() for p in base.rglob('*') if p.is_file()})

    def test_doctor_accepts_preserved_rules_that_match_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'
            client = Path(directory) / 'claude'
            root.mkdir()
            client.mkdir()
            (root / LOCAL_RULES_PRESERVE_FILE).touch()
            for path in [root / 'CLAUDE.md', client / 'CLAUDE.md']:
                path.write_text('current rules\n', encoding='utf-8')
            (client / INSTALL_MANIFEST).write_text(json.dumps({
                'schema': INSTALL_SCHEMA, 'project': PROJECT_NAME,
                'platform': 'claude', 'components': [],
            }), encoding='utf-8')
            checks = check_platform('claude', root, client, [])
            preserved = next(check for check in checks if check['item'] == 'claude.rules.preserved')
            self.assertEqual(preserved['status'], 'PASS')


class StandardMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / 'skills/skill-creator/scripts/quick_validate.py'
        spec = importlib.util.spec_from_file_location('standard_metadata_validator', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.validator = staticmethod(module.validate_skill)

    def validate(self, description: str, compatibility: str = 'Claude Code and Codex') -> tuple[bool, str]:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / 'portable-skill'
            skill.mkdir()
            content = '\n'.join([
                '---', 'name: portable-skill',
                'description: ' + json.dumps(description),
                'compatibility: ' + json.dumps(compatibility),
                '---', '# Task', 'Perform the requested task.',
            ])
            (skill / 'SKILL.md').write_text(content, encoding='utf-8')
            return self.validator(skill)

    def test_standard_metadata_is_accepted_at_documented_limits(self) -> None:
        self.assertTrue(self.validate('a' * 1024, 'b' * 500)[0])

    def test_description_exceeding_standard_limit_is_rejected(self) -> None:
        self.assertFalse(self.validate('a' * 1025)[0])

    def test_invalid_compatibility_is_rejected(self) -> None:
        self.assertFalse(self.validate('Valid description', 'b' * 501)[0])
        self.assertFalse(self.validate('Valid description', ['unexpected list'])[0])


if __name__ == '__main__':
    unittest.main()
