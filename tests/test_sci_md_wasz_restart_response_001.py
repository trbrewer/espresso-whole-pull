"""Scientific observer failure modes; synthetic cases are not empirical evidence."""
import csv
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("restart_observer", ROOT / "tools/sci_md_wasz_restart_response_001/analyze.py")
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
BUNDLE = ROOT / "docs/analysis/sci_md_wasz_restart_response_001"


def rows(times, mass=None, pressure=None):
    return [dict(t=t, m=(mass[i] if mass is not None else t/1000),
                 p2=(pressure[i] if pressure is not None else 800)) for i,t in enumerate(times)]


def synthetic_episode(data, name="E0"):
    return dict(episode_id=name, first_index=0, last_index=len(data)-1,
                start_s=data[0]['t']/1000, end_s=data[-1]['t']/1000, state="ACTIVE")


class RestartObserverTests(unittest.TestCase):
    def test_units_and_original_clock(self):
        data=rows([10126,10219,10314], [21,21.186,21.376], [810,820,800])
        obs=A.Observer(data)
        interval=obs.interval('test',synthetic_episode(data),'later',10.126,10.314,'TEST')
        self.assertTrue(interval['supported'])
        self.assertAlmostEqual(interval['rate_g_s'],2)
        self.assertEqual(interval['mass_start']['left_time_ms'],10126)
        self.assertEqual(interval['mass_end']['right_index'],2)
        self.assertEqual(interval['pressure']['original_support'][0]['pressure_bar'],8.1)

    def test_pressure_only_segmentation_and_transition_brackets(self):
        data=rows([0,93,187,280,375,468],[0,2,-20,500,0,-500],[300,550,551,800,550,300])
        baseline=A.segment(data)
        for r in data:r['m']=float('nan')
        self.assertEqual(A.segment(data),baseline)
        self.assertEqual([r['state'] for r in baseline],['LOW','ACTIVE','LOW'])
        active=baseline[1]
        self.assertEqual((active['first_index'],active['last_index']),(2,3))
        self.assertEqual([v['original_index'] for v in active['entering_bracket']],[1,2])
        self.assertEqual([v['original_index'] for v in active['exiting_bracket']],[3,4])

    def test_exact_and_bracketed_endpoints(self):
        obs=A.Observer(rows([0,93,188],[0,1,3]))
        exact=obs.endpoint(.093,'m')
        bracket=obs.endpoint(.1405,'m')
        self.assertTrue(exact['exact_sample'])
        self.assertEqual(exact['bracket_width_s'],0)
        self.assertEqual((bracket['left_index'],bracket['right_index']),(1,2))
        self.assertAlmostEqual(bracket['interpolation_fraction'],.5)
        self.assertAlmostEqual(bracket['value'],2)

    def test_known_increment_on_irregular_times(self):
        data=rows([0,93,188,282,375])
        for r in data:r['m']=7+3*r['t']/1000
        it=A.Observer(data).interval('known',synthetic_episode(data),'later',.04,.32,'TEST')
        self.assertTrue(it['supported'])
        self.assertAlmostEqual(it['rate_g_s'],3)
        self.assertAlmostEqual(it['mass_change_g'],.84)

    def test_no_extrapolation_or_holding(self):
        obs=A.Observer(rows([0,93,188]))
        for t in [-.001,.189]:
            with self.assertRaises(A.Unsupported):obs.endpoint(t,'m')

    def test_gap_and_documented_discontinuity_not_bridged(self):
        data=rows([0,93,280,375])
        with self.assertRaisesRegex(A.Unsupported,'GAP'):A.Observer(data).endpoint(.2,'m')
        continuous=rows([0,93,188,282])
        with self.assertRaisesRegex(A.Unsupported,'DISCONTINUITY'):
            A.Observer(continuous,blocked_edges=[1]).support(0,.282,'m')

    def test_missing_mass_and_parse_record_not_dropped(self):
        data=rows([0,93,188,282]);data[1].pop('m')
        with self.assertRaises(A.Unsupported):A.Observer(data).support(0,.282,'m')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input.txt';p.write_text('{"t":0,"m":1,"p2":800}\ninvalid\n{"t":188,"m":2,"p2":800}\n')
            parsed=A.parse(p)
            self.assertEqual(len(parsed),3)
            self.assertEqual(parsed[1]['original_index'],1)
            with self.assertRaises(A.Unsupported):A.Observer(parsed).endpoint(.1,'m')

    def test_invalid_clock_and_nonfinite_values(self):
        for ts in ([0,93,93],[0,93,90]):
            with self.assertRaises(A.Unsupported):A.Observer(rows(ts)).endpoint(.05,'m')
        for field in ['t','m','p2']:
            data=rows([0,93,188]);data[1][field]=float('nan')
            it=A.Observer(data).interval('bad',synthetic_episode(data),'later',0,.188,'TEST')
            self.assertFalse(it['supported'])
            self.assertIsNotNone(it['unavailable_reason'])
            self.assertIsNone(it['rate_g_s'])

    def test_negative_mass_preserved(self):
        data=rows([0,93,188],[3,2,1])
        it=A.Observer(data).interval('negative',synthetic_episode(data),'later',0,.188,'TEST')
        self.assertEqual(it['mass_change_g'],-2)
        self.assertLess(it['rate_g_s'],0)

    def test_transition_bracket_not_used_to_recover_window(self):
        data=rows([0,93,188,282],[0,1,2,3],[300,800,800,300])
        ep=A.segment(data)[1]
        it=A.Observer(data).interval('cross',ep,'early',.05,.15,'TEST')
        self.assertFalse(it['supported'])
        self.assertEqual(it['unavailable_reason'],'ENDPOINT_BRACKET_CROSSES_STATE_TRANSITION')

    def test_fixed_designs_and_nonoverlap_eligibility(self):
        data=rows(list(range(0,20001,50)))
        episodes=[dict(episode_id='E0',first_index=0,last_index=200,start_s=0,end_s=10,state='ACTIVE'),
                  dict(episode_id='E1',first_index=200,last_index=360,start_s=10,end_s=18,state='ACTIVE')]
        intervals,elig=A.windows(A.Observer(data),episodes)
        self.assertEqual(A.DESIGNS, (('PRIMARY',2,2),('SENSITIVITY_A',3,2),('SENSITIVITY_B',2,3)))
        self.assertEqual([e['eligible'] for e in elig],[True,False,False])
        self.assertEqual([e['unavailable_reason'] for e in elig],[None,'EARLY_LATER_OVERLAP','EARLY_LATER_OVERLAP'])
        comparisons=A.contrasts(intervals,elig)
        missing=[c for c in comparisons if c['design']=='SENSITIVITY_A' and c['episode_id']=='E1']
        self.assertEqual(len(missing),4)
        self.assertTrue(all(not c['supported'] and c['difference_g_s'] is None for c in missing))

    def test_published_semantics_and_startup(self):
        data=rows([0,93,187,282,375,470,563,657],[0,1,2,4,7,11,16,22])
        means,derivative,check=A.lineage(data)
        self.assertEqual(means[:4],[None]*4)
        self.assertEqual(derivative[:5],[None]*5)
        self.assertAlmostEqual(derivative[5],(11-0)/(5*.095))
        self.assertNotAlmostEqual(derivative[5],11/.470)
        self.assertLess(check['max_formula_difference_g_s'],1e-12)
        data[3]['m']=None
        self.assertTrue(all(v is None for v in A.lineage(data)[1]))

    def test_pressure_equal_mean_different_trajectory(self):
        data1=rows([0,1000,2000],pressure=[700,900,700])
        data2=rows([0,1000,2000],pressure=[800,800,800])
        one=A.Observer(data1,max_gap_ms=1000).interval('one',synthetic_episode(data1),'later',0,2,'TEST')
        two=A.Observer(data2,max_gap_ms=1000).interval('two',synthetic_episode(data2),'later',0,2,'TEST')
        p=A.pressure_difference(one,two)
        self.assertEqual(p['mean_difference_bar'],0)
        self.assertAlmostEqual(p['rms_mismatch_bar'],math.sqrt(1/3))
        self.assertEqual(p['max_absolute_mismatch_bar'],1)

    def test_pressure_time_weighting_on_irregular_samples(self):
        data=rows([0,500,2000],pressure=[700,900,900])
        it=A.Observer(data,max_gap_ms=1500).interval('test',synthetic_episode(data),'later',0,2,'TEST')
        self.assertEqual(it['pressure']['time_weighted_mean_bar'],8.75)
        self.assertNotEqual(it['pressure']['time_weighted_mean_bar'],25/3)

    def test_contrast_signs_and_e1_duplication(self):
        def interval(rate,ep,kind):
            data=rows([0,1000,2000],[0,rate,2*rate])
            it=A.Observer(data,max_gap_ms=1000).interval(ep+kind,synthetic_episode(data,ep),kind,0,2,'TEST')
            return it
        base,early,later=interval(2,'E0','later'),interval(4,'E1','early'),interval(3,'E1','later')
        for k,left,right,value in [('A',later,base,1),('B',later,base,1),('C',later,early,-1),('D',early,base,2)]:
            c=A.contrast(k,left,right)
            self.assertEqual(c['difference_g_s'],value)
            self.assertEqual(c['physical_puck_id'],A.PUCK)
            self.assertEqual(c['duplicates_kind'],'A' if k=='B' else None)

    def test_transient_only_and_sustained_synthetic_observer(self):
        for late_rate in [1,3]:
            data=rows(list(range(0,10001,50)))
            for r in data:
                t=r['t']/1000
                r['m']=4*min(t,4)+late_rate*max(0,t-4)
            obs=A.Observer(data);ep=synthetic_episode(data)
            early=obs.interval('early',ep,'early',2,4,'TEST')
            later=obs.interval('later',ep,'later',6,8,'TEST')
            self.assertAlmostEqual(early['rate_g_s'],4)
            self.assertAlmostEqual(later['rate_g_s'],late_rate)

    def test_retained_one_puck_support_and_tables(self):
        r=json.loads((BUNDLE/'RESULT.json').read_text())
        self.assertEqual(r['physical_puck_count'],1)
        self.assertEqual(r['common_supported_restart_subset'],['E1','E2','E3','E4','E5'])
        self.assertEqual(len(r['episodes']),13)
        self.assertEqual(len(r['intervals']),46)
        self.assertEqual(len(r['contrasts']),66)
        for key,name in [('episodes','EPISODES.csv'),('intervals','INTERVALS.csv'),('contrasts','CONTRASTS.csv')]:
            self.assertEqual({v['physical_puck_id'] for v in r[key]},{A.PUCK})
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/name;A.csv_write(path,r[key])
                self.assertEqual(path.read_bytes(),(BUNDLE/name).read_bytes())
        primary=[v for v in r['contrasts'] if v['design']=='PRIMARY' and v['kind']=='A']
        self.assertAlmostEqual(primary[0]['difference_g_s'],1.4091885272248987)
        self.assertAlmostEqual(primary[-1]['difference_g_s'],2.481660519723306)

    def test_plan_source_and_implementation_hash_bindings(self):
        m=json.loads((BUNDLE/'SOURCE_MANIFEST.json').read_text())
        self.assertEqual(m['plan_sha256'],A.sha256(BUNDLE/'PLAN.md'))
        self.assertEqual(m['implementation_sha256'],A.sha256(Path(A.__file__)))
        self.assertTrue(m['original_source']['authenticated'])
        self.assertEqual(m['original_source']['revision'],A.REVISION)
        self.assertEqual(m['production_puckworks_lock'],A.PRODUCTION)
        for path,(blob,sha) in A.EXPECTED.items():
            self.assertEqual(m['original_source']['files'][path]['git_blob_id'],blob)
            self.assertEqual(m['original_source']['files'][path]['sha256'],sha)

    def test_deterministic_synthetic_outputs_and_no_nan(self):
        data=rows(list(range(0,20001,50)))
        ep=[synthetic_episode(data)]
        outputs=[]
        for _ in range(2):
            intervals,elig=A.windows(A.Observer(data),ep)
            outputs.append(json.dumps(dict(intervals=intervals,contrasts=A.contrasts(intervals,elig)),sort_keys=True,allow_nan=False))
        self.assertEqual(*outputs)


if __name__=='__main__':
    unittest.main()
