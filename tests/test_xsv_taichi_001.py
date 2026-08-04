import csv
import json
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
