import importlib.util
import json
import math
from pathlib import Path
import unittest
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/"verification/cases/xsv_ens_001"
spec=importlib.util.spec_from_file_location("xsv_analysis",CASE/"xsv_ens_001_analysis.py")
analysis=importlib.util.module_from_spec(spec); spec.loader.exec_module(analysis)

class XsvEns001Tests(unittest.TestCase):
    def setUp(self): self.protocol=json.loads((CASE/"XSV_ENS_001_PROTOCOL.json").read_text())
    def test_exact_targets_not_rounded(self):
        self.assertEqual(self.protocol["targets"]["primary"],0.373506)
        self.assertEqual(self.protocol["targets"]["supporting"],[0.389226,0.395294])
        self.assertNotEqual(self.protocol["targets"]["primary"],0.4)
    def test_gross_void_contract_is_adversarial(self):
        phi,q,nu,g=.4,2e-5,.2,1e-6
        kg=nu*q/g; kv=nu*(q/phi)/g
        self.assertTrue(math.isclose(kg,phi*kv)); self.assertFalse(math.isclose(kg,kv))
    def test_false_pairing_prohibited(self):
        self.assertIn("RELATED_NON_NESTED",(ROOT/"docs/verification/XSV_ENS_001_STOCHASTIC_GPU_PORE_SCALE_CLOSURE_AND_RVE_PROTOCOL.md").read_text())
        self.assertFalse(self.protocol["retry"]["scientific_replacement_seed"])
    def test_directional_claim_is_diagonal_only(self):
        text=(ROOT/"docs/verification/XSV_ENS_001_STOCHASTIC_GPU_PORE_SCALE_CLOSURE_AND_RVE_PROTOCOL.md").read_text()
        self.assertIn("diagonal\ncomponents, not a complete permeability tensor",text)
    def test_static_state_not_dynamic_mechanism(self):
        self.assertIn("NOT_DYNAMIC_MECHANISM_IDENTIFICATION",self.protocol["classification"])
    def test_grouped_closure_and_bootstrap_are_frozen(self):
        self.assertEqual(self.protocol["ensemble"]["bootstrap_seed"],20260812)
        self.assertEqual(self.protocol["ensemble"]["minimum_n"],8)
        self.assertEqual(self.protocol["ensemble"]["maximum_n"],24)
    def test_matrix_identity_uniqueness(self):
        import csv
        with (CASE/"XSV_ENS_001_SCORED_MATRIX.csv").open() as f: ids=[r["case_id"] for r in csv.DictReader(f)]
        self.assertEqual(len(ids),len(set(ids)))
    def test_wide_interval_requires_next_batch(self):
        result=analysis.bootstrap_log_mean_precision([1,2,4,8,1,2,4,8])
        self.assertEqual(result["action"],"ADD_NEXT_FROZEN_BATCH")
    def test_maximum_n_allows_unresolved_stop(self):
        result=analysis.bootstrap_log_mean_precision(([1,8]*12))
        self.assertEqual(result["action"],"STOP_MAXIMUM_N_UNRESOLVED")
    def test_rve_is_data_dependent(self):
        stable=[{"L":40,"mean_K":1.0,"cv_K":.2,"sampling_precision_met":True,"mean_ratio_to_largest_ci":[.95,1.05]},
                {"L":56,"mean_K":1.02,"cv_K":.21,"sampling_precision_met":True,"mean_ratio_to_largest_ci":[.96,1.04]},
                {"L":72,"mean_K":1.0,"cv_K":.2,"sampling_precision_met":True,"mean_ratio_to_largest_ci":[1,1]}]
        unstable=[dict(x) for x in stable]; unstable[-2]["mean_ratio_to_largest_ci"]=[.7,.8]
        self.assertNotEqual(analysis.rve_adjudication(stable,resolution_effect_resolved=True,gpu_limit_measured=False)["mean_disposition"],analysis.rve_adjudication(unstable,resolution_effect_resolved=True,gpu_limit_measured=False)["mean_disposition"])
    def test_physical_lineage_unions_hash_parent_and_nested_rng(self):
        rows=[{"geometry_id":"A","geometry_sha256":"h1","family":"BASELINE","L":40,"seed":1,"voxel_um":30,"parent_id":""},
              {"geometry_id":"DUP","geometry_sha256":"h1","family":"DIRECTIONAL","L":40,"seed":1,"voxel_um":30,"parent_id":""},
              {"geometry_id":"CHILD","geometry_sha256":"h2","family":"THROAT_RESTRICTION","L":40,"seed":1,"voxel_um":30,"parent_id":"A"},
              {"geometry_id":"SF50","geometry_sha256":"h3","family":"SOLID_FRACTION","L":40,"seed":1,"voxel_um":30,"parent_id":""},
              {"geometry_id":"SF60","geometry_sha256":"h4","family":"SOLID_FRACTION","L":40,"seed":1,"voxel_um":30,"parent_id":""}]
        labels=analysis.assign_physical_lineages(rows)
        self.assertEqual(labels["A"],labels["DUP"]); self.assertEqual(labels["A"],labels["CHILD"]); self.assertEqual(labels["SF50"],labels["SF60"])
    def test_robust_target_requires_minimum_valid_n(self):
        self.assertEqual(analysis.target_disposition([.2,.25,.3],[.6,.6,.6]),"TARGET_ATTAINMENT_UNRESOLVED_UNCERTAINTY")
        self.assertEqual(analysis.target_disposition([.2]*8,[.6]*8),"ROBUST_TARGET_ATTAINMENT_WITHOUT_TOPOLOGY_LOSS")
    def test_porosity_only_contract_and_scale_correction(self):
        reducer=(CASE/"xsv_ens_001_reduce.py").read_text()
        self.assertIn('"A_porosity_only":["phi_gross"]',reducer)
        self.assertIn("StandardScaler()",reducer)
    def test_nonconverged_rows_are_retained_in_committed_results(self):
        import csv
        with (CASE/"XSV_ENS_001_REALIZATION_RESULTS.csv").open() as f: rows=list(csv.DictReader(f))
        self.assertGreater(sum(r["status"]=="NONCONVERGED" for r in rows),0)
    def test_lineage_label_prevents_hash_cross_fold(self):
        import csv
        with (CASE/"XSV_ENS_001_GEOMETRY_MANIFEST.csv").open() as f: rows=list(csv.DictReader(f))
        by_hash={}
        for row in rows:
            prior=by_hash.setdefault(row["geometry_sha256"],row["physical_lineage_id"])
            self.assertEqual(prior,row["physical_lineage_id"])

if __name__=="__main__": unittest.main()
