"""Task-specific strict identity and synthetic parity checks; no real source rows."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('pooled_consumer', ROOT/'scripts/research_grudeva_pooled_tail_delivery.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


class Identity(unittest.TestCase):
    def test_wrong_execution_identity_fails_before_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'h.json'
            path.write_text('{"execution_producer_commit":"a","execution_producer_tree":"b"}')
            with patch.object(c.parent, 'git', return_value='wrong'):
                with self.assertRaisesRegex(ValueError, 'EXACT_TASK_EXECUTION'):
                    c.load_adapter(tmp, tmp, path)


@unittest.skipUnless(os.environ.get('SCI_MD_MASS_DELIVERY_007_PRODUCER') and os.environ.get('SCI_MD_MASS_DELIVERY_006_PRODUCER'), 'explicit exact producers unavailable')
class Parity(unittest.TestCase):
    def test_wrong_runtime_model_source_and_producer_bindings(self):
        import copy
        import json
        new = Path(os.environ['SCI_MD_MASS_DELIVERY_007_PRODUCER'])
        old = Path(os.environ['SCI_MD_MASS_DELIVERY_006_PRODUCER'])
        pin = json.loads(c.HANDOFF.read_text())
        changes = [({'execution_producer_tree': '0'*40}, 'EXACT_TASK'),
                   ({'source_record_sha256': '0'*64}, 'SOURCE_RECORD'),
                   ({'parent_handoff_sha256': '0'*64}, 'PARENT_HANDOFF'),
                   ({'immutable_parent_producer_commit': '0'*40}, 'IMMUTABLE_PARENT'),
                   ({'adapter_schema': 'wrong'}, 'ADAPTER_SCHEMA')]
        wrong = copy.deepcopy(pin['adapter_files']); wrong[c.ADAPTER] = '0'*64
        changes.append(({'adapter_files': wrong}, 'ADAPTER_OR_PARSER'))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'handoff.json'
            for change, error in changes:
                path.write_text(json.dumps(pin | change))
                with self.assertRaisesRegex(ValueError, error):
                    c.load_adapter(new, old, path)

    def test_all_arms_synthetic_serialized_equivalence_and_firewall(self):
        new = Path(os.environ['SCI_MD_MASS_DELIVERY_007_PRODUCER'])
        old = Path(os.environ['SCI_MD_MASS_DELIVERY_006_PRODUCER'])
        module, _, handoff = c.load_adapter(new, old)
        pin = module.read(handoff)
        models = {a: module.md.Model.load(old/pin['models'][a]['path']) for a in module.md.ARMS}
        early = [{'shot': 1, 'arm': a, 'input': module.md.EarlyInput(a, (.007,.006,.15,.1)[:len(models[a].means)], 'SYNTHETIC').to_dict()} for a in module.md.ARMS]
        queries = [{'shot': 1, 'vial': 9, 'start_kg': .013, 'end_kg': .016, 'mass_kg': .003}]
        expected, _ = module.predict_records(models, early, queries)
        self.assertEqual(c.predict(new, old, early, queries), expected)
        queries[0]['later_tds'] = 17.
        with self.assertRaises(ValueError):
            c.predict(new, old, early, queries)


if __name__ == '__main__':
    unittest.main()
