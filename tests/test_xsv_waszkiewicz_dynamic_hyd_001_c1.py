import csv, hashlib, importlib.util, json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/analysis/xsv_waszkiewicz_dynamic_hyd_001'
P=ROOT/'analysis/xsv_waszkiewicz_dynamic_hyd_001/core.py'
spec=importlib.util.spec_from_file_location('xsv_c1_core',P);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def rows(name):
    with (DOC/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

class TestWaszkiewiczC1(unittest.TestCase):
    def test_original_authority_preserved(self):
        self.assertEqual(hashlib.sha256((DOC/'METHODS_FREEZE.json').read_bytes()).hexdigest(),'c5391a855aee2ddf1bf8d8e0bf3c02395b900b93aabd6ee3edb24248423f70fb')
        self.assertEqual(hashlib.sha256((DOC/'FOLD_MANIFEST.json').read_bytes()).hexdigest(),'e427afbf7b9ecb3af5c144496f46b7517bdee397dd7eaa77bbdb78bea0419d93')
        add=json.loads((DOC/'C1_REVIEW_MANDATED_METHODS_ADDENDUM.json').read_text());self.assertIn('NOT_A_RETROACTIVE_ORIGINAL_FREEZE',add['freeze_semantics'])
    def test_corrected_disposition_and_scope(self):
        s=json.loads((DOC/'summary.json').read_text());self.assertEqual(s['disposition'],'XSV_WASZKIEWICZ_DYNAMIC_HYD_001_NO_TESTED_EVOLVING_RESISTANCE_FORM_HAS_STABLE_GROUPED_PREDICTIVE_ADVANTAGE');self.assertEqual(s['development_consequence'],'FIXED_RESISTANCE_RETAINED_BY_PARSIMONY');self.assertFalse(s['scope']['all_time_dependence_ruled_out'])
    def test_condition_evidence(self):
        rr=rows('CONDITION_DIFFERENCES.csv')
        for m in ['W-H1','W-H2','W-H3']:
            x=[r for r in rr if r['model_id']==m];self.assertEqual(len(x),11);self.assertEqual(sum(float(r['paired_difference'])<0 for r in x),6)
        self.assertEqual(json.loads((DOC/'EXACT_CONDITION_SIGN_RESULTS.json').read_text())['models']['W-H2']['exact_two_sided_sign_probability'],1.0)
    def test_typed_invalid_and_fail_closed(self):
        r=c.physical_flow_result([.1],[5]);self.assertFalse(r.validity[0]);self.assertEqual(r.invalid_reason[0],'LINE_PRESSURE_BELOW_BREWER_OFFSET');self.assertTrue(c.np.isnan(r.flow_value[0]))
        q,m=c.predict('W-H0A',c.np.array([1.,0.]),c.np.array([.1,.1]),c.np.array([0.,c.DT]));self.assertTrue(c.np.isnan(m[1]))
    def test_w_h2_target_independence_mutations(self):
        t=c.np.arange(20)*c.DT;p=c.np.full(20,9.);b=c.np.array([1.,0.,.2,20.]);q,m=c.predict('W-H2',b,p,t)
        observed=c.np.linspace(0,99,20);derived=c.np.linspace(-9,9,20)
        q2,m2=c.predict('W-H2',b,p,t);c.np.testing.assert_allclose(q,q2);c.np.testing.assert_allclose(m,m2)
        p2=p.copy();p2[10:]=8.;q3,_=c.predict('W-H2',b,p2,t);self.assertFalse(c.np.allclose(q,q3))
        self.assertEqual(len(observed),len(derived))
    def test_fold_and_state_mutations_rejected(self):
        with self.assertRaises(ValueError):c.validate_fold(['a'],['a'],[1],[2])
        with self.assertRaises(ValueError):c.validate_fold(['a'],['b'],[1],[1])
        with self.assertRaises(ValueError):c.validate_blocked_state('W-H2',0,reset_requested=True)
    def test_blocked_time_contract_and_invalid_counts(self):
        rr=rows('BLOCKED_TIME_RESULTS.csv');self.assertTrue(all(r['parameter_training_source']=='OTHER_PHYSICAL_BREWS_PREFIX_ONLY' for r in rr));self.assertTrue(all(r['state_at_split']=='CONTINUED_FROM_MODELED_PREFIX' for r in rr))
        inv=rows('INVALID_STATE_AUDIT.csv');self.assertEqual(sum(int(r['invalid_intervals']) for r in inv if r['inside_primary_LOCO']=='True'),0)
    def test_processing_decomposition(self):
        p=json.loads((DOC/'PROCESSING_ROBUSTNESS.json').read_text());self.assertEqual(p['mean_loco_ranking_across_tested_windows'],'STABLE');self.assertEqual(p['adoption_decision_across_tested_windows'],'STABLE');self.assertEqual(p['broader_processing_scope'],'TESTED_CONFIGURATIONS_ONLY')
        rr=rows('PROCESSING_SENSITIVITY.csv')
        for cfg in {r['configuration_id'] for r in rr}:
            self.assertEqual(next(r for r in rr if r['configuration_id']==cfg and r['model']=='W-H2')['mean_rank'],'1')

if __name__=='__main__':unittest.main()
