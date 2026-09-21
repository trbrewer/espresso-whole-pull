"""Ordinary CI uses synthetic tables only; native fixtures are separately recorded."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.aggregate_viscosity import contract
from tools.sci_md_rheology_002.run import scenario, ROOT
from tools.sci_md_rheology_002.export import HEADER
from tools.sci_md_rheology_002.analyze import errors, classify


class Rheology002(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.exe=cls.root/'evaluate'
        subprocess.run(['c++','-std=c++11','-O2',str(ROOT/'tools/sci_md_rheology_002/evaluator.cpp'),'-o',str(cls.exe)],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.table=self.root/'synthetic.table';self.table.write_text(HEADER+'0 0.001\n0.1 0.002\n0.24 0.005\n')
        self.s=scenario('uniform_9bar');self.s['aggregate_viscosity']=dict(mode='coupled',purpose='synthetic',table=str(self.table))

    def evaluate(self,c):return subprocess.run([str(self.exe),str(self.table)],input=c,text=True,capture_output=True)

    def test_native_dense_mapping(self):
        w=[.24*i/2400 for i in range(2401)]
        c=[965*x/(1-x) for x in w]
        r=self.evaluate('\n'.join(map(str,c)));self.assertEqual(r.returncode,0,r.stderr)
        actual=list(map(float,r.stdout.split()))
        self.assertEqual(len(actual),len(w))
        for x,y in zip(w,actual):
            expected=.001+.01*x if x<=.1 else .002+(x-.1)*.003/.14
            self.assertLessEqual(abs(y/expected-1),1e-12)

    def test_native_domains(self):
        for c in ('-1','1000','nan','inf'):
            with self.subTest(c=c):self.assertNotEqual(self.evaluate(c).returncode,0)

    def test_table_rejections(self):
        for body in ('0 .001\n0.1 0\n.24 .005','0 .001\n.1 .002\n.1 .003\n.24 .005',
                     '0 .001\n.24 .005','0 .001\n.1 .002\n.23 .005','0 .001\n.1 nan\n.24 .005',
                     '0 .001\n.1 .002\n.24 .005\ngarbage','0 .001\n.1 .002\n.24'):
            with self.subTest(body=body):
                self.table.write_text(HEADER+body);self.assertNotEqual(self.evaluate('0').returncode,0)
                with self.assertRaises(ValueError):contract(self.s)

    def test_malformed_terminal_tokens_without_newline(self):
        valid = self.table.read_text()
        for token in ('1e999', '1e', '-', 'nan', 'inf', '.24', '.24 1e999'):
            with self.subTest(token=token):
                self.table.write_text(valid+token)
                self.assertNotEqual(self.evaluate('0').returncode, 0)
                with self.assertRaises(ValueError):contract(self.s)
        self.table.write_text(valid.rstrip())
        self.assertEqual(self.evaluate('0').returncode, 0)

    def test_metadata_rejections(self):
        for old,new in [('Pa.s','mPa.s'),('wet_mass_fraction','percent'),('363.15','360'),('965','1000'),('linear','cubic')]:
            with self.subTest(old=old):
                self.table.write_text(HEADER.replace(old,new)+'0 .001\n.1 .002\n.24 .005')
                self.assertNotEqual(self.evaluate('0').returncode,0)
                with self.assertRaises(ValueError):contract(self.s)

    def test_default_and_disabled_require_nothing(self):
        self.assertEqual(contract({}),'')
        self.assertEqual(contract({'aggregate_viscosity':dict(mode='off',table='missing')}),'')

    def test_case_contract_rejections(self):
        mutations=[('pressureBoundaryModel','prescribedFlow'),('flowResistanceModel','darcyForchheimer'),('bedMechanicsModel','waszkiewiczQuasiStaticCompaction')]
        for k,v in mutations:
            s=copy.deepcopy(self.s);s[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):contract(s)
        for group,k,v in [('hydraulics','pressure_ramp_time_s',1),('liquid','temperature_K',360),('liquid','density_kg_m3',1000),
                          ('wetting','initial_saturation',.5),('wetting','initial_wet_front_m',0),('extraction','model','indexedPassiveSpecies')]:
            s=copy.deepcopy(self.s);s[group][k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):contract(s)
        self.assertIn('aggregateViscosityMode coupled',contract(self.s))

    def test_exact_scenarios(self):
        predecessor=json.loads((ROOT/'docs/analysis/sci_md_rheology_001/SCENARIOS.json').read_text())
        for name in ('uniform_9bar','reversed_3bar'):self.assertEqual(scenario(name),predecessor[name])

    def test_interval_metrics_include_first(self):
        self.assertEqual(errors([2,1],[1,1],[1,1]),{'integrated':.5,'peak':1.})
        with self.assertRaises(ValueError):errors([1],[0],[1])

    def test_classification_precedence(self):
        metrics={n:{c:dict(integrated=.01,peak=.02) for c in ('C_W','C_N')} for n in ('uniform_9bar','reversed_3bar')}
        uncertainty=copy.deepcopy(metrics)
        for v in uncertainty.values():
            for u in v.values():u.update(integrated=.001,peak=.001)
        self.assertEqual(classify(metrics,uncertainty,True),'SMALL_COUPLED_EFFECT')
        metrics['reversed_3bar']['C_N']['peak']=.2
        self.assertEqual(classify(metrics,uncertainty,True),'COUPLED_STATE_DEPENDENCE_PERSISTS')
        self.assertEqual(classify(metrics,uncertainty,False),'NUMERICALLY_UNRESOLVED')

    def test_package_cli_discovery(self):
        for module in ('export','run','analyze','verify'):
            r=subprocess.run(['python3','-m','tools.sci_md_rheology_002.'+module,'--help'],cwd=ROOT,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
