from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from waszkiewicz_effective_permeability import (  # noqa: E402
    MINIMUM_MULTIPLIER,
    bounded_multiplier,
    closure_state,
    dynamic_state,
    phi_factor,
    q_static,
    qhat,
    raw_multiplier,
    solids_sigmoid,
)
from wp02_contract_bridge import scenario  # noqa: E402


class WP02EffectivePermeabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "validation/wp02/WP02_001_CLOSURE_CONTRACT.json").read_text()
        )
        cls.source = cls.contract["source_parameters"]
        cls.kwargs = {
            "pc_bar": cls.source["pc_bar"],
            "qc_g_s": cls.source["qc_g_per_s"],
            "k_g": cls.source["k_solids_g"],
            "l_s": cls.source["l_solids_s"],
            "m_s": cls.source["m_solids_s"],
            "dose_g": cls.source["dose_g"],
        }

    def test_exact_source_identity_and_parameters(self) -> None:
        dependency = self.contract["source_dependency"]
        self.assertEqual(dependency["commit"], "fc61c4670ec7bf801e40bb391aab16048b8da26b")
        self.assertEqual(dependency["tree"], "1d553e44ee2f7480a5df521560801b478618cc84")
        self.assertEqual(self.source["pc_bar"], 12.391550000000002)
        self.assertEqual(self.source["qc_g_per_s"], 1.8969919954879988)
        self.assertEqual(self.source["fixed_first_drop_offset_s"], 8.0)
        self.assertFalse(self.source["fixed_first_drop_offset_used_in_mapping"])

    def test_qhat_and_phi_factor(self) -> None:
        self.assertEqual(qhat(1.0), 1.0)
        self.assertAlmostEqual(qhat(0.5), 0.9375, places=15)
        self.assertAlmostEqual(phi_factor(0.1), 3.150298614560608e-5, places=16)
        direct_near_series = phi_factor(0.0005)
        self.assertGreater(direct_near_series, 0.0)
        self.assertAlmostEqual(direct_near_series, 0.0005**4 / 4.0, delta=2e-17)

    def test_static_sigmoid_and_dynamic_formula(self) -> None:
        self.assertAlmostEqual(q_static(9.0, self.source["pc_bar"], self.source["qc_g_per_s"]), 1.886346745611387, places=14)
        self.assertAlmostEqual(solids_sigmoid(self.source["l_solids_s"], self.source["k_solids_g"], self.source["l_solids_s"], self.source["m_solids_s"]), self.source["k_solids_g"] / 2.0)
        state = dynamic_state(50.0, 9.0, **self.kwargs)
        self.assertGreaterEqual(state["flow_g_per_s"], 0.0)
        self.assertTrue(math.isfinite(state["phi_t"]))

    def test_multiplier_bounds_and_roundoff_rejection(self) -> None:
        self.assertEqual(bounded_multiplier(0.0), MINIMUM_MULTIPLIER)
        self.assertEqual(bounded_multiplier(1.0 + 5e-11), 1.0)
        with self.assertRaises(ValueError):
            bounded_multiplier(1.0 + 2e-10)

    def test_time_mapping_hold_and_unsaturated_inactivity(self) -> None:
        common = dict(
            p_bar=9.0,
            source_to_solver_offset_s=3.0,
            source_validity_start_s=10.01001001001001,
            minimum=1e-6,
            base_permeability_m2=2.8642613245723525e-15,
            **self.kwargs,
        )
        unsaturated = closure_state(12.0, False, **common)
        self.assertFalse(unsaturated["active"])
        self.assertEqual(unsaturated["multiplier"], 1.0)
        hold = closure_state(5.0, True, **common)
        self.assertEqual(hold["source_support_status"], "PRE_SOURCE_SUPPORT_SATURATED_HOLD")
        self.assertEqual(hold["source_state_time_s"], 10.01001001001001)
        supported = closure_state(20.0, True, **common)
        self.assertEqual(supported["source_time_s"], 17.0)
        self.assertNotEqual(supported["source_time_s"], 12.0)

    def test_floor_sensitivity_is_immaterial_in_scored_window(self) -> None:
        values = []
        for floor in self.contract["numerical_regularization"]["floor_sensitivity_values"]:
            curve = []
            for index in range(100, 1000):
                time = 100.0 * index / 999.0
                raw = raw_multiplier(time, 9.0, **self.kwargs)
                curve.append(bounded_multiplier(raw, floor))
            late = sum(curve[800:900]) / 100.0
            values.append(([x / late for x in curve[:800]], late))
        for (a, late_a), (b, late_b) in zip(values, values[1:]):
            self.assertLessEqual(
                max(abs(x - y) for x, y in zip(a, b)),
                self.contract["numerical_regularization"][
                    "maximum_normalized_rmse_difference"
                ],
            )
            self.assertLessEqual(
                abs(late_a - late_b) / late_a,
                self.contract["numerical_regularization"][
                    "maximum_late_flow_relative_difference"
                ],
            )

    def test_canonical_scenarios_and_eight_bar_reductions(self) -> None:
        nine = scenario(ROOT, "nine_bar_reconstruction")
        eight = scenario(ROOT, "eight_bar_transfer")
        self.assertEqual(nine["flow_comparison_contract"]["protected_shot_ids"], ["9-1", "9-2", "9-3", "9-4", "9-5"])
        self.assertEqual(eight["flow_comparison_contract"]["protected_shot_ids"], ["8-1", "8-1b", "8-2", "8-3"])
        self.assertEqual(eight["hydraulics"]["target_inlet_pressure_gauge_Pa"], 756616.724)
        self.assertEqual(eight["hydraulics"]["saturated_permeability_m2"], 3.2464136971534258e-15)
        self.assertEqual(nine["effective_permeability_evolution"]["minimum_effective_multiplier"], 1e-6)

    def test_bridge_check_and_edited_configuration_rejection(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/wp02_contract_bridge.py"), "--root", str(ROOT), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with tempfile.TemporaryDirectory() as td:
            edited = json.loads(
                (ROOT / "config/reconstruction_WP02A_waszkiewicz_9bar.json").read_text()
            )
            edited["hydraulics"]["target_inlet_pressure_gauge_Pa"] += 1.0
            path = Path(td) / "edited.json"
            path.write_text(json.dumps(edited))
            case = Path(td) / "case"
            generated = subprocess.run(
                [sys.executable, str(ROOT / "scripts/prepare_case.py"), "--root", str(ROOT), "--config", str(path), "--case-dir", str(case), "--nprocs", "32"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(generated.returncode, 0)

    def test_change_boundary_is_truthful(self) -> None:
        boundary = self.contract["authorization_boundaries"]
        self.assertTrue(boundary["governing_physics_change"])
        self.assertTrue(boundary["new_optional_closure_added"])
        for key in ("frozen_R0_configuration_change", "constant_R1_configuration_change", "wetting_physics_change", "pore_volume_storage_change", "mesh_motion_change", "chemistry_model_change"):
            self.assertFalse(boundary[key])

    def test_historical_identities_unchanged(self) -> None:
        self.assertEqual(
            hashlib.sha256((ROOT / "config/reconstruction_R1_waszkiewicz_9bar.json").read_bytes()).hexdigest(),
            "be275c0302f30dc4dcab120469b0bc62d444e401a80e082a337d9225c659b876",
        )


if __name__ == "__main__":
    unittest.main()
