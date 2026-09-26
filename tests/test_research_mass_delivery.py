"""Identity-bound consumer tests using a synthetic producer, no source files."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('consumer', ROOT/'scripts/research_mass_delivery.py')
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)

# A schema-only fake producer tests handoff enforcement; it contains no numerical kernel.
STUB = '''import json
from types import SimpleNamespace
class Model:
    @classmethod
    def load(cls, path):
        return SimpleNamespace(**json.loads(path.read_text()))
'''


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'kernel.py').write_text(STUB)
        self.model = {'model_id':'synthetic','version':'mass-delivery/1','family':'MASS',
                      'units':{'beverage':'kg'},'domain_kg':[0,.06],
                      'claims':['RESEARCH_ONLY','SOURCE_INTERNAL','TARGET_EXPOSED',
                                'PHYSICAL_VALIDATION_NOT_ESTABLISHED']}
        (self.root/'model.json').write_text(json.dumps(self.model))
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Synthetic Test','-c',
                        'user.email=synthetic@example.invalid','commit','-qm','synthetic producer'],check=True)
        self.pin = {'producer_commit':consumer.git(self.root,'HEAD'),
                    'producer_tree':consumer.git(self.root,'HEAD^{tree}'),
                    'kernel_path':'kernel.py','model_path':'model.json',
                    'producer_files':{p:consumer.sha(self.root/p) for p in ['kernel.py','model.json']},
                    'model_id':'synthetic','model_version':'mass-delivery/1',
                    'units':self.model['units'],'domain_kg':[0,.06]}
        self.handoff = self.root/'handoff.json'
        self.write_pin()

    def write_pin(self):
        self.handoff.write_text(json.dumps(self.pin))

    def test_explicit_identity_load(self):
        model,pin = consumer.load_producer(self.root,self.handoff)
        self.assertEqual(model.model_id,'synthetic')
        self.assertEqual(pin['producer_commit'],consumer.git(self.root,'HEAD'))

    def test_wrong_revision_or_tree(self):
        for key in ['producer_commit','producer_tree']:
            original=self.pin[key]; self.pin[key]='0'*40; self.write_pin()
            with self.assertRaisesRegex(ValueError,'revision/tree'):
                consumer.load_producer(self.root,self.handoff)
            self.pin[key]=original

    def test_dirty_producer_bytes_rejected(self):
        (self.root/'kernel.py').write_text(STUB+'\n# modified')
        with self.assertRaisesRegex(ValueError,'hash/path'):
            consumer.load_producer(self.root,self.handoff)

    def test_wrong_model_domain_units_or_identity(self):
        for key,value in [('model_id','wrong'),('model_version','future'),('domain_kg',[0,1]),('units',{'beverage':'g'})]:
            original=self.pin[key]; self.pin[key]=value; self.write_pin()
            with self.assertRaises(ValueError): consumer.load_producer(self.root,self.handoff)
            self.pin[key]=original

    def test_unbound_artifact_rejected(self):
        del self.pin['producer_files']['model.json']; self.write_pin()
        with self.assertRaisesRegex(ValueError,'unbound'):
            consumer.load_producer(self.root,self.handoff)


if __name__ == '__main__':
    unittest.main()
