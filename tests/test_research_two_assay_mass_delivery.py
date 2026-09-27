"""Offline producer identity adversaries; explicit public producer parity."""
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
spec = importlib.util.spec_from_file_location('two_assay_consumer', ROOT/'scripts/research_two_assay_mass_delivery.py')
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
        (runtime/'mass_delivery.py').write_text('SENTINEL="explicit synthetic producer"\n')
        (runtime/'conditioned_mass_delivery.py').write_text('from . import mass_delivery as kernel\n')
        (runtime/'anchored_mass_delivery.py').write_text(
            'from . import mass_delivery as kernel\nfrom . import conditioned_mass_delivery as conditioned\n')
        (runtime/'two_assay_mass_delivery.py').write_text(
            'from . import mass_delivery as kernel\nfrom . import anchored_mass_delivery as legacy\n'
            'import json,hashlib\nfrom types import SimpleNamespace\n'
            'VERSION="synthetic"\nUNITS={"beverage":"kg"}\nCLAIMS=("RESEARCH_ONLY",)\n'
            'ARMS='+repr(consumer.ARMS)+'\nstrict_json=json.loads\n'
            'class FrozenBase:\n @staticmethod\n def load(path):\n'
            '  raw=path.read_bytes();d=json.loads(raw)\n'
            '  return SimpleNamespace(artifact_json=raw.decode(),sha256=hashlib.sha256(raw).hexdigest(),model_id=d["model_id"])\n')
        self.pin = {'runtime_modules': list(consumer.RUNTIME), 'producer_files': {},
            'models': {}, 'state_schema': 'synthetic', 'state_units': {'beverage':'kg'},
            'required_state_claims':['RESEARCH_ONLY'], 'source_rights':'synthetic', 'base_domain_kg':[0.,.06]}
        for family in ('MASS','EMPIRICAL'):
            model = dict(model_id='synthetic/'+family,family=family,version='synthetic',
                         units={'beverage':'kg'},domain_kg=[0.,.06],rights='synthetic')
            path = self.producer/(family+'.json')
            path.write_text(json.dumps(model))
            self.pin['models'][family] = dict(path=path.name,**{k:model[k] for k in ('model_id','family','version','units')})
        for relative in (*consumer.RUNTIME,'MASS.json','EMPIRICAL.json'):
            self.pin['producer_files'][relative] = consumer.sha(self.producer/relative)
        self.git('init','-q'); self.git('add','.')
        self.git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','fixture')
        self.pin['producer_commit'] = consumer.git(self.producer,'HEAD')
        self.pin['producer_tree'] = consumer.git(self.producer,'HEAD^{tree}')
        self.handoff = self.root/'handoff.json'
        self.save()

    def git(self,*args):
        subprocess.run(['git','-C',str(self.producer),*args],check=True,capture_output=True)

    def save(self):
        self.handoff.write_text(json.dumps(self.pin))

    def load(self):
        return consumer.load_producer(self.producer,handoff_path=self.handoff)

    def test_every_transitive_module_model_and_exact_commit_tree_enforced(self):
        self.load()
        for relative in self.pin['producer_files']:
            path = self.producer/relative; content=path.read_bytes();path.write_bytes(content+b'\n')
            with self.assertRaisesRegex(ValueError,'HASH_OR_PATH'):self.load()
            path.write_bytes(content)
        for key in ('producer_commit','producer_tree'):
            original=self.pin[key];self.pin[key]='0'*40;self.save()
            with self.assertRaisesRegex(ValueError,'REVISION_OR_TREE'):self.load()
            self.pin[key]=original

    def test_installed_package_poison_cannot_enter_runtime(self):
        name='puckworks.analysis.two_assay_mass_delivery';old=sys.modules.get(name)
        sys.modules[name]=types.ModuleType(name)
        try:
            md,_,_=self.load()
            self.assertEqual(md.kernel.SENTINEL,'explicit synthetic producer')
            self.assertIs(md.kernel,md.legacy.kernel)
        finally:
            if old is None:sys.modules.pop(name,None)
            else:sys.modules[name]=old

    def test_missing_binding_path_escape_and_incomplete_runtime(self):
        original=self.pin['producer_files'].copy()
        self.pin['producer_files'].pop(consumer.RUNTIME[1]);self.save()
        with self.assertRaisesRegex(ValueError,'UNBOUND_RUNTIME'):self.load()
        self.pin['producer_files']=original
        self.pin['producer_files']['../handoff.json']=consumer.sha(self.handoff);self.save()
        with self.assertRaisesRegex(ValueError,'HASH_OR_PATH'):self.load()
        self.pin['producer_files'].pop('../handoff.json');self.pin['runtime_modules'].pop();self.save()
        with self.assertRaisesRegex(ValueError,'COMPLETE_RUNTIME'):self.load()

    def test_model_support_and_state_units_enforced(self):
        for key,value in [('base_domain_kg',[0.,.07]),('state_units',{}),('state_schema','stale'),('required_state_claims',['FALSE_CLAIM'])]:
            old=self.pin[key];self.pin[key]=value;self.save()
            with self.assertRaises(ValueError):self.load()
            self.pin[key]=old

    def test_real_output_not_allowed_in_checkout(self):
        with self.assertRaisesRegex(ValueError,'OUTSIDE_GIT'):
            consumer.private_output(ROOT/'real.json',self.producer)
        with self.assertRaisesRegex(ValueError,'OUTSIDE_GIT'):
            consumer.private_output(self.producer/'real.json',self.producer)
        self.assertEqual(consumer.private_output(self.root/'private.json',self.producer),self.root/'private.json')


@unittest.skipUnless(os.environ.get('SCI_MD_MASS_DELIVERY_005_PRODUCER'),'explicit producer checkout unavailable')
class ProducerParity(unittest.TestCase):
    def test_all_six_arms_supplied_json_and_direct_producer_parity(self):
        producer=Path(os.environ['SCI_MD_MASS_DELIVERY_005_PRODUCER'])
        for arm in consumer.ARMS:
            md,base,_=consumer.load_producer(producer,arm)
            observations=asdict(md.synthetic_pair())
            queries=[{'start_kg':.008,'end_kg':.02}]
            direct=md.FittedState(base,md.ObservationPair.from_dict(observations),arm)
            expected=asdict(direct.predict_intervals((md.IntervalQuery(.008,.02),))[0])
            actual=consumer.predict(producer,observations,queries,arm=arm,stop_kg=.04)
            self.assertEqual(actual['predictions'],[expected])
            self.assertEqual(actual['conditional_remaining'],asdict(direct.remaining_solute(.04)))
            self.assertEqual(actual['input_class'],'SYNTHETIC_TWO_ASSAY_INPUT')
            with self.assertRaisesRegex(ValueError,'COORDINATE_ONLY'):
                consumer.predict(producer,observations,[dict(queries[0],later_tds=4.)],arm=arm)

    def test_cli_accepts_actual_observation_files_and_writes_exclusively(self):
        producer=Path(os.environ['SCI_MD_MASS_DELIVERY_005_PRODUCER'])
        md,_,_=consumer.load_producer(producer)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);obs=root/'obs.json';queries=root/'queries.json';output=root/'result.json'
            obs.write_text(json.dumps(asdict(md.synthetic_pair())))
            queries.write_text('[{"start_kg":0.008,"end_kg":0.02}]')
            cmd=[sys.executable,str(ROOT/'scripts/research_two_assay_mass_delivery.py'),
                 '--producer',str(producer),'--observations',str(obs),'--queries',str(queries),'--output',str(output)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(output.read_text())['input_class'],'SYNTHETIC_TWO_ASSAY_INPUT')
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main()
