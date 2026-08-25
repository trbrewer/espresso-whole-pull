import json, math, tempfile, unittest
from pathlib import Path

import numpy as np

from tools.sci_md_006.core import (BOUNDS, DIFFUSIVITY, Observation, blocked_metrics,
    bound_distance, decision, dump_json, model_parameters, objective, pooled_inventory,
    predict, starts)


class SciMd006Tests(unittest.TestCase):
    def rows(self):
        return [Observation(1,1,s,1e-6,0,.005,.001) for s in DIFFUSIVITY]

    def test_exact_prediction_nesting(self):
        rows=self.rows(); inv={s:.01 for s in DIFFUSIVITY}; x=np.log([.08,10.])
        h0,_=predict(rows,inv,"H0-SHARED",x,cells=12,dt_s=.1)
        h1,_=predict(rows,inv,"H1-SPECIES",[x[0],x[1],x[0],x[1]],cells=12,dt_s=.1)
        self.assertEqual(h0,h1)

    def test_shared_and_species_parameter_maps(self):
        h0=model_parameters("H0-SHARED",np.log([.1,2.]));self.assertEqual(h0["caffeine"],h0["trigonelline"])
        h1=model_parameters("H1-SPECIES",np.log([.1,2.,.2,3.]));self.assertNotEqual(h1["caffeine"],h1["trigonelline"])

    def test_optimizer_scope_excludes_inventory_and_diffusivity(self):
        self.assertEqual(len(starts("H0-SHARED")[0]),2)
        self.assertEqual(len(starts("H1-SPECIES",np.log([.1,2.]))[0]),4)

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
        base={k:True for k in ("data_contract","inventory_policy","nesting","parity","h0_optimizer","h0_identifiable","h0_no_bounds","numerical","governance","joint_improvement","species_noninferiority","h1_identifiable","h1_no_bounds","h1_optimizer","nesting_inequality")}
        self.assertIn("ELIGIBLE",decision(base)); base["joint_improvement"]=False;self.assertIn("BASELINE_RETAINED",decision(base))
        base["h0_identifiable"]=False;self.assertEqual(decision(base),"SCI_MD_006_SHARED_NULL_NOT_QUALIFIED")
        base["parity"]=False;self.assertEqual(decision(base),"SCI_MD_006_TRAINING_APPLICATION_CONTRACT_BLOCKED")

    def test_nonpositive_prediction_fails_closed(self):
        rows=[Observation(1,1,"caffeine",1e-6,0,0,.001)]
        with self.assertRaises(Exception): predict(rows,{"caffeine":.01,"trigonelline":.01},"H0-SHARED",np.log([.1,2.]))

    def test_deterministic_serialization(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a";b=Path(d)/"b";dump_json(a,{"z":1,"a":2});dump_json(b,{"a":2,"z":1});self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_secondary_cannot_enter_decision(self):
        with self.assertRaises(TypeError): decision({"data_contract":True}, secondary=True)

