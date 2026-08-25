import copy
import csv
import hashlib
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/sci_md_004_stage_e1_hydraulic_reconciliation"


class HydraulicFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = json.loads((OUT / "CONDITIONAL_DARCY_ADAPTER.json").read_text())
        cls.freeze = json.loads((OUT / "EXECUTABLE_CASE_FREEZE.json").read_text())

    def test_exact_pairing_and_nonvariety_keys(self):
        self.assertEqual(len(self.adapter["conditions"]), 33)
        keys = set()
        for row in self.adapter["conditions"]:
            self.assertEqual(row["varieties"], ["Arabica", "Robusta"])
            self.assertEqual(len(row["sample_ids"]), 2)
            key = tuple(row["apparatus_key"])
            self.assertNotIn(key, keys)
            keys.add(key)

    def test_porosity_water_and_dimensional_permeability(self):
        self.assertEqual(self.adapter["porosity_by_grind"], {"C": .330, "F": .276, "O": .305})
        for row in self.adapter["conditions"]:
            T, pressure, grind, duration, radius, depth, beverage, _ = row["apparatus_key"]
            expected = (row["dynamic_viscosity_Pa_s"] * depth * beverage /
                        (row["liquid_density_kg_m3"] * math.pi * radius**2 * pressure * duration))
            self.assertEqual(row["effective_permeability_m2"], expected)
            self.assertGreater(expected, 0)
            self.assertTrue(353.15 <= T <= 371.15)
            self.assertEqual(row["porosity"], self.adapter["porosity_by_grind"][grind])

    def test_264_hash_bound_scenarios_and_hydraulic_identity(self):
        self.assertEqual(len(self.freeze["scenarios"]), 264)
        grouped = {}
        for row in self.freeze["scenarios"]:
            path = ROOT / row["scenario_path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["scenario_sha256"])
            s = json.loads(path.read_text())
            hydraulic = {"geometry": s["geometry"], "coffee_bed": s["coffee_bed"],
                         "liquid": s["liquid"], "hydraulics": s["hydraulics"],
                         "wetting": s["wetting"], "pressureBoundaryModel": s["pressureBoundaryModel"],
                         "flowResistanceModel": s["flowResistanceModel"], "bedMechanicsModel": s["bedMechanicsModel"]}
            numerical = {"axial_cells": hydraulic["geometry"].pop("axial_cells"),
                         "radial_cells": hydraulic["geometry"].pop("radial_cells"),
                         "delta_t_s": s["time"]["delta_t_s"]}
            grouped.setdefault(row["sample_id"], []).append((row["hypothesis"], row["resolution"], hydraulic, numerical))
        for records in grouped.values():
            first = records[0][2]
            self.assertTrue(all(item[2] == first for item in records))

    def test_66_hydraulic_runs_pass(self):
        with (OUT / "HYDRAULIC_QUALIFICATION.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 66)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))
        self.assertLessEqual(max(float(row["flow_relative_error"]) for row in rows), 1e-8)
        self.assertLessEqual(max(float(row["beverage_mass_absolute_error_kg"]) for row in rows), 1e-4)
        self.assertLessEqual(max(float(row["reference_fine_beverage_mass_relative"]) for row in rows), .0025)

    def test_no_target_path_or_target_value(self):
        for path in OUT.rglob("*"):
            if path.is_file():
                text = path.read_text(errors="ignore").casefold()
                self.assertNotIn("angeloni_targets_long", text)
                self.assertNotIn("protected_target", text)
        self.assertEqual(json.loads((OUT / "G1_FREEZE_MANIFEST.json").read_text())["target_open_count"], 0)


if __name__ == "__main__":
    unittest.main()
