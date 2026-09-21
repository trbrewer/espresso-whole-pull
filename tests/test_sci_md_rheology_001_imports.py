"""Regression coverage for package imports and the bounded post-result amendment."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.sci_md_rheology_001 import analysis


class RheologyImportTests(unittest.TestCase):
    def test_import_orders_keep_repository_analysis_package(self):
        for first in ('analysis.sci_data_fusion_001.audit',
                      'tools.sci_md_rheology_001.report',
                      'tools.sci_md_rheology_001.runner'):
            with self.subTest(first=first):
                code = f'''import {first}
import analysis.sci_data_fusion_001.audit
from tools.sci_md_rheology_001 import analysis as expected, report, runner
assert report.check_freeze is expected.check_freeze
assert runner.check_freeze is expected.check_freeze
assert report.compare is expected.compare
'''
                result = subprocess.run([sys.executable, '-B', '-c', code],
                                        cwd=analysis.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_maintained_launchers(self):
        for name in ('sci_md_rheology_001', 'run_sci_md_rheology_001',
                     'report_sci_md_rheology_001'):
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, '-B',
                                         str(analysis.ROOT/'scripts'/f'{name}.py'), '--help'],
                                        cwd=tempfile.gettempdir(), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_original_audit_and_amended_hashes(self):
        analysis.check_freeze(analysis.DOC/'AUDIT.json')

    def test_unlisted_scientific_change_rejected(self):
        original = analysis.sha
        with patch.object(analysis, 'sha', side_effect=lambda p:
                          'changed' if Path(p).name == 'SCENARIOS.json' else original(p)):
            with self.assertRaisesRegex(ValueError, 'frozen analysis changed'):
                analysis.check_freeze(analysis.DOC/'AUDIT.json')

    def test_changed_amended_file_rejected(self):
        original = analysis.sha
        with patch.object(analysis, 'sha', side_effect=lambda p:
                          'changed' if Path(p).name == 'report.py' else original(p)):
            with self.assertRaisesRegex(ValueError, 'frozen analysis changed'):
                analysis.check_freeze(analysis.DOC/'AUDIT.json')

    def test_amendment_cannot_replace_original_authority(self):
        original_doc = analysis.DOC
        for field, value, message in (
                ('original_freeze_sha256', 'wrong', 'another freeze'),
                ('files', {'tools/sci_md_rheology_001/report.py':
                           {'original_sha256': 'wrong', 'amended_sha256': 'wrong'}},
                 'original hash mismatch')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                doc = Path(directory)
                (doc/'FREEZE.json').write_bytes((original_doc/'FREEZE.json').read_bytes())
                amendment = json.loads((original_doc/'POST_RESULT_AMENDMENT.json').read_text())
                amendment[field] = value
                (doc/'POST_RESULT_AMENDMENT.json').write_text(json.dumps(amendment))
                with patch.object(analysis, 'DOC', doc):
                    with self.assertRaisesRegex(ValueError, message):
                        analysis.check_freeze('unused')
