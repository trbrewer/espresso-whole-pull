"""Small analytic and fail-closed tests; no native scientific execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.sci_md_rheology_004 import observer as o,evidence as e
from tools.sci_md_rheology_003.run import invoke
from tools.sci_md_rheology_003.analyze import calibrate


def trace(solute=(.1,.2),water=(1.,2.)):
    n=len(water);dt=30/n
    d=dict(start_s=[i*dt for i in range(n)],end_s=[(i+1)*dt for i in range(n)],
           dt_s=[dt]*n,state_s=[i*dt for i in range(n)],water_kg=water,solute_kg=solute)
    d['Q_m3_s']=[x/965/dt for x in o.np.diff([0,*water])]
    d['volume_m3']=[q*dt for q in d['Q_m3_s']]
    return {k:o.np.asarray(v,float) for k,v in d.items()}


class Rheology004(unittest.TestCase):
    def test_identity_constant_concentration(self):
        h=o.history(trace());m=o.compare(h,h,'B',1.37)
        self.assertLess(m['E_path'],1e-14)
        for x in m['C']['TDS_percent']:self.assertAlmostEqual(x,100/11)
        self.assertIsNone(m['C']['cumulative_TDS_percent'][0])
        self.assertEqual(m['C']['solute_g'][0],0)

    def test_stretched_identical_mass_curve(self):
        h=o.history(trace());n=copy.deepcopy(h);n['t']*=2
        m=o.compare(h,n,'B',1.3)
        self.assertAlmostEqual(m['E_path'],0);self.assertAlmostEqual(m['time_ratio'],.5)

    def test_within_first_last_and_recombination(self):
        h=o.history(trace((.1,.4)));b=o.at(h,'B',[0,.55,1.1,1.75,2.4])
        self.assertAlmostEqual(b['S'][1],.05);self.assertAlmostEqual(b['t'][1],7.5)
        self.assertAlmostEqual(b['S'][3],.25);self.assertAlmostEqual(b['t'][-1],30)
        for k in ('W','S','B'):self.assertAlmostEqual(sum(o.np.diff(b[k])),h[k][-1])
        self.assertTrue(o.np.allclose(b['W']+b['S'],b['B'],rtol=0,atol=1e-14))
        self.assertAlmostEqual(o.at(h,'W',[.5])['S'][0],.05)

    def test_crossing_and_union_extremum(self):
        c=dict(B=o.np.array([0,1,2,3.]),S=o.np.array([0,.2,.2,.4]),t=o.np.array([0,10,20,30.]))
        n=dict(B=o.np.array([0,.5,1.5,3.]),S=o.np.array([0,.05,.25,.4]),t=o.np.array([0,5,15,30.]))
        for h in (c,n):h['W']=h['B']-h['S']
        m=o.compare(c,n,'B',3)
        self.assertAlmostEqual(m['E_end'],0);self.assertGreater(m['E_path'],.1)
        self.assertEqual(m,o.compare(c,n,'B',3))
        x=o.np.unique(o.np.r_[c['B'],n['B']]);signed=o.at(c,'B',x)['S']-o.at(n,'B',x)['S']
        self.assertGreater(max(signed),0);self.assertLess(min(signed),0)

    def test_invalid_histories(self):
        for key,value in [('water_kg',[1,.9]),('solute_kg',[.1,.09]),('solute_kg',[-.1,.2]),
                          ('end_s',[15,float('nan')]),('start_s',[0,16]),('dt_s',[0,15]),
                          ('water_kg',[1,3]),('Q_m3_s',[0,0])]:
            d=trace();d[key]=o.np.array(value)
            with self.assertRaises(ValueError):o.history(d)
        d=trace();del d['water_kg']
        with self.assertRaises(ValueError):o.history(d)
        d=trace();d['solute_kg']=o.np.array([.1])
        with self.assertRaises(ValueError):o.history(d)
        d={k:o.np.array([]) for k in trace()}
        with self.assertRaises(ValueError):o.history(d)

    def test_zero_and_unsupported_endpoints(self):
        h=o.history(trace());z=o.history(trace((0,0)))
        for x in (-1,0,2.3,float('nan')):
            with self.assertRaises(ValueError):o.compare(h,h,'B',x)
        with self.assertRaises(ValueError):o.compare(z,z,'W',1)
        with self.assertRaises(ValueError):o.at(h,'B',[-1])

    def test_common_support_all_refinements(self):
        hs=[o.history(trace(water=(.5*x,x))) for x in (2,1.9,1.8,1.7)]
        self.assertAlmostEqual(o.common_support(hs)['W'],1.7)
        self.assertAlmostEqual(o.common_support(hs)['B'],1.9)
        with self.assertRaises(ValueError):o.common_support([])

    def test_thresholds(self):
        self.assertEqual(o.decide(.06,.005,'E_path'),'MATERIAL')
        self.assertEqual(o.decide(.044,.005,'E_path'),'BELOW THRESHOLDS')
        for value,u in ((.049,.002),(.2,.006),(float('nan'),0)):
            self.assertEqual(o.decide(value,u,'E_path'),'UNRESOLVED')
        self.assertEqual(o.decide(.5,.051,'max_fraction_TDS_pp'),'UNRESOLVED')
        self.assertEqual(o.disposition(['MATERIAL','BELOW THRESHOLDS']),'LAW_OR_SCENARIO_DEPENDENT')
        self.assertEqual(o.disposition(['MATERIAL'],False),'PARTIALLY_QUALIFIED_OR_UNRESOLVED')

    def test_reference_only_calibration(self):
        c,w=trace(),trace();c['volume_m3']*=.8;c['Q_m3_s']*=.8
        a=calibrate(c,w)
        c['solute_kg']*=100;w['solute_kg']*=200
        self.assertEqual(calibrate(c,w),a)
        with self.assertRaises(TypeError):calibrate(c,w,trace())

    def test_run_matrix_failed_attempt_duplicate(self):
        self.assertEqual(len(e.matrix()),8)
        self.assertEqual(set(e.matrix()),{f'{s}_{c}_N' for s in e.SETS for c in ('uniform_9bar','reversed_3bar')})
        with tempfile.TemporaryDirectory() as root:
            for ident in e.matrix():
                with self.assertRaises(RuntimeError):invoke(root,ident,8,set(e.matrix()),{},lambda d:(_ for _ in ()).throw(RuntimeError('fixture failure')))
            events=[json.loads(x) for x in (Path(root)/'INVOCATIONS.jsonl').read_text().splitlines()]
            self.assertEqual(sum(x['status']=='STARTED' for x in events),8)
            self.assertEqual(sum(x['status']=='FAILED' for x in events),8)
            for ident in (e.matrix()[0],'base_uniform_9bar_C'):
                with self.assertRaises(ValueError):invoke(root,ident,8,set(e.matrix()),{},lambda d:None)

    def test_reject_scaled_chemistry_record(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);p.joinpath('INVOCATIONS.jsonl').write_text(json.dumps(dict(id=e.matrix()[0],status='STARTED',freeze_sha256='x',executable_sha256='e',table_sha256='t',alpha=.8,transport='SCALED_W'))+'\n')
            f=dict(executable_sha256='e',tables={'SW_WATER_ANCHORED_90C_base':'t'},alpha={'SW_WATER_ANCHORED_90C':{'base':.8}})
            with patch.object(e,'check',return_value=f),patch.object(e,'sha',return_value='x'):
                with self.assertRaises(ValueError):e.completed(p)

    def test_source_executable_mismatch(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);p.joinpath('FREEZE.json').write_text(json.dumps(dict(files={'missing':'wrong'},executable_sha256='expected')))
            with patch.object(e,'DOC',p),patch.object(e,'sha',return_value='actual'):
                with self.assertRaises(ValueError):e.check('binary')
            p.joinpath('FREEZE.json').write_text(json.dumps(dict(files={},executable_sha256='expected')))
            with patch.object(e,'DOC',p),patch.object(e,'sha',return_value='actual'):
                with self.assertRaises(ValueError):e.check('binary')

if __name__=='__main__':unittest.main()
