import ast
import csv
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sci_lc_001a_protocol.py"
OUT = ROOT / "validation/cases/sci_lc_001a"
spec = importlib.util.spec_from_file_location("sci_lc_001a_protocol", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SciLc001aProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = mod.build_rows()
        cls.protocol = mod.protocol(cls.rows)
        mod.validate(cls.rows, cls.protocol)

    def test_human_machine_authority_agrees(self):
        text = (ROOT / "docs/analysis/sci_lc_001a/PROTOCOL.md").read_text()
        for value in (mod.TASK_ID, mod.STATUS, "NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE",
                      "LATERAL_EQUALIZATION", "HETEROGENEITY_PERSISTS",
                      "HETEROGENEITY_AMPLIFIES", "TRANSITION_OR_BISTABLE_REGION",
                      "C0", "S1", "S2", "S3", "D1", "D2", "D3-EQ", "D3-LOC",
                      "5,000", "15,000", "1,000", "20,000", "25,000"):
            self.assertIn(value, text)

    def test_generation_is_deterministic_and_ids_unique(self):
        again = mod.build_rows()
        self.assertEqual(self.rows, again)
        self.assertEqual(len(self.rows), len({r["case_id"] for r in self.rows}))

    def test_row_and_matrix_hashes(self):
        for row in self.rows:
            expected = mod.digest({k: row[k] for k in mod.FIELDS if k != "row_sha256"})
            self.assertEqual(row["row_sha256"], expected)
        expected = mod.digest([{k: r[k] for k in mod.FIELDS} for r in self.rows])
        self.assertEqual(self.protocol["matrix_summary"]["matrix_sha256"], expected)

    def test_committed_csv_json_semantically_equal(self):
        payload = json.loads((OUT / "SCI_LC_001A_PARAMETER_MATRIX.json").read_text())
        with (OUT / "SCI_LC_001A_PARAMETER_MATRIX.csv").open(newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        normalized = [{k: str(v) for k, v in row.items()} for row in payload["rows"]]
        self.assertEqual(csv_rows, normalized)
        self.assertEqual(payload["row_count"], len(payload["rows"]))

    def test_counts_are_generated_and_within_budget(self):
        summary = self.protocol["matrix_summary"]
        self.assertEqual(sum(summary["rows_by_arm"].values()), len(self.rows))
        budget = self.protocol["compute_budget"]
        self.assertLessEqual(budget["maximum_total_rows"], budget["absolute_protocol_ceiling"])
        self.assertLessEqual(budget["initial_static_control_rows"], 5000)
        self.assertLessEqual(budget["initial_dynamic_rows"], 15000)

    def test_invalid_combinations_absent(self):
        for row in self.rows:
            self.assertFalse(row["feedback_gain"] == "0" and row["feedback_sign"] != "NONE")
            if row["pressure_mode"].startswith("PRESCRIBED"):
                self.assertEqual(row["machine_response_ratio"], mod.NA)
            if row["heterogeneity_mode"].isdigit():
                self.assertLessEqual(int(row["heterogeneity_mode"]), row["sector_count"] // 2)
            self.assertNotEqual(row["arm"], "X1")

    def test_adaptive_arms_have_named_rules(self):
        rules = self.protocol["adaptive_rules"]
        self.assertIn("D4_LOG_MIDPOINT_V1", rules)
        self.assertIn("X1_SELECTED_HYDRAULIC_DIAGNOSTICS_V1", rules)
        self.assertEqual(self.protocol["matrix_summary"]["adaptive_placeholder_rows"], 0)

    def test_every_row_is_explicit_and_complete(self):
        for row in self.rows:
            self.assertEqual(set(row), set(mod.FIELDS))
            self.assertTrue(row["scientific_role"])
            self.assertTrue(row["units_or_dimensionless_status"])
            self.assertTrue(row["row_sha256"])
            self.assertNotIn(None, row.values())

    def test_uniform_and_zero_coupling_exact_identities(self):
        r = mod.conductance_matched_resistances([0.0] * 8, "1")
        self.assertEqual(r, [1.0] * 8)
        pressure = 2.0
        flows = [pressure / value for value in r]
        fractions = [q / sum(flows) for q in flows]
        self.assertEqual(fractions, [0.125] * 8)
        self.assertEqual(0.5 * sum(abs(f - 0.125) for f in fractions), 0.0)
        self.assertEqual(sum(0.0 * (i - ((i + 1) % 8)) for i in range(8)), 0.0)

    def test_rotation_preserves_scalar_conductance_identity(self):
        pattern = [math.cos(2 * math.pi * 2 * i / 8) for i in range(8)]
        a = mod.conductance_matched_resistances(pattern, "4")
        b = mod.conductance_matched_resistances(pattern[1:] + pattern[:1], "4")
        self.assertAlmostEqual(sum(1 / x for x in a), sum(1 / x for x in b), places=14)
        self.assertEqual(sorted(round(x, 14) for x in a), sorted(round(x, 14) for x in b))

    def test_scaled_ring_eigenvalue_converges(self):
        errors = [abs(mod.ring_eigenvalue(n, 1) - 1.0) for n in (8, 16, 32)]
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])

    def test_machine_reference_identity(self):
        ref_spec = importlib.util.spec_from_file_location(
            "machine", ROOT / "scripts/machine_coupling_reference.py")
        ref = importlib.util.module_from_spec(ref_spec)
        ref_spec.loader.exec_module(ref)
        args = dict(t=0.4, p0=0.0, outlet=0.0, compliance=2.0, q0=3.0,
                    shutoff=6.0, conductance=0.25)
        result = ref.continuous(**args)
        a = args["q0"] / args["shutoff"] + args["conductance"]
        expected = args["q0"] / a * (1 - math.exp(-args["t"] * a / args["compliance"]))
        self.assertAlmostEqual(result["pressure_Pa"], expected, places=14)

    def test_protocol_has_no_execution_import_or_classifier(self):
        tree = ast.parse(SCRIPT.read_text())
        imports = {node.names[0].name for node in ast.walk(tree)
                   if isinstance(node, ast.Import)}
        imports |= {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module}
        forbidden = ("Foam", "OpenFOAM", "puckworks", "subprocess")
        self.assertFalse(any(any(word.lower() in name.lower() for word in forbidden)
                             for name in imports))
        source = SCRIPT.read_text()
        self.assertNotIn("def integrate", source)
        self.assertNotIn("def classify", source)

    def test_pending_review_status_is_frozen(self):
        committed = json.loads((OUT / "SCI_LC_001A_PROTOCOL.json").read_text())
        self.assertEqual(committed["status"], mod.STATUS)
        self.assertNotIn("EXECUTION_AUTHORIZED", committed["status"])


if __name__ == "__main__":
    unittest.main()
