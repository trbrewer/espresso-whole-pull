import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/"verification/cases/xsv_ens_001"

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

if __name__=="__main__": unittest.main()
