"""Synthetic fixtures for the independent storage closure and decision arithmetic."""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tools.sci_md_rheology_002.run import ROOT, scenario
from tools.sci_md_rheology_002.export import HEADER
from scripts.aggregate_viscosity import contract

class BulkClosureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.table=self.root/'law.table'
        self.table.write_text(HEADER+'0 .001\n.1 .002\n.24 .006\n')
    def test_native_analytical(self):
        constant=self.root/'constant.table';constant.write_text(HEADER+'0 .001\n.1 .001\n.24 .001\n')
        exe=self.root/'fixture'
        subprocess.run(['c++','-std=c++11','-O2',str(ROOT/'tools/sci_md_rheology_005/analytical.cpp'),'-o',str(exe)],check=True)
        subprocess.run([str(exe),str(self.table),str(constant)],check=True)
    def test_generation_modes(self):
        s=scenario('uniform_9bar');self.assertEqual(contract(s),'')
        s['aggregate_viscosity']={'mode':'off','table':'missing'};self.assertEqual(contract(s),'')
        for mode in ('observe','coupled','bulkCoupled'):
            s['aggregate_viscosity']={'mode':mode,'table':str(self.table)}
            self.assertIn('aggregateViscosityMode '+mode+';',contract(s))
    def test_generation_rejects_unsupported(self):
        s=scenario('uniform_9bar');s['aggregate_viscosity']={'mode':'bulkCoupled','table':str(self.table)}
        changes=[('flowResistanceModel',None,'forchheimer'),('bedMechanicsModel',None,'poroelastic'),
            ('hydraulics','pressure_boundary_model','prescribedFlow'),('hydraulics','pressure_boundary_model','prescribedPressureHistory'),
            ('hydraulics','pressure_ramp_time_s',1),('wetting','initial_saturation',.5),
            ('wetting','initial_wet_front_m',0),('liquid','density_kg_m3',1000),('liquid','temperature_K',360),
            ('time','start_s',1),('extraction','model','indexed')]
        for section,key,value in changes:
            q=copy.deepcopy(s)
            if key is None:q[section]=value
            else:q[section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):contract(q)
        q=copy.deepcopy(s);q['effective_permeability_evolution']={}
        with self.assertRaises(ValueError):contract(q)

class DecisionTests(unittest.TestCase):
    def test_budget_edges_and_failure_precedence(self):
        from tools.sci_md_rheology_005.analyze import decide,disposition
        self.assertEqual(decide(.008,.001,.01),'QUALIFIED_PASS')
        self.assertEqual(decide(.012,.001,.01),'QUALIFIED_FAILURE')
        self.assertEqual(decide(.01,.001,.01),'UNRESOLVED')
        self.assertEqual(decide(.1,.003,.01),'UNRESOLVED')
        self.assertEqual(disposition(['QUALIFIED_FAILURE','UNRESOLVED'],False,False),'BULK_STATE_CLOSURE_INSUFFICIENT')
        self.assertEqual(disposition(['QUALIFIED_PASS'],True,False),'BULK_STATE_CLOSURE_UNRESOLVED')
    def test_C_denominator_and_first_interval(self):
        from tools.sci_md_rheology_005.analyze import hydraulic,operator
        def d(q,qc=None):
            q=np.array(q,float)
            return dict(start_s=np.array([0.,10.]),end_s=np.array([10.,30.]),state_s=np.array([0.,10.]),
                dt_s=np.array([10.,20.]),Q_m3_s=q,volume_m3=q*np.array([10.,20.]),Q_cont_m3_s=q if qc is None else np.array(qc))
        c=d([2,2]);g=d([4,2]);m=hydraulic(g,c)
        self.assertAlmostEqual(m['E_Qint'],1/3);self.assertEqual(m['E_Qpeak'],1.)
        op=operator(d([4,2],[3.9,1.99]),d([2,2],[1.99,1.98]))
        self.assertGreater(op['E_Qint']['C'],0);self.assertGreater(op['E_Qint']['G'],0);self.assertGreater(op['E_Qint']['denominator'],0)
    def test_mass_observer_C_denominator(self):
        from tools.sci_md_rheology_004.observer import compare
        def h(s):return dict(B=np.array([0.,1.,2.]),S=np.array([0.,s,2*s]),W=np.array([0.,1-s,2-2*s]),t=np.array([0.,1.,2.]))
        v=compare(h(.2),h(.1),'B',2)
        self.assertAlmostEqual(v['E_path'],1.)
        self.assertAlmostEqual(v['max_fraction_TDS_pp'],10.)
        self.assertIsNone(v['C']['cumulative_TDS_percent'][0])
