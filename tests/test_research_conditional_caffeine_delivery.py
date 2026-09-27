"""Offline hash/namespace adversaries and exact public-producer parity."""
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

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tail_consumer',ROOT/'scripts/research_conditional_caffeine_delivery.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.producer=self.root/'producer'
        runtime=self.producer/c.RUNTIME;runtime.parent.mkdir(parents=True)
        runtime.write_text('import json\nfrom types import SimpleNamespace\n'
            'VERSION="synthetic"\nUNITS={"beverage":"kg"}\nCLAIMS=("RESEARCH_ONLY",)\n'
            'PARENT_RUNTIME_SHA256="parent-runtime"\nFINAL_PARENT_SHA256="parent-model"\nSENTINEL="explicit"\nclass Model:\n @classmethod\n def load(cls,path):\n'
            '  value=json.loads(path.read_text())\n  return SimpleNamespace(**value,to_dict=lambda: {"parent_sha256":"parent-model"})\n')
        self.pin={'runtime_modules':[c.RUNTIME,c.PARENT_RUNTIME],'models':{},'schema':'synthetic',
            'units':{'beverage':'kg'},'claims':['RESEARCH_ONLY'],'domain_kg':[0.,.08],
            'rights':'SYNTHETIC','parent_runtime_sha256':'parent-runtime','parent_model_sha256':'parent-model','producer_files':{c.RUNTIME:c.sha(runtime)}}
        for arm in ('D0','S0','S1','S2'):
            path=self.producer/(arm+'.json')
            path.write_text(json.dumps({'arm':arm,'sha256':'synthetic-'+arm,'domain_kg':.08,'rights':'SYNTHETIC'}))
            self.pin['models'][arm]={'path':path.name,'model_sha256':'synthetic-'+arm}
            self.pin['producer_files'][path.name]=c.sha(path)
        for args in [('init','-q'),('add','.'),('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','fixture')]:
            subprocess.run(['git','-C',str(self.producer),*args],check=True,capture_output=True)
        for relative in (c.PARENT_RUNTIME,c.PARENT_MODEL):
            p=self.producer/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('synthetic parent')
            self.pin['producer_files'][relative]=c.sha(p)
        for args in [('add','.'),('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','parent fixture')]:
            subprocess.run(['git','-C',str(self.producer),*args],check=True,capture_output=True)
        self.pin.update(producer_commit=c.git(self.producer,'HEAD'),producer_tree=c.git(self.producer,'HEAD^{tree}'))
        self.handoff=self.root/'handoff.json';self.save()

    def save(self):
        self.handoff.write_text(json.dumps(self.pin))

    def load(self):
        return c.load_producer(self.producer,handoff_path=self.handoff)

    def test_exact_hashes_commit_and_tree(self):
        self.load()
        for relative in self.pin['producer_files']:
            path=self.producer/relative;old=path.read_bytes();path.write_bytes(old+b'\n')
            with self.assertRaisesRegex(ValueError,'HASH_OR_PATH'):self.load()
            path.write_bytes(old)
        for key in ('producer_commit','producer_tree'):
            old=self.pin[key];self.pin[key]='0'*40;self.save()
            with self.assertRaisesRegex(ValueError,'EXACT_EVALUATED'):self.load()
            self.pin[key]=old

    def test_package_poison_does_not_enter_isolated_runtime(self):
        key='puckworks.analysis.conditional_caffeine_delivery';old=sys.modules.get(key)
        sys.modules[key]=types.ModuleType(key)
        try:
            module,_,_=self.load();self.assertEqual(module.SENTINEL,'explicit')
        finally:
            if old is None:sys.modules.pop(key,None)
            else:sys.modules[key]=old

    def test_missing_binding_bad_units_and_domain(self):
        old=self.pin['producer_files'].pop(c.RUNTIME);self.save()
        with self.assertRaisesRegex(ValueError,'EXACT_BOUND'):self.load()
        self.pin['producer_files'][c.RUNTIME]=old
        for key,value in [('units',{}),('domain_kg',[0.,.10]),('schema','bad'),('claims',[])]:
            old=self.pin[key];self.pin[key]=value;self.save()
            with self.assertRaises(ValueError):self.load()
            self.pin[key]=old


@unittest.skipUnless(os.environ.get('SCI_MD_CAFFEINE_DELIVERY_001_PRODUCER'),'explicit producer unavailable')
class ProducerParity(unittest.TestCase):
    def test_all_arms_condition_interval_remaining_and_extra_chemistry_rejection(self):
        producer=Path(os.environ['SCI_MD_CAFFEINE_DELIVERY_001_PRODUCER'])
        for arm in ('D0','S0','S1','S2'):
            module,model,_=c.load_producer(producer,arm)
            inputs=module.EarlyInput(arm,(.004,.004,.15,.10)[:len(module.feature_names(arm))],'SYNTHETIC')
            direct=model.condition(inputs)
            result=c.predict(producer,inputs.to_dict(),[{'start_kg':.008,'end_kg':.02}],arm=arm,stop_kg=.04)
            self.assertEqual(result['predictions'],[asdict(direct.predict_intervals([.008],[.02])[0])])
            self.assertEqual(result['remaining_caffeine'],asdict(direct.remaining_caffeine(.04)))
            with self.assertRaisesRegex(ValueError,'COORDINATE_ONLY'):
                c.predict(producer,inputs.to_dict(),[{'start_kg':.008,'end_kg':.02,'future_TDS':10}],arm=arm)

    def test_cli_supplied_files_exclusive_output(self):
        producer=Path(os.environ['SCI_MD_CAFFEINE_DELIVERY_001_PRODUCER'])
        module,_,_=c.load_producer(producer)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);early=root/'early.json';queries=root/'queries.json';out=root/'output.json'
            early.write_text(json.dumps(module.EarlyInput('S2',(.004,.004,.15,.10),'SYNTHETIC').to_dict()))
            queries.write_text('[{"start_kg":0.008,"end_kg":0.02}]')
            cmd=[sys.executable,str(ROOT/'scripts/research_conditional_caffeine_delivery.py'),'--producer',str(producer),
                '--early-inputs',str(early),'--queries',str(queries),'--output',str(out)]
            done=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(done.returncode,0,done.stderr)
            self.assertEqual(json.loads(out.read_text())['input_class'],'SYNTHETIC')
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main()
