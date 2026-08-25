import json, math, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock

from tools.sci_md_006.core import (BOUNDS, DIFFUSIVITY, Observation, blocked_metrics,
    REQUIRED_GATES, bound_distance, decision, dump_json, model_parameters, objective, pooled_inventory,
    predict, starts, verify_bundle)
from tools.sci_md_006.parity import frozen_matrix, prefit_qualification
from tools.sci_md_006 import run_analysis


class SciMd006Tests(unittest.TestCase):
    def rows(self):
        return [Observation(1,1,s,1e-6,0,.005,.001) for s in DIFFUSIVITY]

    def test_exact_prediction_nesting(self):
        rows=self.rows(); inv={s:.01 for s in DIFFUSIVITY}; x=[math.log(.08),math.log(10.)]
        h0,_=predict(rows,inv,"H0-SHARED",x,cells=12,dt_s=.1)
        h1,_=predict(rows,inv,"H1-SPECIES",[x[0],x[1],x[0],x[1]],cells=12,dt_s=.1)
        self.assertEqual(h0,h1)

    def test_shared_and_species_parameter_maps(self):
        h0=model_parameters("H0-SHARED",[math.log(.1),math.log(2.)]);self.assertEqual(h0["caffeine"],h0["trigonelline"])
        h1=model_parameters("H1-SPECIES",[math.log(.1),math.log(2.),math.log(.2),math.log(3.)]);self.assertNotEqual(h1["caffeine"],h1["trigonelline"])

    def test_optimizer_scope_excludes_inventory_and_diffusivity(self):
        self.assertEqual(len(starts("H0-SHARED")[0]),2)
        self.assertEqual(len(starts("H1-SPECIES",[math.log(.1),math.log(2.)])[0]),4)

    def test_fold_inventory_exclusion_and_reproducibility(self):
        source={(e,s):e/1000 for e in (1,2,3) for s in DIFFUSIVITY}
        got=pooled_inventory(source,[1,2]);self.assertEqual(got["caffeine"],.0015)
        source[(3,"caffeine")]=99;self.assertEqual(pooled_inventory(source,[1,2]),got)

    def test_equal_species_objective(self):
        rows=[Observation(1,1,"caffeine",1,0,1,1),Observation(1,2,"caffeine",1,0,1,1),Observation(1,1,"trigonelline",1,0,1,1)]
        pred={(1,1,"caffeine"):math.e,(1,2,"caffeine"):math.e,(1,1,"trigonelline"):math.exp(2)}
        self.assertAlmostEqual(objective(rows,pred),2.5)

    def test_concatenated_nrmse_and_thresholds(self):
        rows=[Observation(1,1,s,1,0,1,1) for s in DIFFUSIVITY]
        p={(1,1,s):{"H0-SHARED":2.,"H1-SPECIES":1.84} for s in DIFFUSIVITY}
        m=blocked_metrics(rows,p);self.assertAlmostEqual(m["improvement"],.16);self.assertTrue(m["joint_improvement_pass"])
        self.assertTrue(all(m["species_noninferiority_pass"].values()))

    def test_bound_distance(self):
        self.assertEqual(bound_distance(BOUNDS["k_1_s"][0],"k_1_s"),0)
        self.assertAlmostEqual(bound_distance(math.sqrt(.002*.5),"k_1_s"),.5)

    def test_decision_truth_table(self):
        base={k:True for k in REQUIRED_GATES}
        self.assertIn("ELIGIBLE",decision(base)); base["joint_improvement"]=False;self.assertIn("BASELINE_RETAINED",decision(base))
        base["h0_identifiability"]=False;self.assertEqual(decision(base),"SCI_MD_006_SHARED_NULL_NOT_QUALIFIED")
        base["prefit_application_parity"]=False;self.assertEqual(decision(base),"SCI_MD_006_TRAINING_APPLICATION_CONTRACT_BLOCKED")

    def test_nonpositive_prediction_fails_closed(self):
        rows=[Observation(1,1,"caffeine",1e-6,0,0,.001)]
        with self.assertRaises(Exception): predict(rows,{"caffeine":.01,"trigonelline":.01},"H0-SHARED",[math.log(.1),math.log(2.)])

    def test_deterministic_serialization(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a";b=Path(d)/"b";dump_json(a,{"z":1,"a":2});dump_json(b,{"a":2,"z":1});self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_secondary_cannot_enter_decision(self):
        with self.assertRaises(TypeError): decision({"data_contract":True}, secondary=True)

    def test_frozen_bundle_direct_consumption_and_hash_failure(self):
        bundle=Path(__file__).parents[1]/"validation/sci_md_006/training_bundle"
        self.assertEqual(verify_bundle(bundle)["semantic_target_access"],False)
        with tempfile.TemporaryDirectory() as d:
            copied=Path(d)/"bundle";shutil.copytree(bundle,copied)
            (copied/"training_contract.json").write_text("{}")
            with self.assertRaisesRegex(ValueError,"MEMBER_HASH_MISMATCH"):verify_bundle(copied)

    def test_prefit_blocks_unrepresentable_application_without_optimizer(self):
        root=Path(__file__).parents[1]
        with mock.patch("tools.sci_md_006.parity.sha256",side_effect=lambda p: "d793a731fd2f4f82e623350c61835d0e955d886849f5e363a5abd8dd0fae4c93" if p.name=="accepted-solver" else "9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599"):
            with mock.patch.object(Path,"is_file",return_value=True):result=prefit_qualification(root,Path("accepted-solver"),{"frozen":True})
        self.assertFalse(result["pass"]);self.assertEqual(result["optimizer_call_count"],0)
        self.assertEqual(result["reason"],"UNCHANGED_PRODUCTION_INTERFACE_HAS_NO_IDENTICAL_PRESCRIBED_FLOW_BOUNDARY")

    def test_execute_orders_parity_before_fit(self):
        source=Path(run_analysis.__file__).read_text()
        body=source[source.index("def execute("):source.index("def close_manifest(")]
        self.assertLess(body.index("prefit_qualification("),body.index("fit(obs"))

    def test_stopped_candidate_and_review_pass_required(self):
        self.assertIn("d2236022fd7cc9e81ee008be7c932ffd32487efc",run_analysis.STOPPED)
        self.assertEqual(run_analysis.REVIEW_PASS,"SCI_MD_006_CORRECTED_PREEXECUTION_REVIEW_PASS")

    def test_h1_parity_numerical_and_integrity_are_explicit(self):
        for key in ("h1_postfit_parity","h1_numerical","production_solver_immutable","angeloni_nonaccess"):
            self.assertIn(key,REQUIRED_GATES)
        gates={k:True for k in REQUIRED_GATES};gates["h1_postfit_parity"]=False
        self.assertEqual(decision(gates),"SCI_MD_006_SHARED_PARAMETER_PRODUCTION_BASELINE_RETAINED")

    def test_profile_contract_requires_two_sides_and_reoptimization(self):
        source=(Path(__file__).parents[1]/"tools/sci_md_006/identifiability.py").read_text()
        self.assertIn("least_squares(fun",source);self.assertIn("lower_profile_crossing",source)
        self.assertIn("upper_profile_crossing",source);self.assertIn("profile_open_to_bound",source)

    def test_freeze_is_nonrecursive(self):
        source=(Path(__file__).parents[1]/"tools/sci_md_006/freeze.py").read_text()
        self.assertNotIn('"validation/sci_md_006/CORRECTED_SCIENTIFIC_FREEZE_MANIFEST.json"',source.split("EXACT=",1)[1].split("def main",1)[0])
