"""Offline synthetic loader adversaries and optional explicit-producer parity."""
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('anchored_consumer', ROOT/'scripts/research_anchored_mass_delivery.py')
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.producer = self.root/'producer'
        runtime = self.producer/'puckworks/analysis'
        runtime.mkdir(parents=True)
        (runtime/'mass_delivery.py').write_text('SENTINEL = "synthetic explicit producer"\n')
        (runtime/'conditioned_mass_delivery.py').write_text('from . import mass_delivery as kernel\n')
        (runtime/'anchored_mass_delivery.py').write_text(
            'from . import mass_delivery as kernel\nfrom . import conditioned_mass_delivery as conditioned\n'
            'import json, hashlib\nfrom types import SimpleNamespace\n'
            'VERSION="synthetic-state"\nUNITS={"beverage":"kg"}\nCLAIMS=("RESEARCH_ONLY",)\n'
            'strict_json=json.loads\nclass FrozenBase:\n @staticmethod\n def load(path):\n'
            '  raw=path.read_bytes();d=json.loads(raw)\n'
            '  return SimpleNamespace(artifact_json=raw.decode(),sha256=hashlib.sha256(raw).hexdigest(),model_id=d["model_id"])\n')
        self.pin = {'runtime_modules': list(consumer.RUNTIME), 'models': {}, 'producer_files': {},
            'state_schema': 'synthetic-state', 'state_units': {'beverage': 'kg'},
            'required_state_claims': ['RESEARCH_ONLY'], 'source_rights': 'synthetic',
            'base_domain_kg': [0., .06], 'feature_definitions': {'synthetic': True},
            'setting_hull': {'synthetic': True}, 'source_code_semantics': 'synthetic'}
        for family in consumer.FAMILIES:
            model = {'model_id': 'synthetic/'+family, 'family': family, 'version': 'synthetic-base',
                'units': {'beverage': 'kg'}, 'domain_kg': [0., .06], 'rights': 'synthetic',
                'claims': ['RESEARCH_ONLY', 'SOURCE_INTERNAL', 'TARGET_EXPOSED', 'PHYSICAL_VALIDATION_NOT_ESTABLISHED']}
            model.update({k: self.pin[k] for k in ('feature_definitions', 'setting_hull', 'source_code_semantics')})
            path = self.producer/(family+'.json')
            path.write_text(json.dumps(model))
            self.pin['models'][family] = dict(path=path.name, **{k: model[k] for k in ('model_id', 'family', 'version', 'units')})
        for relative in (*consumer.RUNTIME, *(f+'.json' for f in consumer.FAMILIES)):
            self.pin['producer_files'][relative] = consumer.sha(self.producer/relative)
        self.git('init', '-q'); self.git('add', '.')
        self.git('-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.invalid', 'commit', '-qm', 'synthetic fixture')
        self.pin['producer_commit'] = consumer.git(self.producer, 'HEAD')
        self.pin['producer_tree'] = consumer.git(self.producer, 'HEAD^{tree}')
        self.handoff = self.root/'handoff.json'
        self.save()

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.producer), *args], check=True, capture_output=True)

    def save(self):
        self.handoff.write_text(json.dumps(self.pin))

    def load(self):
        return consumer.load_producer(self.producer, 'MASS', self.handoff)

    def test_isolated_transitive_imports_ignore_installed_poison(self):
        names = ('puckworks.analysis.mass_delivery', 'puckworks.analysis.conditioned_mass_delivery',
                 'puckworks.analysis.anchored_mass_delivery')
        previous = {n: sys.modules.get(n) for n in names}
        for n in names:
            sys.modules[n] = types.ModuleType(n)
        try:
            module, base, _ = self.load()
            self.assertIs(module.kernel, module.conditioned.kernel)
            self.assertEqual(module.kernel.SENTINEL, 'synthetic explicit producer')
            self.assertEqual(base.model_id, 'synthetic/MASS')
        finally:
            for n, v in previous.items():
                if v is None:
                    sys.modules.pop(n, None)
                else:
                    sys.modules[n] = v

    def test_exact_revision_and_tree(self):
        for key in ('producer_commit', 'producer_tree'):
            original = self.pin[key]
            self.pin[key] = '0'*40; self.save()
            with self.assertRaisesRegex(ValueError, 'REVISION_OR_TREE'):
                self.load()
            self.pin[key] = original

    def test_every_transitive_module_and_model_is_bound(self):
        for rel in tuple(self.pin['producer_files']):
            p = self.producer/rel
            data = p.read_bytes(); p.write_bytes(data+b'\n')
            with self.assertRaisesRegex(ValueError, 'HASH_OR_PATH'):
                self.load()
            p.write_bytes(data)
        self.pin['producer_files'].pop(consumer.RUNTIME[0]); self.save()
        with self.assertRaisesRegex(ValueError, 'UNBOUND_RUNTIME'):
            self.load()

    def test_missing_dependency_and_path_escape_fail_closed(self):
        p = self.producer/consumer.RUNTIME[0]
        data = p.read_bytes(); p.unlink()
        with self.assertRaisesRegex(ValueError, 'HASH_OR_PATH'):
            self.load()
        p.write_bytes(data)
        self.pin['producer_files']['../handoff.json'] = consumer.sha(self.handoff); self.save()
        with self.assertRaisesRegex(ValueError, 'HASH_OR_PATH'):
            self.load()

    def test_schema_units_and_claim_contract(self):
        for key, value in [('state_schema', 'wrong'), ('state_units', {}),
                           ('required_state_claims', ['UNSUPPORTED_CLAIM'])]:
            original = self.pin[key]; self.pin[key] = value; self.save()
            with self.assertRaises(ValueError):
                self.load()
            self.pin[key] = original

    def test_support_and_nominal_semantics(self):
        self.pin['base_domain_kg'] = [0., .07]; self.save()
        with self.assertRaisesRegex(ValueError, 'SUPPORT'):
            self.load()
        self.pin['base_domain_kg'] = [0., .06]
        self.pin['source_code_semantics'] = 'MEASURED_FLOW'; self.save()
        with self.assertRaisesRegex(ValueError, 'SETTING_SEMANTICS'):
            consumer.load_producer(self.producer, 'SETTING_EMPIRICAL', self.handoff)

    def test_unlisted_family_rejected(self):
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_FROZEN_BASE'):
            consumer.load_producer(self.producer, 'MTF', self.handoff)


@unittest.skipUnless(os.environ.get('SCI_MD_MASS_DELIVERY_003_PRODUCER'), 'explicit producer checkout unavailable')
class ProducerParity(unittest.TestCase):
    def test_all_bases_with_shared_synthetic_anchor(self):
        path = Path(os.environ['SCI_MD_MASS_DELIVERY_003_PRODUCER'])
        for family in consumer.FAMILIES:
            module, base, _ = consumer.load_producer(path, family)
            setting = module.NominalSetting(362.15, 2.) if family == 'SETTING_EMPIRICAL' else None
            state = module.anchor(base, module.synthetic_observation(), setting=setting)
            expected = asdict(state.remaining_solute(.04))
            result = consumer.demonstrate(path, family)
            self.assertEqual(result['conditional_remaining'], expected)
            self.assertEqual(result['input_class'], 'SYNTHETIC_ANCHOR_INPUT')
            self.assertLessEqual(expected['numerical_allowance_kg'], 1e-9)


if __name__ == '__main__':
    unittest.main()
