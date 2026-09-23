"""Focused contract, observation and execution-order regression tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tools.sci_md_rheology_010 import common as c
from tools.sci_md_rheology_010 import analyze as a
from tools.sci_md_rheology_010.run import reserve, check_assignment, field_check, complete
from tools.sci_md_rheology_007.observer import decide, history
from tools.sci_md_rheology_004.observer import compare

class ReversalTests(unittest.TestCase):
    def test_algebra_not_swap(self):
        k=c.permeability();i,o=k.values()
        self.assertGreater(i,0);self.assertGreater(o,0);self.assertEqual(i/o,.25)
        self.assertAlmostEqual((.25*i+.75*o)/1.3125e-15,1,places=15)
        self.assertAlmostEqual(.25*i/(.25*i+.75*o),1/13,places=15)
        self.assertNotEqual(.25*7.5e-16+.75*3e-15,1.3125e-15)
    def test_matrix(self):
        m=c.matrix();self.assertEqual(len(m),32);self.assertEqual(len(c.references()),18)
        self.assertEqual(sum(v['model']=='E2' for v in m.values()),14)
        self.assertEqual(sum(v['resolution']=='radial' for v in m.values()),4)
        self.assertFalse(any(v['model']=='E2' and v['resolution']=='radial' for v in m.values()))
    def test_only_permeability_changes(self):
        from tools.sci_md_rheology_009.common import radial,history
        old=history(radial(),'UP');new=c.reverse(old);check=copy.deepcopy(new)
        check['hydraulics']['permeability_profile']=old['hydraulics']['permeability_profile']
        self.assertEqual(check,old);self.assertEqual(old['hydraulics']['permeability_profile']['inner_permeability_m2'],3e-15)
    def test_region_assignment_and_core_label(self):
        s={'hydraulics':{'permeability_profile':c.permeability()}}
        zone=np.array([True,False]);i,o=c.permeability().values()
        values=dict(permeabilityZoneId=np.array([0.,1.]),permeability=np.array([i,o]))
        check_assignment(values,zone,s)
        values['permeability']=np.array([o,i])
        with self.assertRaises(ValueError):check_assignment(values,zone,s)
        values['permeability']=np.array([i,o]);values['permeabilityZoneId']=np.array([1.,0.])
        with self.assertRaises(ValueError):check_assignment(values,zone,s)
    def test_actual_generated_short_mesh_if_retained(self):
        import os
        if not os.environ.get('RHEOLOGY010_ARTIFACTS'):self.skipTest('external native artifacts not configured')
        art=Path(os.environ['RHEOLOGY010_ARTIFACTS']);specs=json.loads((art/'SHORT_SCENARIOS.json').read_text())
        for model in ('C','E2'):
            k=model+'_up';e=complete(art,[k])[k]
            self.assertEqual(field_check(art/'runs'/e['id']/'case',specs[k])['permeability_assignment'],'PASS')
    def test_inherited_contract_complete(self):
        current=json.loads((c.DOC/'CONTRACT.json').read_text())
        self.assertEqual(current['limits'],c.INHERITED['limits']);self.assertEqual(current['budgets'],c.INHERITED['budgets'])
        self.assertEqual(set(c.LIMITS),{'water_balance_kg','solute_balance_kg','absolute_correction_sum_kg','c_min_kg_m3','c_max_kg_m3','w_max','inventory_min_kg','inventory_max_kg','storage_min_kg','Qdt_volume_m3','water_increment_kg','reverse_relative','regional_flow_sum_relative','geometry_relative','face_alignment_m','field_mass_kg','clock_end_s','clock_dt_s','analytical_relative','pressure_Pa','baseline_normalized','repeat_absolute','mpi_relative','mpi_floors','allowance_budget_fraction'})
    def test_all_36_references_required(self):
        d={config+'_'+k:'0.01234567891' for config in ('old','new') for k in c.references()}
        self.assertEqual(c.support(d),{'UP':'0.011728394','DOWN':'0.011728394'})
        for bad in [dict(list(d.items())[1:]),dict(d,extra='.1')]:
            with self.assertRaises(ValueError):c.support(bad)
        for value in ('NaN','0','-1'):
            bad=dict(d);bad[next(iter(bad))]=value
            with self.assertRaises(ValueError):c.support(bad)
    def test_sealed_support_order_and_recompute(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);doc=root/'doc';doc.mkdir();(doc/'FREEZE.json').write_text('{}')
            terminals={config+'_'+k:.01 for config in ('old','new') for k in c.references()}
            hashes={k:'h' for k in terminals};sealed=dict(B_star_kg=c.support(terminals),C_terminals_kg=terminals,C_traces=hashes,freeze_sha256=c.sha(doc/'FREEZE.json'))
            def save():
                for p in [doc/'SUPPORT.json',root/'SUPPORT.json']:c.write(p,sealed)
                h=c.sha(doc/'SUPPORT.json');c.write(doc/'SUPPORT_RECEIPT.json',dict(sha256=h));return h
            h=save();ev=[dict(status='SUPPORT_SEALED',sha256=h,stage='support')]
            with patch.object(a,'DOC',doc),patch.object(a,'reference_data',return_value=({},terminals,hashes,{})),patch.object(a,'events',return_value=ev):
                a.checked_support(root)
                ev.insert(0,dict(status='STARTED',stage='E2'))
                with self.assertRaises(ValueError):a.checked_support(root)
                ev.pop(0);sealed['B_star_kg']['UP']='.001';ev[0]['sha256']=save()
                with self.assertRaises(ValueError):a.checked_support(root)
    def test_immutable_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'trace';p.write_text('original');identity={'trace':c.sha(p)}
            c.verify_files(root,identity);p.write_text('changed')
            with self.assertRaises(ValueError):c.verify_files(root,identity)
    def test_zero_origin_first_increment_conservative_split(self):
        d=dict(water_kg=np.array([.008,.018]),solute_kg=np.array([.002,.002]),end_s=np.array([1.,2.]))
        h=history(d);self.assertEqual(h['B'][0],0);self.assertEqual(h['S'][1],.002)
        result=compare(h,h,'B',float(h['B'][-1]))
        np.testing.assert_allclose(result['C']['TDS_percent'],[20,20,10,0,0],atol=1e-13)
        self.assertEqual(result['E_path'],0)
    def test_union_native_mass_breakpoints(self):
        x=dict(B=np.array([0.,.01,.02]),S=np.array([0.,.002,.002]),W=np.array([0.,.008,.018]),t=np.array([0.,1.,2.]))
        y=dict(B=np.array([0.,.015,.02]),S=np.array([0.,.0015,.002]),W=np.array([0.,.0135,.018]),t=np.array([0.,1.,2.]))
        r=compare(x,y,'B',.02);self.assertAlmostEqual(r['E_path'],.5);self.assertEqual(r['breakpoint_count'],4)
    def test_short_candidate_support_retains_hydraulics(self):
        d=dict(start_s=np.array([0.]),end_s=np.array([30.]),state_s=np.array([0.]),dt_s=np.array([30.]),Q=np.array([1e-7]),share=np.array([1/13]),water_kg=np.array([.009]),solute_kg=np.array([.001]))
        m=c.metrics(d,d,.011);self.assertIsNone(m['E_Spath']);self.assertIsNone(m['D_TDS_pp']);self.assertEqual(m['E_Qint'],0)
    def test_strict_thresholds_and_allowance_ceiling(self):
        for v,u,expected in [(1.,0.,'UNRESOLVED'),(.875,.125,'UNRESOLVED'),(1.125,.125,'UNRESOLVED'),(.5,.2,'PASS'),(.5,.20000001,'UNRESOLVED'),(1.5,.1,'FAIL')]:
            self.assertEqual(decide(v,u,1),expected)
    def test_separate_radial_pairings(self):
        self.assertEqual(c.pair_keys('TR_LINEAR','UP','radial'),('new_E2_TR_LINEAR_UP_base','new_C_TR_LINEAR_UP_radial'))
        self.assertEqual(c.pair_keys('TR_LINEAR','UP','radial',True),('new_C_TR_LINEAR_UP_radial','old_C_TR_LINEAR_UP_radial'))
    def test_fresh_allowances_and_missing_variant(self):
        values={r:{'E_Spath':v} for r,v in [('base',.02),('temporal',.0201),('axial',.0202),('radial',.0203)]}
        ar={r:{'E_Spath':1e-16} for r in values}
        d=c.decision(values,ar,'TR_LINEAR','E_Spath',True)
        self.assertAlmostEqual(d['u_total'],.0006+1e-16);self.assertIn('both_C_radial',d['terms']);self.assertEqual(d['decision'],'MATERIAL_MODELED_DELIVERY_CONTRAST')
        del values['radial'];self.assertEqual(c.decision(values,ar,'TR_LINEAR','E_Spath')['decision'],'UNRESOLVED')
    def test_failure_precedes_unresolved(self):
        self.assertTrue(c.overall(['FAIL','UNRESOLVED']).endswith('INSUFFICIENT'))
        self.assertTrue(c.overall(['PASS']*23).endswith('UNRESOLVED'))
        self.assertTrue(c.overall(['PASS']*24).endswith('SUFFICIENT_FOR_TESTED_OUTPUTS'))
    def test_attempt_accounting_and_no_numerical_retry(self):
        start=dict(id='x',slot='x',status='STARTED',stage='C',scenario_sha256='s',executable_sha256='e')
        ev=[start]
        with self.assertRaises(ValueError):reserve(ev,'x','s','e')
        ev.append(dict(id='x',slot='x',status='FAILED',stage='C',failure_class='NUMERICAL',integrating=False))
        recovery=dict(category='INFRASTRUCTURE_INTERRUPTION',evidence_sha256='proof')
        with self.assertRaises(ValueError):reserve(ev,'x','s','e',recovery)
        ev[-1]['failure_class']='INFRASTRUCTURE_INTERRUPTION'
        self.assertEqual(reserve(ev,'x','s','e',recovery),'x__recovery1')
        with self.assertRaises(ValueError):reserve(ev,'x','changed','e',recovery)
        ev.extend([dict(start,id='other1',slot='other1',recovery=recovery),dict(start,id='other2',slot='other2',recovery=recovery)])
        with self.assertRaises(ValueError):reserve(ev,'x','s','e',recovery)
        with self.assertRaises(ValueError):reserve([start]*44,'new','s','e')
        with patch.object(a,'events',return_value=ev),patch.object(a,'sha',return_value='ledger'):
            count=a.accounting(Path('unused'));self.assertEqual(count['actual_native_launches'],3);self.assertEqual(count['startup_failures'],1);self.assertEqual(len(count['pending_attempts']),2)

if __name__=='__main__':unittest.main()
