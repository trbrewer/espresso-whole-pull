"""Synthetic contract tests; ordinary CI never executes the scientific matrix."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools.sci_md_rheology_003 import laws,analyze,run,evidence,export


def measured(tk,water_percent):
    if tk!=363.15 or not 76<=water_percent<=90:raise ValueError('units')
    return .00045+(.9-water_percent/100)*.001


def trace(q):
    return {k:analyze.np.array(v,float) for k,v in dict(start_s=[0,15],end_s=[15,30],dt_s=[15,15],state_s=[0,15],
        Q_m3_s=q,volume_m3=[15*x for x in q]).items()}


class Rheology003(unittest.TestCase):
    def test_basis_and_units(self):
        self.assertAlmostEqual(float(laws.fraction(965/9)),.1)
        self.assertNotAlmostEqual(float(laws.fraction(100)),.1)
        for w in (-1e-12,.24000001,10,90,.9,float('nan')):
            with self.assertRaises(ValueError):laws.evaluate('TR_EARLY',[w],.0003,measured)
        for t in (90,636.3):
            with self.assertRaises(ValueError):laws.evaluate('TR_EARLY',[.1],.0003,measured,t)
        with self.assertRaises(ValueError):laws.fraction(-1)
        with self.assertRaises(ValueError):laws.eq5(.1,363.15)
        with self.assertRaises(ValueError):laws.eq5(.1,90)
        with self.assertRaises(ValueError):laws.eq5(10,20)

    def test_water_anchors_and_shapes(self):
        for l in laws.LAWS:
            self.assertAlmostEqual(float(laws.evaluate(l,0,.0003,measured)),.0003,places=18)
            mu=laws.evaluate(l,laws.np.linspace(0,.24,24001),.0003,measured)
            self.assertTrue((mu>0).all());self.assertTrue((laws.np.diff(mu)>=-1e-18).all())
        values=[float(laws.evaluate(l,.05,.0003,measured)) for l in ('TR_DELAYED','TR_LINEAR','TR_EARLY')]
        self.assertLess(values[0],values[1]);self.assertLess(values[1],values[2])

    def test_measured_segment_and_continuity(self):
        w=laws.np.linspace(.1,.24,1401)
        ref=laws.evaluate('TR_LINEAR',w,.0003,measured)
        for law in ('TR_EARLY','TR_DELAYED'):
            self.assertTrue(laws.np.array_equal(laws.evaluate(law,w,.0003,measured),ref))
            a=laws.evaluate(law,[.1-1e-12,.1,.1+1e-12],.0003,measured)
            self.assertLess(float(max(a)-min(a)),1e-12)

    def test_eq5_raw_versus_adaptation(self):
        self.assertAlmostEqual(float(laws.eq5(0,90,extrapolate_90=True)),.0003243585489046714,places=17)
        raw=float(laws.eq5(.1,90,extrapolate_90=True))
        adapted=float(laws.evaluate(laws.LAWS[-1],.1,.0003,measured))
        self.assertNotEqual(raw,adapted)
        self.assertAlmostEqual(adapted/raw,.0003/float(laws.eq5(0,90,extrapolate_90=True)))

    def test_csv_rounding(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'eq.csv';p.write_text('omega,T_degC,mu_Pa_s\n0,0,0.00164423\n')
            self.assertEqual(export.reproduce_csv(p)['rows'],1)
            p.write_text('omega,T_degC,mu_Pa_s\n0,0,0.0164423\n')
            with self.assertRaises(ValueError):export.reproduce_csv(p)

    def test_deterministic_knots(self):
        for refined in (False,True):
            a=laws.knots([.24,.1,.16,.2,.16],refined);b=laws.knots([.2,.16,.1,.24],refined)
            self.assertTrue(laws.np.array_equal(a,b));self.assertTrue((laws.np.diff(a)>0).all())
            self.assertEqual(len(a),481 if refined else 241)

    def test_native_table_equivalence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);exe=p/'evaluate'
            subprocess.run(['c++','-std=c++11','-O2',str(evidence.ROOT/'tools/sci_md_rheology_002/evaluator.cpp'),'-o',str(exe)],check=True,capture_output=True)
            for law in laws.NEW:
                ws=laws.knots([.1,.16,.2,.24]);mus=laws.evaluate(law,ws,.0003,measured)
                table=p/'law.table';table.write_text(export.HEADER+''.join(f'{w:.17g} {m:.17g}\n' for w,m in zip(ws,mus)))
                points=laws.np.linspace(0,.24,10001);cs=965*points/(1-points)
                result=subprocess.run([str(exe),str(table)],input='\n'.join(map(str,cs)),text=True,capture_output=True,check=True)
                native=laws.np.array(list(map(float,result.stdout.split())))
                interp=laws.np.interp(cs/(965+cs),ws,mus)
                self.assertLess(float(max(abs(native/interp-1))),1e-12)
                self.assertLess(float(max(abs(interp/laws.evaluate(law,cs/(965+cs),.0003,measured)-1))),1e-4)

    def test_independent_reference_calibration(self):
        w=trace([2,2]);c=trace([1,2]);transfer=trace([100,200])
        self.assertEqual(analyze.calibrate(c,w),.75)
        transfer['Q_m3_s']*=100
        self.assertEqual(analyze.calibrate(c,w),.75)
        self.assertEqual(analyze.calibrate(trace([1,1]),w),.5)
        self.assertNotEqual(analyze.calibrate(trace([1,1]),w),analyze.calibrate(c,w))
        # Scaling hydraulics creates no transport fields.
        null=.75*w['Q_m3_s'];self.assertEqual(null.shape,(2,))
        self.assertNotIn('solute_kg',w)

    def test_interval_rejections(self):
        good=trace([1,2]);analyze.validate(good)
        for key,values in [('start_s',[1,15]),('end_s',[15,29]),('start_s',[0,14]),
                           ('start_s',[0,0]),('Q_m3_s',[0,2]),('Q_m3_s',[1,float('nan')]),
                           ('dt_s',[15,-15]),('volume_m3',[14,30]),('state_s',[1,15])]:
            bad=copy.deepcopy(good);bad[key]=analyze.np.array(values)
            with self.assertRaises(ValueError):analyze.validate(bad)
        different=trace([1,2]);different['end_s']=analyze.np.array([10,30.]);different['start_s']=analyze.np.array([0,10.])
        different['state_s']=different['start_s'];different['dt_s']=analyze.np.array([10,20.]);different['volume_m3']=analyze.np.array([10,40.])
        with self.assertRaises(ValueError):analyze.matched(good,different)
        e=analyze.errors([2,1],[1,1],[15,15]);self.assertEqual(e,dict(integrated=.5,peak=1.))

    def test_classification_truth_table(self):
        def family():return {l:dict(qualified=True,conditions={c:dict(C_N='material') for c in run.CASES}) for l in laws.LAWS}
        f=family();self.assertEqual(analyze.family_status(f),'ROBUST_ACROSS_TESTED_VISCOSITY_LAWS')
        f['TR_DELAYED']['conditions']['reversed_3bar']['C_N']='below'
        self.assertEqual(analyze.family_status(f),'SOURCE_OR_CONTINUATION_SENSITIVE')
        f['TR_EARLY']['conditions']['uniform_9bar']['C_N']='unresolved'
        self.assertEqual(analyze.family_status(f),'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED')
        f=family();f.pop('TR_LINEAR');self.assertEqual(analyze.family_status(f),'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED')
        f=family();f['TR_LINEAR']['qualified']=False;self.assertEqual(analyze.family_status(f),'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED')
        terms={m:{'total':.005} for m in ('integrated','peak')}
        for vals,want in [((.055,.01),'material'),((.044,.094),'below'),((.05,.095),'unresolved')]:
            self.assertEqual(analyze.comparison_status(dict(zip(terms,vals)),terms),want)
        self.assertEqual(analyze.comparison_status(dict(integrated=1,peak=1),terms,False),'unresolved')

    def test_missing_artifacts_and_audit_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            # Later authorized G2 source can fail the historical source check
            # before the missing-file check; either must remain fail-closed.
            with self.assertRaises((OSError,ValueError)):evidence.reuse(Path(d))
            with self.assertRaises((OSError,ValueError)):analyze.analyze(Path(d)/'runs',Path(d),Path(d)/'output')

    def test_campaign_provenance_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);doc=root/'doc';doc.mkdir()
            (doc/'FREEZE.json').write_text(json.dumps(dict(files={},executable_sha256='exe',tables={'TR_DELAYED_base':'table'})))
            ident='base_uniform_9bar_TR_DELAYED';out=root/ident;out.mkdir()
            (out/'scenario.json').write_text('{}');(out/'case').mkdir();interval=out/'case'/evidence.INTERVAL
            interval.parent.mkdir(parents=True);interval.write_text('test')
            start=dict(id=ident,status='STARTED',freeze_sha256=evidence.sha(doc/'FREEZE.json'),executable_sha256='exe',table_sha256='table')
            end=dict(id=ident,status='COMPLETE',configuration_sha256=evidence.sha(out/'scenario.json'),intervals_sha256=evidence.sha(interval),logs_sha256={},input_hashes={})
            def save(a,b):(root/'INVOCATIONS.jsonl').write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
            with patch.object(analyze,'DOC',doc):
                save(start,end);self.assertEqual(len(analyze.validate_campaign(root)[1]),1)
                for key in ('freeze_sha256','executable_sha256','table_sha256'):
                    bad=dict(start);bad[key]='wrong';save(bad,end)
                    with self.assertRaises(ValueError):analyze.validate_campaign(root)
                save(start,end);(out/'scenario.json').write_text('tamper')
                with self.assertRaises(ValueError):analyze.validate_campaign(root)

    def test_partial_preserves_completed_branch(self):
        ident='base_uniform_9bar_TR_DELAYED'
        with patch.object(analyze,'reuse'),patch.object(analyze,'validate_campaign',return_value=([],[{'id':ident}])), \
             patch.object(analyze,'rows',return_value=trace([1,2])),patch.object(analyze,'gates',return_value={'numerical_state_pass':True}), \
             patch.object(analyze,'secondary',return_value={'solute_kg':.001}):
            r=analyze.partial_report(Path('new'),Path('old'))
            self.assertEqual(r['classification'],'SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED')
            self.assertIn(ident,r['completed']);self.assertEqual(r['completed'][ident]['C_N']['integrated'],0.)
            self.assertEqual(len(r['unavailable']),23)

    def test_failed_attempt_preserved_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def fail(p):p.mkdir();(p/'failed.txt').write_text('preserved');raise RuntimeError('synthetic failure')
            with self.assertRaises(RuntimeError):run.invoke(root,'a',1,{'a','b'},{},fail)
            content=(root/'INVOCATIONS.jsonl').read_text()
            self.assertEqual([json.loads(s)['status'] for s in content.splitlines()],['STARTED','FAILED'])
            for ident in ('a','b'):
                with self.assertRaises(ValueError):run.invoke(root,ident,1,{'a','b'},{},fail)
            self.assertEqual((root/'INVOCATIONS.jsonl').read_text(),content)
            self.assertEqual((root/'a/failed.txt').read_text(),'preserved')
        self.assertEqual(len(run.matrix()),24);self.assertEqual(len(run.matrix(True)),4)

if __name__=='__main__':unittest.main()
