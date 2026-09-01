import csv, hashlib, json, pathlib, tempfile, unittest
from analysis.obs_pannusch_fraction_window_001.core import *

ROOT=pathlib.Path(__file__).resolve().parents[1]

class QualificationTests(unittest.TestCase):
    def test_fraction_coordinates(self):
        self.assertEqual(ASSAY_IDS,(1,2,3,5,7,10)); self.assertEqual(ASSAY_IDS[4:],(7,10))
    def test_length_and_undocumented_order_fail(self):
        self.assertEqual(join(list(range(24)),False),[]); self.assertEqual(join(list(range(23)),True),[])
    def test_explicit_mapping(self):
        x=join(list(range(24)),True); self.assertEqual(x[0],(1,1,1)); self.assertEqual(x[-1],(8,3,24))
    def test_unique_matching_and_ambiguity(self):
        self.assertEqual(unique_matching({"a":{1},"b":{2}}),(("a",1),("b",2)))
        with self.assertRaisesRegex(ValueError,"ambiguous"): unique_matching({"a":{1,2},"b":{1,2}})
    def test_full_vial_sequence(self):
        x=cumulative_boundaries([1]*10); self.assertEqual(x,[1,2,3,4,5,6,7,8,9,10]); self.assertEqual([x[i-1] for i in ASSAY_IDS],[1,2,3,5,7,10])
    def test_invalid_masses(self):
        for masses in ([1]*9,[1]*9+[-1],[1]*9+[float("nan")]):
            with self.assertRaises(ValueError): cumulative_boundaries(masses)
    def test_inversion(self):
        self.assertAlmostEqual(invert_mass(.1,2,2.1,(0,10)),1)
        with self.assertRaisesRegex(ValueError,"non-monotonic"): invert_mass(-1,1,.1,(0,2))
        with self.assertRaises(ValueError): invert_mass(.1,2,1000,(0,2))
        with self.assertRaises(ValueError): invert_mass(.1,2,-1,(0,2))
    def test_observer_math(self):
        self.assertEqual(interval_average(lambda x:3,1,2),3); self.assertEqual(interval_average(lambda x:2*x+1,1,3),5)
        q=normalize([1]*6,[1,2,3,4,5,6]); self.assertAlmostEqual(sum(q),1)
        with self.assertRaises(ValueError): normalize([float("nan")]*6,[1]*6)
    def test_identity_and_classifier(self):
        self.assertEqual(classify(0,0,0,False,0,0),("NULL",False))
        self.assertEqual(classify(-1,-2,-.1,True,1,.11),("POSITIVE",True))
        self.assertEqual(classify(-1,-2,.1,True,0,.5),("NULL",False))
        self.assertEqual(classify(1,.1,2,False,4,0),("NEGATIVE",False))
    def test_source_semantics_guard(self):
        good="""load('MassData_modelval.mat')\nMassData(i*3-3+j).flow; MassData(i*3-3+j).a; MassData(i*3-3+j).b;\nmE = ExperimentalData(i).run(j).mE_cum;\ntE(:,1) = (-b+sqrt(b.^2-4.*a.*(-mE)))./(2.*a);\nExperimentalData(i).run(j).tE = tE;\n%% TdS\ncAlcaloids"""
        self.assertTrue(source_semantics(good))
        with self.assertRaises(ValueError): source_semantics(good.replace("%% TdS","cAlcaloids\n%% TdS"))
    def test_hash_controls(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError): verify_sources(d)
    def test_committed_result_contract_if_present(self):
        doc=ROOT/"docs/analysis/obs_pannusch_fraction_window_001"
        if not doc.exists(): self.skipTest("generated result not installed yet")
        s=json.loads((doc/"summary.json").read_text()); self.assertEqual(s["joins"],{"qualified":24,"total":24}); self.assertEqual(s["primary_delta"],0)
        self.assertEqual(s["claims"],["TARGET_EXPOSED","SOURCE_INTERNAL","NOT INDEPENDENT VALIDATION","NOT PHYSICAL VALIDATION","NOT HYDRAULIC VALIDATION","NOT PRODUCTION QUALIFICATION"])
    def test_independent_audit_perturbations(self):
        audit=json.loads((ROOT/"docs/analysis/obs_pannusch_fraction_window_001/QUALIFICATION_AUDIT.json").read_text())
        self.assertEqual(audit["status"],"PASS")
        for name in ("chemistry_zero_invariant","chemistry_permutation_invariant","chemistry_synthetic_invariant","source_hashes","code_hashes","prior_results_unavailable_to_phase_a"):
            self.assertTrue(audit["checks"][name],name)
    def test_baseline_rows_and_required_diagnostics(self):
        doc=ROOT/"docs/analysis/obs_pannusch_fraction_window_001"
        summary=json.loads((doc/"summary.json").read_text()); self.assertEqual(summary["baseline_reproduction"]["rows"],144); self.assertEqual(summary["baseline_reproduction"]["status"],"PASS_EXACT_ROW_IDENTITY")
        with (doc/"METRIC_RESULTS.csv").open(newline="") as stream: rows=list(csv.DictReader(stream))
        pairs={(r["metric"],r["scope"]) for r in rows}
        required={("mean_signed_residual",f"profile_position_{i}") for i in range(1,7)}|{("systematic_residual_vector_norm","positions_2_5_6"),("cumulative_share_rmse","PRIMARY"),("centroid_error","PRIMARY"),("exact_four_condition_sign_enumeration","4_conditions")}
        self.assertTrue(required<=pairs); self.assertTrue(all(float(r["delta"])==0 for r in rows))
    def test_repository_invariants(self):
        changed=set(__import__('subprocess').check_output(["git","diff","--name-only","HEAD"],cwd=ROOT,text=True).splitlines())
        forbidden=("applications/solvers/","cases/","dependencies/puckworks.lock.json")
        self.assertFalse(any(path.startswith(forbidden[:2]) or path==forbidden[2] for path in changed))

if __name__=="__main__": unittest.main()
