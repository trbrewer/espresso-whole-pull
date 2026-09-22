"""Focused synthetic qualification of the autonomous composition and decisions."""
import copy,unittest
import numpy as np
from tools.sci_md_rheology_007.common import BUDGETS,matrix,constituent,radial
from tools.sci_md_rheology_007.observer import adapt,compose,history,metrics,decide,verdict,clocks,accounting
from tools.sci_md_rheology_004.observer import at,compare
from tools.sci_md_rheology_007.arithmetic import audit
from tools.sci_md_rheology_007.analyze import support

def fixture(q=1e-7):
    n=3;dt=np.full(n,10.);water=np.cumsum(965*q*dt);solute=np.cumsum(np.array([1.,2.,1.])*1e-5)
    z=np.zeros(n)
    d=dict(start_s=np.arange(n)*10.,end_s=np.arange(1,n+1)*10.,dt_s=dt,state_s=np.arange(n)*10.,Q_m3_s=np.full(n,q),volume_m3=q*dt,water_kg=water,solute_kg=solute,stored_solute_kg=z,remaining_kg=.0056-solute,inlet_loss_kg=z,correction_kg=z,water_balance_kg=z,solute_balance_kg=z)
    for k in ('c_n_min','c_n_max','c_next_min','c_next_max'):d[k]=z.copy()
    for k in ('mu_min','mu_max','mu_next_min','mu_next_max'):d[k]=np.full(n,.001)
    return d

class TestParallelPaths(unittest.TestCase):
    def path(self,q=1e-7):return adapt(fixture(q),'uniform')
    def test_matrix(self):self.assertEqual(len(matrix()),28)
    def test_physical_changes(self):
        s=radial();p=constituent(s,'inner');self.assertEqual(p['coffee_bed'],s['coffee_bed']);self.assertEqual(p['liquid'],s['liquid']);self.assertEqual(p['hydraulics']['saturated_permeability_m2'],3e-15)
    def test_area_fixture(self):
        p=constituent(radial(),'inner',.25,True);self.assertAlmostEqual(p['coffee_bed']['dry_dose_kg'],.005);self.assertAlmostEqual(p['geometry']['basket_radius_m'],.0145);self.assertEqual(p['coffee_bed']['bed_depth_m'],radial()['coffee_bed']['bed_depth_m'])
    def test_exact_once_inventory(self):
        p=compose(self.path(),self.path());self.assertEqual(p['dose_kg'],.020);self.assertEqual(p['initial_inventory_kg'],.0056);self.assertAlmostEqual(p['regions'][0]['remaining_kg'][0]+p['regions'][0]['solute_kg'][0],.0014)
    def test_equal_paths(self):
        a=self.path();p=compose(a,a)
        for k in ('Q','water_kg','solute_kg','remaining_kg'):np.testing.assert_allclose(p[k],a[k],rtol=1e-15)
    def test_permutation(self):
        a,b=self.path(),self.path(2e-7);p=compose(a,b);r=compose(b,a,(.75,.25));np.testing.assert_array_equal(p['Q'],r['Q']);np.testing.assert_allclose(p['share'],1-r['share'])
    def test_analytical_constant_viscosity(self):
        area=np.pi*.029**2;L=.009011660896432553;mu=.00031267394194924405
        qi=area*3e-15*9e5/(L*mu);qo=area*7.5e-16*9e5/(L*mu)
        p=compose(self.path(qi),self.path(qo));np.testing.assert_allclose(p['share'],4/7,rtol=1e-15);np.testing.assert_allclose(p['Q'],area*(.25*3e-15+.75*7.5e-16)*9e5/(L*mu),rtol=1e-15)
    def test_mixing_not_tds_average(self):
        a=self.path();b=self.path(3e-7);b['solute_kg']*=2;b['remaining_kg']=.0056-b['solute_kg'];p=compose(a,b);h=history(p)
        tds=100*h['S'][-1]/h['B'][-1];avg=sum(w*100*d['solute_kg'][-1]/(d['water_kg'][-1]+d['solute_kg'][-1]) for w,d in zip((.25,.75),(a,b)))
        self.assertNotAlmostEqual(tds,avg);self.assertNotIn('mu_min',p)
    def test_first_fraction_conservative(self):
        h=history(self.path());x=h['B'][1]/2;v=at(h,'B',[0,x]);self.assertAlmostEqual(v['S'][1],h['S'][1]/2);self.assertAlmostEqual(v['W'][1],h['W'][1]/2);self.assertAlmostEqual(v['t'][1],5.)
    def test_fraction_closure(self):
        h=history(self.path());v=at(h,'B',np.linspace(0,h['B'][-1],6));self.assertAlmostEqual(sum(np.diff(v['S'])),h['S'][-1]);np.testing.assert_allclose(v['W']+v['S'],v['B'])
    def test_clock_rejected(self):
        a,b=self.path(),self.path();b['start_s'][1]+=1e-13
        with self.assertRaises(ValueError):compose(a,b)
    def test_missing(self):
        d=fixture();del d['start_s']
        with self.assertRaises(ValueError):adapt(d,'uniform')
    def test_duplicate_gap_overlap(self):
        for shift in (-10,1,10):
            d=fixture();d['start_s'][1]+=shift
            with self.assertRaises(ValueError):adapt(d,'uniform')
    def test_nonfinite_zero_negative_flow(self):
        for q in (0,-1e-7,np.nan,np.inf):
            with self.assertRaises(ValueError):adapt(fixture(q),'uniform')
    def test_negative_increment(self):
        d=fixture();d['solute_kg'][1]=-1e-5
        with self.assertRaises(ValueError):adapt(d,'uniform')
    def test_double_scaling(self):
        a=self.path();a['dose_kg']*=.25
        with self.assertRaises(ValueError):compose(a,self.path())
    def test_bad_weights(self):
        for w in ((.25,.25),(-1,2),(0,1)):
            with self.assertRaises(ValueError):compose(self.path(),self.path(),w)
    def test_constituent_balance_cannot_cancel(self):
        d=fixture();d['remaining_kg']+=1e-4
        with self.assertRaises(ValueError):adapt(d,'uniform')
    def test_boundary_decisions(self):
        self.assertEqual(decide(.5,.1,1),'PASS');self.assertEqual(decide(2,.1,1),'FAIL');self.assertEqual(decide(1,0,1),'UNRESOLVED');self.assertEqual(decide(2,.21,1),'UNRESOLVED');self.assertEqual(decide(2,0,1,False),'UNRESOLVED')
    def test_partial_verdict(self):
        self.assertEqual(verdict(['FAIL','UNRESOLVED'],False),'INSUFFICIENT');self.assertEqual(verdict(['PASS'],False),'UNRESOLVED');self.assertEqual(verdict([]),'UNRESOLVED')
    def test_reference_denominator_and_decimal(self):
        a,b=self.path(),self.path(2e-7);p=compose(a,b);c=self.path(1.2e-7);c['share']=np.full(3,.6);end=min(history(p)['B'][-1],history(c)['B'][-1])
        m=metrics(p,c,end);h=audit(a,b,c,end)
        for k in BUDGETS:self.assertAlmostEqual(m[k],h[k],places=12)
        obs=compare(history(p),history(c),'B',end);self.assertEqual(m['E_Spath'],obs['E_path']);self.assertEqual(m['delivery']['P'],obs['C'])
    def test_missing_support(self):self.assertFalse(support({}, {})['3']['adequate'])
    def test_support_common_all_laws(self):
        c={};p={}
        from tools.sci_md_rheology_007.common import LAWS,sets
        for l in LAWS:
            for r in sets(l)+('radial',):c[f'{l}_3bar_{r}']=self.path()
            for r in sets(l):p[f'{l}_3bar_{r}']=self.path(.94e-7)
        s=support(c,p)['3'];self.assertTrue(s['complete']);self.assertFalse(s['adequate']);self.assertLess(s['coverage'],.95)
if __name__=='__main__':unittest.main()
