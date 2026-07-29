import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "machine_ref", ROOT / "scripts/machine_coupling_reference.py"
)
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)


class MachineCouplingTests(unittest.TestCase):
    def test_backward_euler_residual_and_continuous_limit(self):
        args = (0.02, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12)
        p = 0.0
        for _ in range(1500):
            row = REF.backward_euler(p, *args)
            self.assertLess(abs(row["residual_m3_s"]), 1e-18)
            p = row["pressure_Pa"]
        exact = REF.continuous(30.0, 0.0, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12)
        self.assertLess(abs(p - exact["pressure_Pa"]) / exact["pressure_Pa"], 0.01)

    def test_refinement_is_first_order(self):
        exact = REF.continuous(1.0, 0.0, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12)
        errors = []
        for dt in (0.04, 0.02, 0.01):
            p = 0.0
            for _ in range(round(1.0 / dt)):
                p = REF.backward_euler(
                    p, dt, 0.0, 2e-11, 6e-6, 1.2e6, 1.65e-12
                )["pressure_Pa"]
            errors.append(abs(p - exact["pressure_Pa"]))
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])
        self.assertGreater(math.log(errors[0] / errors[1], 2), 0.8)

    def test_run_spec_is_synthetic_and_predeclared(self):
        data = json.loads(
            (ROOT / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text()
        )
        self.assertEqual(data["compliance_sensitivity_ratio"], [0.25, 1.0, 4.0])
        for name in ("MC-1", "MC-2", "MC-3", "MC-4", "MC-5"):
            self.assertTrue(data["case_matrix"][name]["parameter_role"].startswith("SYNTHETIC_"))

    def test_invalid_machine_config_is_rejected(self):
        prepare_spec = importlib.util.spec_from_file_location(
            "prepare", ROOT / "scripts/prepare_case.py"
        )
        prepare = importlib.util.module_from_spec(prepare_spec)
        prepare_spec.loader.exec_module(prepare)
        scenario = json.loads((ROOT / "config/reference_R0.json").read_text())
        scenario["pressureBoundaryModel"] = "lumpedMachineCompliance"
        scenario["machineBoundary"] = {}
        with self.assertRaises(SystemExit):
            prepare.render_properties(scenario)


if __name__ == "__main__":
    unittest.main()
