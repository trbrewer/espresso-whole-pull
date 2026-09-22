"""Focused scientific tests for native communicating radial reductions."""
import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tests.test_sci_md_rheology_007 import fixture
from tools.sci_md_rheology_007.observer import adapt, compose, history, decide, verdict
from tools.sci_md_rheology_004.observer import at
from tools.sci_md_rheology_008.common import matrix, candidate, radial, BUDGETS
from tools.sci_md_rheology_008.geometry import annular_volumes
from tools.sci_md_rheology_008.observer import native, metrics, qualify_metric
from tools.sci_md_rheology_008.arithmetic import audit
from tools.sci_md_rheology_008.run import next_attempt
from tools.sci_md_rheology_008.analyze import selection

def raw(q=1e-7):
    d=fixture(q);z=np.zeros(3)
    d.update(schema_version=np.ones(3),Q_total_m3_s=d.pop('Q_m3_s'),Q_inner_m3_s=np.full(3,q*4/7),Q_outer_m3_s=np.full(3,q*3/7),cup_Q_m3_s=np.full(3,q),reverse_inner_m3_s=z.copy(),reverse_outer_m3_s=z.copy(),reverse_total_m3_s=z.copy(),dilute_pore_volume_fraction=z.copy(),pore_courant_outgoing_max=z.copy())
    for old,new in [('c_n_min','c_n_min_kg_m3'),('c_n_max','c_n_max_kg_m3'),('c_next_min','c_next_min_kg_m3'),('c_next_max','c_next_max_kg_m3'),('mu_min','mu_n_min_Pa_s'),('mu_max','mu_n_max_Pa_s'),('mu_next_min','mu_next_min_Pa_s'),('mu_next_max','mu_next_max_Pa_s')]:d[new]=d.pop(old)
    for zone,f in [('inner',.25),('outer',.75)]:
        d[zone+'_area_m2']=np.full(3,np.pi*.029**2*f);d[zone+'_volume_m3']=d[zone+'_area_m2']*.009011660896432553;d[zone+'_remaining_kg']=f*d['remaining_kg']
    return d

class TestCommunicatingRadial(unittest.TestCase):
    def test_matrix(self):
        m=matrix();self.assertEqual(len(m),42)
        self.assertEqual(sum(v[1]=='TR_LINEAR' for v in m.values()),18)
        self.assertEqual(sum(v[3]=='property' for v in m.values()),6)
    def test_only_declared_changes(self):
        s=radial();e=candidate(s,4);self.assertEqual(s['hydraulics'],e['hydraulics']);self.assertEqual(s['coffee_bed'],e['coffee_bed'])
        with self.assertRaises(ValueError):candidate(s,16)
    def test_annular_volume(self):
        for n in (2,4,8):
            v=annular_volumes(n);self.assertTrue(np.all(v>0));self.assertAlmostEqual(sum(v[:n//2])/sum(v),.25);self.assertAlmostEqual(v[-1]/v[0],2*n-1)
    def test_native_not_weighted(self):
        r=raw();d=native(r);np.testing.assert_array_equal(d['Q'],r['Q_total_m3_s']);np.testing.assert_array_equal(d['water_kg'],r['water_kg'])
        with self.assertRaises(ValueError):compose(d,d)
    def test_native_inventory(self):
        d=native(raw());self.assertEqual(d['initial_inventory_kg'],.0056);self.assertAlmostEqual(d['dose_kg'],.020,places=15)
    def test_nonfinite_negative_inventory(self):
        for key,value in [('Q_total_m3_s',-1),('Q_inner_m3_s',float('nan')),('remaining_kg',.006),('stored_solute_kg',-1e-5),('inner_remaining_kg',.002)]:
            r=raw();r[key][0]=value
            with self.assertRaises(ValueError):native(r)
    def test_exact_clocks(self):
        a=native(raw());b=copy.deepcopy(a);b['state_s'][0]=1e-13
        with self.assertRaises(ValueError):metrics(a,b,.001)
        with self.assertRaises(ValueError):audit(a,b,.001)
    def test_first_interval_fraction(self):
        h=history(native(raw()));x=h['B'][1]/2
        self.assertAlmostEqual(at(h,'B',[x])['S'][0],h['S'][1]/2)
        v=at(h,'B',np.linspace(0,h['B'][-1],6));self.assertAlmostEqual(sum(np.diff(v['S'])),h['S'][-1])
    def test_fixed_support(self):
        a=native(raw());b=native(raw(2e-7));end=history(b)['B'][-1];m=metrics(a,b,end)
        self.assertIsNone(m['E_Spath']);self.assertIsNotNone(m['E_Qint']);self.assertNotIn('E_Spath',audit(a,b,end))
    def test_support_roundoff_does_not_discard_hydraulics(self):
        a=native(raw());end=history(a)['B'][-1]+5e-15
        m=metrics(a,a,end)
        self.assertEqual(m['E_Qint'],0)
        self.assertEqual(m['D_share_peak_pp'],0)
        self.assertIsNone(m['E_Spath'])
    def test_decimal_nontrivial(self):
        a=native(raw());b=native(raw(1.002e-7));a['Q_inner_native']*=.99;a['share']*=.99
        a['solute_kg']*=.95;end=min(history(a)['B'][-1],history(b)['B'][-1]);m=metrics(a,b,end);d=audit(a,b,end)
        for k in BUDGETS:self.assertAlmostEqual(m[k],d[k],places=12)
    def test_decimal_recomputes_shares(self):
        a=native(raw());b=native(raw());a['share']*=0
        self.assertEqual(audit(a,b,.001)['D_share_peak_pp'],0)
        self.assertGreater(metrics(a,b,.001)['D_share_peak_pp'],50)
    def test_boundary(self):
        for b in BUDGETS.values():
            self.assertEqual(decide(b,0,b),'UNRESOLVED');self.assertEqual(decide(b*.9,b*.1,b),'UNRESOLVED')
            self.assertEqual(decide(0,b*.200001,b),'UNRESOLVED');self.assertEqual(decide(0,0,b),'PASS');self.assertEqual(decide(b*2,0,b),'FAIL')
    def test_failure_precedence(self):
        self.assertEqual(verdict(['UNRESOLVED','FAIL']),'INSUFFICIENT')
    def test_no_intercandidate_allowance(self):
        v={r:{m:0. for m in BUDGETS} for r in ('base','temporal','axial','radial')};v['E8']={m:10 for m in BUDGETS}
        a={r:{m:0. for m in BUDGETS} for r in v};q=qualify_metric(v,a,'TR_LINEAR','E_Qint')
        self.assertEqual(q['u_total'],0);self.assertEqual(set(q['terms']),{'time','axial','Cradial','property','arithmetic'})
    def test_missing_allowance(self):
        self.assertEqual(qualify_metric({}, {}, 'TR_LINEAR','E_Qint')['decision'],'UNRESOLVED')
    def test_resume_accounting(self):
        s=dict(id='x',slot='x',status='STARTED',recovery_reason=None)
        with self.assertRaises(ValueError):next_attempt([s],'x','retry',46,4)
        f=dict(id='x',slot='x',status='FAILED');self.assertEqual(next_attempt([s,f],'x','I/O recovery',46,4),'x__recovery1')
        with self.assertRaises(ValueError):next_attempt([s,f],'x',None,46,4)
        with self.assertRaises(ValueError):next_attempt([s]*46,'y',None,46,4)
    def test_recovery_budget(self):
        events=[dict(id=str(i),slot=str(i),status='STARTED',recovery_reason='I/O') for i in range(4)]+[dict(id='0',slot='0',status='FAILED')]
        with self.assertRaises(ValueError):next_attempt(events,'0','I/O',46,4)
    def test_selection_with_lower_unresolved(self):
        d={f'E{n}':{'disposition':v} for n,v in [(2,'UNRESOLVED'),(4,'SUFFICIENT_FOR_TESTED_OUTPUTS'),(8,'INSUFFICIENT')]}
        s=selection(d);self.assertEqual(s['N'],4);self.assertEqual(s['lower_unresolved'],[2])
if __name__=='__main__':unittest.main()
