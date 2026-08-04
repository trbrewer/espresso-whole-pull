import csv
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "verification/cases/xsv_taichi_001"


class XSVTaichi001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads(
            (CASE_ROOT / "XSV_TAICHI_001_PROTOCOL.json").read_text(encoding="utf-8")
        )
        with (CASE_ROOT / "XSV_TAICHI_001_CASE_MATRIX.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.matrix = list(csv.DictReader(handle))

    def test_frozen_protocol_identity_and_quantity_contract(self) -> None:
        protocol = self.protocol
        self.assertEqual(protocol["task"], "XSV-TAICHI-001")
        self.assertEqual(
            protocol["sources"]["puckworks"]["commit"],
            "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        )
        self.assertEqual(
            protocol["sources"]["puckworks"]["tree"],
            "1d553e44ee2f7480a5df521560801b478618cc84",
        )
        quantities = protocol["quantities"]
        self.assertEqual(quantities["phi_gross"], "N_fluid / N_total")
        self.assertEqual(
            quantities["K_gross_lu"], "nu_lu * q_box_lu / g_lu"
        )
        self.assertEqual(
            protocol["adapters"]["primary"]["K_EWP_lu"],
            "phi_gross * k_puckworks_returned",
        )
        self.assertNotEqual(
            protocol["adapters"]["primary"]["K_EWP_lu"],
            protocol["adapters"]["alternate_diagnostic"]["K_ALT_lu"],
        )
        self.assertEqual(
            protocol["claim_ceiling"]["physical_validation"], "NOT_ESTABLISHED"
        )

        launcher_path = ROOT / "scripts/xsv_taichi_001.py"
        runtime_path = CASE_ROOT / "xsv_taichi_001_runtime.py"
        self.assertTrue(launcher_path.is_file())
        self.assertTrue(runtime_path.is_file())
        self.assertTrue(os.access(launcher_path, os.X_OK))
        self.assertTrue(launcher_path.stat().st_mode & stat.S_IXUSR)
        launcher = launcher_path.read_text(encoding="utf-8")
        runtime = runtime_path.read_text(encoding="utf-8")
        self.assertEqual(launcher.splitlines()[0], "#!/usr/bin/env python3")
        self.assertIn("runpy.run_path", launcher)
        self.assertIn('"verification"', launcher)
        self.assertIn('"cases"', launcher)
        self.assertIn('"xsv_taichi_001"', launcher)
        self.assertIn('"xsv_taichi_001_runtime.py"', launcher)
        forbidden_import = re.compile(
            r"^\s*(?:from|import)\s+(?:numpy|pandas|scipy|taichi)(?:\s|\.|$)",
            re.MULTILINE,
        )
        self.assertIsNone(forbidden_import.search(launcher))
        for function_name in (
            "generate_mask",
            "connected_descriptor",
            "generate_geometry",
            "parse_args",
            "main",
        ):
            self.assertIn(f"def {function_name}(", runtime)
        self.assertIn(
            'EXPECTED_PUCKWORKS_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"',
            runtime,
        )
        self.assertIn("Path(__file__).resolve().parents[3]", runtime)
        self.assertIn("sys.dont_write_bytecode = True", runtime)
        geometry_manifest = CASE_ROOT / "XSV_TAICHI_001_GEOMETRY_MANIFEST.json"
        self.assertEqual(
            hashlib.sha256(geometry_manifest.read_bytes()).hexdigest(),
            "5ddb9617b3543d7f48eecf5941291d265894a6cd2d5a142265a0750ab509afdd",
        )

    def test_exact_prospective_run_matrices(self) -> None:
        lbm = [row for row in self.matrix if row["family"] == "LBM"]
        openfoam = [row for row in self.matrix if row["family"] == "OPENFOAM"]
        self.assertEqual(len(lbm), 19)
        self.assertEqual(len(openfoam), 8)
        self.assertEqual(len({row["run_id"] for row in self.matrix}), 27)
        self.assertEqual({row["precision"] for row in lbm}, {"float64"})
        self.assertEqual(
            {row["geometry"] for row in lbm}, {"CH33", "SP32", "M0A"}
        )
        self.assertEqual(
            {row["fixture"] for row in openfoam},
            {"UNIFORM", "AXIAL_TWO_LAYER", "RADIAL_TWO_ZONE"},
        )
        self.assertTrue(all(row["status"] == "PROSPECTIVE" for row in self.matrix))

    def test_geometry_definitions_and_thresholds_are_exact(self) -> None:
        geometry = self.protocol["geometry_definitions"]
        self.assertEqual(geometry["CH33"]["shape"], [33, 33, 33])
        self.assertEqual(
            geometry["SP32"],
            {"function": "lb_reference.sphere_case", "L": 32, "c_nom": 0.08},
        )
        self.assertEqual(geometry["M0A"]["seed"], 42)
        self.assertEqual(geometry["M0A"]["hetero_amp"], 0.0)
        thresholds = self.protocol["thresholds"]
        self.assertEqual(thresholds["backend_relative_q_max"], 0.0025)
        self.assertEqual(thresholds["channel_relative_error_max"], 0.0075)
        self.assertEqual(thresholds["returned_identity_relative_tolerance"], 1e-12)
        self.assertEqual(thresholds["serial_mpi_relative_difference_max"], 1e-8)

    def test_frozen_geometry_manifest_is_complete_and_connected(self) -> None:
        manifest = json.loads(
            (CASE_ROOT / "XSV_TAICHI_001_GEOMETRY_MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["generation_repetitions"], 2)
        self.assertEqual(manifest["repeat_identity"], "PASS")
        self.assertFalse(
            manifest["connectivity"][
                "connected_porosity_used_to_redefine_flow_or_permeability"
            ]
        )
        geometries = {row["case_id"]: row for row in manifest["geometries"]}
        self.assertEqual(set(geometries), {"CH33", "SP32", "M0A"})
        expected_payloads = {
            "CH33": "9bf1654efe5045c59f8b0bbb0b2f537b390382522a1c34bfaaa294635240edd7",
            "SP32": "40196fd2f2b86de853f2afcfce801b6da0fca1d399e107c6ed40328776ed5a85",
            "M0A": "10d9a010cbac4b8579154456c4271ecd2808af5116beab15a2ffd4e2c99cd039",
        }
        expected_configs = {
            "CH33": "674b2f00791e0f12f9dd5cf8c26b98afd56f2ccde81980189cfddda7c5afbebb",
            "SP32": "6f086749b44555938e2b5612c2a41ebcc6536661756a541a78f5c1657d6eb9ac",
            "M0A": "4c5ded6230ec5781c810d2a8f53a92a507a3b393cc99f16d9c2a8e5fb027b4f9",
        }
        for case_id, row in geometries.items():
            self.assertEqual(row["payload_sha256"], expected_payloads[case_id])
            self.assertEqual(
                row["geometry_config_sha256"], expected_configs[case_id]
            )
            self.assertTrue(row["x_through_connected"])
            self.assertGreater(row["phi_gross"], 0.0)
            self.assertLess(row["phi_gross"], 1.0)
            self.assertLessEqual(row["phi_x_connected"], row["phi_gross"])
        self.assertEqual(manifest["retained_flow_solutions_before_freeze"], 0)


if __name__ == "__main__":
    unittest.main()
