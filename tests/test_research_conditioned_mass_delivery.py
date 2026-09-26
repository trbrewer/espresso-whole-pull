"""Synthetic pin/import adversaries plus optional explicit-checkout parity.

No permissioned measurements are read. Parity queries synthetic intervals only.
"""
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
spec = importlib.util.spec_from_file_location('conditioned_consumer', ROOT/'scripts/research_conditioned_mass_delivery.py')
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


class PinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.producer = self.root/'producer'
        self.producer.mkdir()
        runtime = self.producer/'puckworks/analysis'
        runtime.mkdir(parents=True)
        (runtime/'mass_delivery.py').write_text('SENTINEL = "explicit synthetic producer"\n')
        (runtime/'conditioned_mass_delivery.py').write_text(
            'from . import mass_delivery as kernel\nimport json\nfrom types import SimpleNamespace\n'
            'class Model:\n @staticmethod\n def load(path):\n  return SimpleNamespace(**json.loads(path.read_text()))\n')
        claims = ['RESEARCH_ONLY', 'SOURCE_INTERNAL', 'TARGET_EXPOSED',
                  'PHYSICAL_VALIDATION_NOT_ESTABLISHED', 'RETROSPECTIVE_MODEL_DEVELOPMENT_COMPARISON']
        self.pin = {'runtime_modules': list(consumer.RUNTIME), 'models': {}, 'producer_files': {},
                    'schema_version': 'synthetic', 'units': {'beverage': 'kg'}, 'domain_kg': [0., .06],
                    'feature_definitions': {'synthetic': True}, 'setting_hull': {'synthetic': True},
                    'source_code_semantics': 'synthetic'}
        for family in consumer.FAMILIES:
            path = self.producer/(family+'.json')
            artifact = {'family': family, 'model_id': 'synthetic/'+family, 'version': 'synthetic',
                        'units': self.pin['units'], 'domain_kg': self.pin['domain_kg'],
                        'feature_definitions': self.pin['feature_definitions'],
                        'setting_hull': self.pin['setting_hull'], 'source_code_semantics': 'synthetic', 'claims': claims}
            path.write_text(json.dumps(artifact))
            self.pin['models'][family] = {'path': path.name, 'model_id': artifact['model_id']}
        for path in self.producer.rglob('*.py'):
            self.pin['producer_files'][str(path.relative_to(self.producer))] = consumer.sha(path)
        for path in self.producer.glob('*.json'):
            self.pin['producer_files'][path.name] = consumer.sha(path)
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.invalid', 'commit', '-qm', 'synthetic producer')
        self.pin['producer_commit'] = consumer.git(self.producer, 'HEAD')
        self.pin['producer_tree'] = consumer.git(self.producer, 'HEAD^{tree}')
        self.handoff = self.root/'handoff.json'
        self.save()

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.producer), *args], check=True, capture_output=True)

    def save(self):
        self.handoff.write_text(json.dumps(self.pin))

    def load(self):
        return consumer.load_producer(self.producer, 'MTF', self.handoff)

    def test_correct_pin_and_installed_poison_cannot_influence_kernel(self):
        poison = types.ModuleType('puckworks.analysis.mass_delivery')
        poison.SENTINEL = 'installed poison'
        key = 'puckworks.analysis.mass_delivery'
        previous = sys.modules.get(key)
        sys.modules[key] = poison
        try:
            model, _ = self.load()
            self.assertEqual(model.family, 'MTF')
            ns = '_ewp_conditioned_mass_delivery_'+self.pin['producer_commit']
            self.assertEqual(sys.modules[ns+'.conditioned_mass_delivery'].kernel.SENTINEL, 'explicit synthetic producer')
        finally:
            if previous is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = previous

    def test_wrong_commit_and_tree(self):
        for field in ('producer_commit', 'producer_tree'):
            original = self.pin[field]
            self.pin[field] = '0'*40
            self.save()
            with self.assertRaises(ValueError):
                self.load()
            self.pin[field] = original

    def test_altered_wrapper_kernel_or_model(self):
        for relative in (*consumer.RUNTIME, 'MTF.json'):
            path = self.producer/relative
            original = path.read_bytes()
            path.write_bytes(original+b'\n')
            with self.assertRaises(ValueError):
                self.load()
            path.write_bytes(original)

    def test_missing_dependency_cannot_fall_back(self):
        (self.producer/consumer.RUNTIME[0]).unlink()
        with self.assertRaises(ValueError):
            self.load()

    def test_unbound_dependency_and_path_escape(self):
        self.pin['producer_files'].pop(consumer.RUNTIME[0])
        self.save()
        with self.assertRaises(ValueError):
            self.load()
        self.pin['producer_files'][consumer.RUNTIME[0]] = consumer.sha(self.producer/consumer.RUNTIME[0])
        self.pin['producer_files']['../handoff.json'] = consumer.sha(self.handoff)
        self.save()
        with self.assertRaises(ValueError):
            self.load()

    def test_explicit_model_selection(self):
        with self.assertRaises(ValueError):
            consumer.load_producer(self.producer, 'BEST', self.handoff)


@unittest.skipUnless(os.environ.get('CONDITIONED_MASS_PRODUCER'), 'explicit producer parity checkout not configured')
class ProducerParity(unittest.TestCase):
    def test_all_families_direct_kernel_and_consumer_parity(self):
        producer = Path(os.environ['CONDITIONED_MASS_PRODUCER'])
        for family in consumer.FAMILIES:
            model, pin = consumer.load_producer(producer, family)
            recipe = {'temperature_K': 363.15, 'source_flow_setting_code': 1.7}
            result = consumer.demonstrate(producer, family, **recipe)
            direct = model.predict([0., .01, .02], [.01, .02, .03], **recipe)
            self.assertEqual(result['interval_solute_kg'], direct.solute_kg.tolist())
            code = ('import json; from puckworks.analysis.conditioned_mass_delivery import Model; '
                    f'm=Model.load({pin["models"][family]["path"]!r}); '
                    'print(json.dumps(m.predict([0.,.01,.02],[.01,.02,.03],temperature_K=363.15,source_flow_setting_code=1.7).solute_kg.tolist()))')
            values = json.loads(subprocess.check_output([sys.executable, '-c', code], cwd=producer, text=True))
            self.assertEqual(values, result['interval_solute_kg'])


if __name__ == '__main__':
    unittest.main()
