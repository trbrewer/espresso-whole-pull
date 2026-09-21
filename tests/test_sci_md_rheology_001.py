"""Synthetic fixtures only; no redistributed measured tables."""
import unittest
import tempfile
import json
import math
from pathlib import Path
from unittest.mock import patch
from tools.sci_md_rheology_001 import analysis
from tools.sci_md_rheology_001.report import classify
from tools.sci_md_rheology_001.runner import budget_available
from tools.sci_md_rheology_001.analysis import np
from tools.sci_md_rheology_001.analysis import (solids_fraction,viscosity,resistance,errors,compare,
    axial_reduce,REF,AGGREGATE,straight_sided_wedge_scale,load_profile)

class RheologyTests(unittest.TestCase):
    def test_mass_basis(self):
        self.assertAlmostEqual(float(solids_fraction(100,900)),.1)
        self.assertNotAlmostEqual(float(solids_fraction(100,900)),100/900)
    def test_inventory(self):
        for model in ('indexed_passive_species_first_order_with_capacity_ceiling','caffeine',''):
            with self.assertRaises(ValueError): solids_fraction(1,965,model)
    def test_invalid_concentration(self):
        for c in (-1,np.nan,np.inf):
            with self.assertRaises(ValueError): solids_fraction(c,965)
    def test_water_and_units(self):
        calls=[]
        def measured(t,x):
            calls.append((t,x)); return .8e-3 # synthetic mPa.s -> Pa.s
        mu,dilute=viscosity(np.array([0,.05,.1,.24]),90,.4e-3,measured)
        np.testing.assert_allclose(mu,[.4e-3,.6e-3,.8e-3,.8e-3])
        self.assertTrue(all(t==363.15 for t,x in calls)); self.assertIn((363.15,76.),calls)
        self.assertEqual(dilute.tolist(),[True,True,False,False])
    def test_source_rejection(self):
        for w,t in ((.25,90),(.36,90),(-.01,90),(.1,100),(.1,0),(np.nan,90)):
            with self.assertRaises(ValueError): viscosity([w],t,.001,lambda t,x:.002)
    def test_stress(self):
        m,_=viscosity([0,.05,.1],90,.001,lambda t,x:.002,2)
        np.testing.assert_allclose(m,[.001,.002,.003])
    def test_uniform_darcy(self):
        self.assertAlmostEqual(resistance([2,2],[1,3],[4,4],2),1)
    def test_two_layer(self):
        self.assertAlmostEqual(resistance([2,3],[1,3],[4,6],2),1)
    def test_nonuniform_thickness(self):
        self.assertAlmostEqual(resistance([1,4],[1,3],[1,1],1),13)
    def test_constant_alpha(self):
        t=np.arange(3); p=dict(t=t,q=np.ones(3)*2,q0=np.ones(3)*4)
        alpha,m=compare({REF:p,'other':p}); self.assertEqual(alpha,.5)
        self.assertEqual(m['other']['residual']['peak'],0)
    def test_time_varying(self):
        alpha,m=compare({REF:dict(t=[0,1,2],q=[1,2,1],q0=np.ones(3)*2)})
        self.assertGreater(m[REF]['residual']['integrated'],0)
    def test_reference_only(self):
        p=dict(t=[0,1],q=[1,1],q0=np.array([2,2]))
        a,m=compare({REF:p,'other':dict(t=[0,1],q=[2,2],q0=np.array([2,2]))})
        self.assertEqual(a,.5);self.assertEqual(m['other']['residual']['integrated'],1)
    def test_correlation(self):
        self.assertGreater(resistance([4,1],[1,1],[1,4],1),resistance([1,4],[1,1],[1,4],1))
    def test_sector_nonuniform(self):
        scale=straight_sided_wedge_scale(5)
        centres=np.array([[.5,0,0],[.5,1,0],[2,0,0],[2,1,0]])
        z,dz,f=axial_reduce(centres,np.array([.5,.5,1,1])/scale,{'c':[1,1,2,2]},1,scale,3)
        np.testing.assert_allclose(dz,[1,2]);np.testing.assert_equal(f['c'],[1,2])
    def test_reject_radial(self):
        with self.assertRaises(ValueError): axial_reduce(np.array([[.5,0,0],[.5,1,0]]),np.array([.5,.5]),{'c':[1,2]},1,1,1)
    def test_deterministic(self):
        p={REF:dict(t=[0,1],q=[1,2],q0=np.array([2,2]))}
        self.assertEqual(compare(p),compare(p))
    def test_export_adapter_with_text_trace_columns(self):
        # Foundation12 geometry export and EWP mixed numeric/text CSV contract.
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'0').mkdir();(p/'30').mkdir();(p/'postProcessing/wholePull/0').mkdir(parents=True)
            scale=straight_sided_wedge_scale(5)
            s=dict(geometry=dict(axial_cells=2,radial_cells=1,basket_radius_m=1/math.sqrt(math.pi),wedge_angle_deg=5),
                   coffee_bed=dict(bed_depth_m=2,initial_porosity=.4),
                   liquid=dict(dynamic_viscosity_Pa_s=.001,density_kg_m3=965),
                   time=dict(field_write_interval_s=30),
                   extraction=dict(model=AGGREGATE),hydraulics=dict(target_inlet_pressure_gauge_Pa=1,outlet_pressure_gauge_Pa=0,saturated_permeability_m2=1))
            (p/'CASE_SCENARIO_V0_1_4.json').write_text(json.dumps(s))
            (p/'0/C').write_text('internalField nonuniform List<vector> 2 ((0.5 0 0) (1.5 0 0));')
            (p/'0/Vc').write_text('internalField uniform '+str(1/scale)+';')
            for name,value in dict(dissolvedConcentration=0,permeability=1,porosity=.4,saturation=1).items():
                (p/'30'/name).write_text('internalField uniform '+str(value)+';')
            (p/'postProcessing/wholePull/0/traces.csv').write_text(
                'time_s,outlet_flow_m3_s,radialToAxialVelocityRatio,bedMechanicsModel\n30,500,0,none\n')
            prof=load_profile(p,s,lambda t,x:.002,1)
            np.testing.assert_allclose(prof['q'],[500,500]);self.assertLess(prof['hydraulic_relative_error'],1e-14)
            s['liquid']['density_kg_m3']=1000
            with self.assertRaises(ValueError):load_profile(p,s,lambda t,x:.002,1)
    def test_decision_surface(self):
        def metric(a,b): return {REF:dict(absolute=dict(integrated=a,peak=a),residual=dict(integrated=b,peak=b))}
        for a,b,expected in [(0.01,.01,'SMALL_WITHIN_TESTED_ENVELOPE'),(.08,.01,'STATIC_SCALE_SUFFICIENT'),(.12,.08,'STATE_DEPENDENT_EFFECT')]:
            self.assertEqual(classify(metric(a,b),[.001,.001])[0],expected)
        self.assertIsNone(classify(metric(.0495,.01),[.001,.001])[0])
        self.assertIsNone(classify(metric(.01,.01),[.005,.001])[0])
    def test_budget_includes_failures(self):
        self.assertFalse(budget_available([dict(kind='primary',status='FAILED')]*6,'primary'))
        self.assertTrue(budget_available([dict(kind='primary')]*6,'spatial'))
        self.assertFalse(budget_available([dict(kind='temporal')]*3+[dict(kind='spatial')]*3,'temporal'))
    def test_audit_binding_rejects_wrong_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audit.json';p.write_text(json.dumps(dict(disposition='PASS',independent_reviewer='synthetic',freeze_sha256='wrong')))
            with self.assertRaises(ValueError): analysis.check_freeze(p)
    def test_runtime_lock_guard(self):
        real=analysis.sha
        with patch.object(analysis,'sha',side_effect=lambda p:'changed' if str(p).endswith('puckworks.lock.json') else real(p)):
            with self.assertRaisesRegex(ValueError,'runtime lock'): analysis.check_freeze('unused')
    def test_discrete_continuum_gate_is_feasible(self):
        cases=json.loads((analysis.DOC/'SCENARIOS.json').read_text())
        for s in cases.values():
            k,dz=analysis.discrete_layered_pressure_reference.__globals__['axial_permeability_profile'](s)
            r=resistance(np.full(len(k),s['liquid']['dynamic_viscosity_Pa_s']),np.full(len(k),dz),k,math.pi*.029**2)
            q=s['hydraulics']['target_inlet_pressure_gauge_Pa']/r
            qd=analysis.discrete_layered_pressure_reference(s)['outlet_flow_m3_s']
            self.assertLess(abs(qd/q-1),.001)
    def test_positive_window(self):
        with self.assertRaises(ValueError): errors([0,1],[1,1],[0,1])

if __name__=='__main__':unittest.main()
