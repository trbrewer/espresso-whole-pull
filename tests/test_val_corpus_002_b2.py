import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import val_corpus_002_b0_tooling as b0
import val_corpus_002_b2 as b2
import val_corpus_002_b2_recovery as recovery
import val_corpus_002_b2_reporting as reporting


class StageB2ProspectiveTests(unittest.TestCase):
    def test_exact_fixed_rate(self):
        self.assertEqual(b2.RATE, 0.3439597024835067)
        self.assertEqual(b2.RATE.hex(), b2.RATE_HEX)

    def test_closed_inventory(self):
        inventory = b0.build_configuration_inventory(ROOT)
        self.assertEqual(inventory["counts"]["final_production_identities"], 45)
        self.assertEqual(inventory["counts"]["sensitivity_identities"], 9)

    def test_sensitivity_is_fixed_p1_h1_only(self):
        inventory = b0.build_configuration_inventory(ROOT)
        baseline = next(row["configuration"] for row in inventory["numeric_configurations"]
                        if row["id"] == "SCHM_EXP7_P1_H1")
        rows = json.loads((ROOT / b0.SENSITIVITY_MATRIX).read_text())["future_runs"]
        for row in rows:
            scenario = b2.sensitivity_scenario(ROOT, baseline, row)
            self.assertEqual(scenario["calibration"]["status"], "CLOSED_NO_REFIT")
            self.assertEqual(scenario["scenario_id"], row["run_id"])

    def test_raw_rate_has_no_entry_point(self):
        self.assertFalse(hasattr(b2, "calibrate"))
        self.assertFalse(hasattr(b2, "optimize"))

    def test_protected_or_refit_actions_absent(self):
        text = (ROOT / "scripts/val_corpus_002_b2.py").read_text()
        self.assertNotIn("historical_shape_scorer(", text)
        self.assertNotIn("golden_section_log_k(", text)

    def test_closed_matrix_driver_and_one_retry(self):
        text = (ROOT / "scripts/val_corpus_002_b2.py").read_text()
        self.assertIn("for attempt in (1, 2):", text)
        self.assertIn("production_planned\": 45", text)
        self.assertIn("sensitivity_planned\": 9", text)

    def test_b1_anchor_hash_is_immutable(self):
        self.assertEqual(b2.B1_MANIFEST_SHA256,
                         "554ce1c35979fa8961973b8cdd663a7a0ba817f6369667ea10808a06f644cbbc")

    def test_missing_target_is_typed_not_infrastructure(self):
        text = (ROOT / "scripts/val_corpus_002_b2.py").read_text()
        self.assertIn("REQUIRED_TARGET_BEVERAGE_MASS_NOT_REACHED_NO_EXTRAPOLATION", text)
        self.assertIn("raise b0.TypedNumericalEvaluationFailure", text)

    def test_refuses_reused_runtime_root(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(b2.InfrastructureFailure):
                b2.initialize(ROOT, Path(temp), Path(temp) / "missing", Path(temp))

    def test_structured_waszkiewicz_placeholder_collapses_to_scalar(self):
        inventory = b0.build_configuration_inventory(ROOT)
        row = next(row for row in inventory["typed_p2_templates"]
                   if row["id"] == recovery.WASZ_P2_ID)
        self.assertEqual(row["template"]["extraction"]["rate_constant_1_s"],
                         b0.TYPED_PLACEHOLDER)
        value = b0._materialize_p2_rate(row["template"], b2.RATE, row["canonical_sha256"])
        self.assertIs(type(value["extraction"]["rate_constant_1_s"]), float)
        self.assertEqual(value["extraction"]["rate_constant_1_s"].hex(), b2.RATE_HEX)
        self.assertNotIn(b0.PLACEHOLDER_TOKEN, json.dumps(value))
        self.assertNotIn("UNMATERIALIZED", json.dumps(value))
        self.assertNotIn("UNRESOLVED", json.dumps(value))

    def test_token_is_not_reverse_materialization_rate_key(self):
        value, count = b0._replace_numeric_rate({"token": b2.RATE}, b2.RATE)
        self.assertEqual(count, 0)
        self.assertEqual(value, {"token": b2.RATE})

    def test_nested_numeric_token_object_is_rejected(self):
        bad = {"extraction": {"rate_constant_1_s": {
            "status": "UNRESOLVED", "token": b2.RATE,
            "type": "CALIBRATED_SCALAR_S_INVERSE"}}}
        with self.assertRaises(ValueError):
            b0._materialize_p2_rate(bad, b2.RATE, b0.canonical_sha256(bad))

    def test_only_waszkiewicz_p2_hash_changes(self):
        old = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_CONFIGURATION_INVENTORY.json").read_text())
        inventory = b0.build_configuration_inventory(ROOT)
        new = {}
        for row in inventory["typed_p2_templates"]:
            value = b0._materialize_p2_rate(row["template"], b2.RATE, row["canonical_sha256"])
            new[row["id"]] = b0.canonical_sha256(value)
        changed = [key for key in new if new[key] != old["materialized_p2_configuration_sha256"][key]]
        self.assertEqual(changed, [recovery.WASZ_P2_ID])
        self.assertEqual(sum(key.startswith("SCHM_") for key in new), 14)

    def test_every_p2_template_has_one_semantic_rate_path(self):
        inventory = b0.build_configuration_inventory(ROOT)
        for row in inventory["typed_p2_templates"]:
            value = b0._materialize_p2_rate(row["template"], b2.RATE, row["canonical_sha256"])
            found = []
            for path in b0.APPROVED_RATE_PATHS:
                current = value
                for key in path:
                    if not isinstance(current, dict) or key not in current:
                        break
                    current = current[key]
                else:
                    found.append(current)
            self.assertEqual(found, [b2.RATE])

    def test_zero_or_multiple_semantic_rate_paths_fail(self):
        empty = {"chemistry": {"unrelated": b0.TYPED_PLACEHOLDER}}
        with self.assertRaises(ValueError):
            b0._materialize_p2_rate(empty, b2.RATE, b0.canonical_sha256(empty))
        duplicate = {"chemistry": {"extractionRateConstant_s_inverse": b0.TYPED_PLACEHOLDER},
                     "extraction": {"rate_constant_1_s": b0.TYPED_PLACEHOLDER}}
        with self.assertRaises(ValueError):
            b0._materialize_p2_rate(duplicate, b2.RATE, b0.canonical_sha256(duplicate))

    def test_non_scalar_and_nonfinite_rates_fail(self):
        for value in ({"value": b2.RATE}, [b2.RATE], "0.343", True, float("inf")):
            config = {"extraction": {"rate_constant_1_s": value}}
            with self.assertRaises(ValueError):
                b0._materialize_p2_rate(config, b2.RATE, b0.canonical_sha256(config))

    def test_corrected_inventory_preserves_declared_44(self):
        record = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_CORRECTED_CONFIGURATION_INVENTORY.json").read_text())
        self.assertEqual(record["unchanged_numeric_count"], 30)
        self.assertEqual(record["unchanged_schmieder_p2_count"], 14)
        self.assertEqual(record["changed_configuration_ids"], [recovery.WASZ_P2_ID])

    def test_typed_failures_remain_unavailable(self):
        result_path = ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json"
        if not result_path.exists():
            self.skipTest("final B2 result is generated after controlled execution")
        result = json.loads(result_path.read_text())
        failures = [row for row in result["availability_matrix"] if row["status"] == "TYPED_NUMERICAL_CASE_FAILURE"]
        self.assertEqual(len(failures), 18)
        self.assertTrue(all(row["unavailable_disposition"] ==
                            "UNAVAILABLE_TYPED_TARGET_COVERAGE_FAILURE" for row in failures))
        self.assertTrue(all(not any(row["target_availability"].values()) for row in failures))

    def test_result_keeps_protected_scoring_and_refit_outside_scope(self):
        text = (ROOT / "docs/validation/VAL_CORPUS_002_STAGE_B2_RESULT.md").read_text()
        self.assertIn("protected scoring was not performed", text)
        self.assertIn("Calibration is closed with no refit", text)

    def test_final_result_exact_inventory_and_dispositions(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        summary = json.loads((ROOT / result["records"]["per_case_numerical_summary"]["path"]).read_text())
        cases = summary["cases"]
        self.assertEqual(len(cases), 45)
        self.assertEqual(sum(row["status"] == "PASS" for row in cases), 27)
        failures = [row for row in cases if row["status"] == "TYPED_NUMERICAL_CASE_FAILURE"]
        self.assertEqual(len(failures), 18)
        self.assertTrue(all(row["typed_failure_reason"] == reporting.TARGET_FAILURE for row in failures))
        self.assertEqual(result["interpretation"]["scientific_result_disposition"], reporting.FINAL_SCIENTIFIC)
        self.assertEqual(result["interpretation"]["validation_framework_disposition"], reporting.FINAL_FRAMEWORK)
        self.assertNotEqual(result["interpretation"]["validation_framework_disposition"],
                            "SOURCE_SPECIFIC_AGGREGATE_CHEMISTRY_SUPPORT_WITH_LIMITATIONS")

    def test_hydraulic_coverage_and_axis_interpretation(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        interpreted = result["interpretation"]
        self.assertEqual(interpreted["h0_target_coverage"]["failure_count"], 18)
        self.assertEqual(interpreted["h1_target_coverage"]["pass"], 21)
        self.assertEqual(interpreted["p2_h1_axis_signs"], {
            "flow": {"matches": 3, "total": 3},
            "grind": {"matches": 0, "total": 3},
            "temperature": {"matches": 3, "total": 3}})

    def test_exact_waszkiewicz_interpretation(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())["interpretation"]["waszkiewicz"]
        self.assertEqual(value["fixed_plus_3_s"]["rmse"], 0.06682489539009928)
        self.assertEqual(value["source_clock"]["rmse"], 0.08603049216615972)
        self.assertEqual(value["fixed_plus_3_s"]["window_mean_residual"], {
            "early": -0.08072143166849205, "middle": 0.06597320745689621,
            "late": -0.0037413913634276215})

    def test_normalized_species_audit_is_complete(self):
        audit = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json").read_text())
        self.assertEqual(audit["replicate_triplets_per_component"], 24)
        self.assertEqual(len(audit["records"]), 96)
        means = {name: [audit["summary"][name][ratio]["mean"] for ratio in ("1/1", "1/2", "1/3")]
                 for name in ("TDS", "trigonelline", "5-CQA", "caffeine")}
        expected = {"TDS": [0.7080462873561918, 0.9300451013015908, 1.0],
                    "trigonelline": [0.7356657104905614, 0.9419107120748139, 1.0],
                    "5-CQA": [0.6599169162836315, 0.9071458316027874, 1.0],
                    "caffeine": [0.6338657391825547, 0.8929750022861945, 1.0]}
        for name in expected:
            for actual, target in zip(means[name], expected[name]):
                self.assertAlmostEqual(actual, target, places=15)

    def test_reduced_source_clock_grid_is_closed(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_REDUCED_SOURCE_CLOCK.json").read_text())
        self.assertEqual(len(value["rows"]), 21)
        self.assertTrue(all(len(row["targets"]) == 3 for row in value["rows"]))
        self.assertTrue(all(target["label"] == "DIAGNOSTIC_NOT_OPENFOAM_NOT_VALIDATION"
                            for row in value["rows"] for target in row["targets"]))

    def test_mandatory_summary_and_unavailable_operator(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json").read_text())
        self.assertEqual(value["reduction_status"], "PASS")
        self.assertEqual(value["production_matrix_disposition"],
                         "COMPLETE_WITH_18_TYPED_NUMERICAL_CASE_FAILURES")
        self.assertEqual(len(value["cases"]), 45)
        self.assertTrue(all(row["mean_outlet_flow_over_declared_intervals"] == reporting.UNAVAILABLE
                            and row["source_conditioned_hydraulic_residual"] == reporting.UNAVAILABLE
                            for row in value["cases"]))

    def test_deterministic_figure_manifest_and_repeatability(self):
        result_path = ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json"
        result = json.loads(result_path.read_text())
        summary = json.loads((ROOT / result["records"]["per_case_numerical_summary"]["path"]).read_text())
        value = {**result, "per_case_numerical_summary": summary}
        base = json.loads((ROOT / result["base_result_reference"]["path"]).read_text())
        script_sha = reporting.sha256(ROOT / "scripts/val_corpus_002_b2_reporting.py")
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            first = reporting.figures(value, base, Path(one), reporting.sha256(result_path), script_sha)
            second = reporting.figures(value, base, Path(two), reporting.sha256(result_path), script_sha)
            self.assertEqual([Path(one, Path(row["figure_path"]).name).read_bytes() for row in first["figures"]],
                             [Path(two, Path(row["figure_path"]).name).read_bytes() for row in second["figures"]])
            self.assertEqual(first["aggregate_sha256"], second["aggregate_sha256"])
        manifest = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FIGURE_MANIFEST.json").read_text())
        self.assertEqual(manifest["figure_count"], 5)
        for row in manifest["figures"]:
            self.assertEqual(reporting.sha256(ROOT / row["figure_path"]), row["figure_sha256"])
            svg = ET.fromstring((ROOT / row["figure_path"]).read_bytes())
            primitives = [node for node in svg.iter() if node.tag.rsplit("}", 1)[-1] in
                          {"line", "circle", "polyline", "polygon", "rect"}]
            self.assertGreater(len(primitives), 5)
            for node in primitives:
                for key in ("x", "x1", "x2", "cx"):
                    if key in node.attrib:
                        self.assertGreaterEqual(float(node.attrib[key]), 0.0)
                        self.assertLessEqual(float(node.attrib[key]), reporting.CANVAS_WIDTH)
                for key in ("y", "y1", "y2", "cy"):
                    if key in node.attrib:
                        self.assertGreaterEqual(float(node.attrib[key]), 0.0)
                        self.assertLessEqual(float(node.attrib[key]), reporting.CANVAS_HEIGHT)
                for point in node.attrib.get("points", "").split():
                    x, y = map(float, point.split(","))
                    self.assertTrue(0.0 <= x <= reporting.CANVAS_WIDTH and
                                    0.0 <= y <= reporting.CANVAS_HEIGHT)
            self.assertNotIn("timestamp", (ROOT / row["figure_path"]).read_text().lower())

    def test_figure_semantics_and_required_labels_are_closed(self):
        figures = ROOT / "validation/cases/val_corpus_002/figures"
        source = (figures / "schmieder_h1_source_model.svg").read_text()
        for experiment in range(1, 8):
            self.assertIn(f"Experiment {experiment}", source)
        for label in ("source", "model P0", "model P1", "model P2", "20", "40", "60",
                      "calibration reconstruction anchor", "post-fit derived", "not independent"):
            self.assertIn(label, source)

        contrasts = (figures / "schmieder_h1_axis_contrasts.svg").read_text()
        for label in ("P1 — Flow: high − low", "P1 — Grind: coarse − fine",
                      "P1 — Temperature: high − low", "P2 — Flow: high − low",
                      "P2 — Grind: coarse − fine", "P2 — Temperature: high − low",
                      "1:1", "1:2", "1:3", "post-fit derived", "not independent"):
            self.assertIn(label, contrasts)

        wasz = (figures / "waszkiewicz_both_clocks.svg").read_text()
        for label in ("Source-reported clock", "Frozen +3 s offset", "0.00", "0.14", "0.28",
                      "5-second interval index", "No optimized shift", "not validation"):
            self.assertIn(label, wasz)

        sensitivity = (figures / "sensitivity_matrix_and_singular_values.svg").read_text()
        base = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_RESULT.json").read_text())
        for label in reporting.SENSITIVITY_OUTPUT_LABELS + tuple(base["sensitivity"]["parameters"]):
            self.assertIn(label, sensitivity)
        for value in base["sensitivity"]["singular_values"]:
            self.assertIn(repr(value), sensitivity)
        for label in ("matrix rank = 3", "NOT_STRUCTURAL_IDENTIFIABILITY",
                      "not structural-identifiability proof", "Signed elasticity key"):
            self.assertIn(label, sensitivity)

    def test_figure_plot_geometry_is_inside_declared_panels_and_bands_do_not_overlap(self):
        figures = ROOT / "validation/cases/val_corpus_002/figures"
        for path in sorted(figures.glob("*.svg")):
            svg = ET.fromstring(path.read_bytes())
            panels = {node.attrib["data-panel"]: tuple(float(node.attrib[key]) for key in
                      ("data-plot-x", "data-plot-y", "data-plot-width", "data-plot-height"))
                      for node in svg.iter() if "data-panel" in node.attrib}
            bands = sorted((float(node.attrib["data-y"]), float(node.attrib["data-y"]) +
                            float(node.attrib["data-height"]), node.attrib["data-band"])
                           for node in svg.iter() if "data-band" in node.attrib)
            for (_, end, left), (start, _, right) in zip(bands, bands[1:]):
                self.assertLessEqual(end, start, f"overlapping {left}/{right} in {path.name}")
            for node in svg.iter():
                if node.attrib.get("data-role") != "data":
                    continue
                x, y, width, height = panels[node.attrib["data-panel-ref"]]
                points = []
                tag = node.tag.rsplit("}", 1)[-1]
                if tag == "line":
                    points = [(float(node.attrib["x1"]), float(node.attrib["y1"])),
                              (float(node.attrib["x2"]), float(node.attrib["y2"]))]
                elif tag in ("polyline", "polygon"):
                    points = [tuple(map(float, item.split(","))) for item in node.attrib["points"].split()]
                elif tag == "circle":
                    cx, cy, radius = map(float, (node.attrib["cx"], node.attrib["cy"], node.attrib["r"]))
                    points = [(cx-radius, cy-radius), (cx+radius, cy+radius)]
                elif tag == "rect":
                    rx, ry, rw, rh = map(float, (node.attrib["x"], node.attrib["y"],
                                                node.attrib["width"], node.attrib["height"]))
                    points = [(rx, ry), (rx+rw, ry+rh)]
                for px, py in points:
                    self.assertTrue(x - 1e-6 <= px <= x + width + 1e-6, (path.name, tag, px, x, width))
                    self.assertTrue(y - 1e-6 <= py <= y + height + 1e-6, (path.name, tag, py, y, height))

    def test_production_figure_maps_all_governed_run_ids_once(self):
        path = ROOT / "validation/cases/val_corpus_002/figures/production_availability_matrix.svg"
        svg = ET.fromstring(path.read_bytes())
        figure_ids = [node.attrib["data-run-id"] for node in svg.iter() if "data-run-id" in node.attrib]
        summary = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json").read_text())
        governed = [row["run_id"] for row in summary["cases"]]
        self.assertEqual(len(figure_ids), 45)
        self.assertEqual(len(set(figure_ids)), 45)
        self.assertEqual(set(figure_ids), set(governed))

    def test_claim_and_execution_boundaries_unchanged(self):
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        self.assertEqual(result["base_result_reference"]["sha256"], reporting.BASE_RESULT_SHA256)
        base = json.loads((ROOT / result["base_result_reference"]["path"]).read_text())
        self.assertEqual(base["claim_ceiling"]["physical_validation"], "NOT_ESTABLISHED")
        self.assertEqual(result["bundle_status"], "RESULT_COMPLETE_WITH_TYPED_FAILURES")
        self.assertEqual(result["reduction_status"], "PASS")
        self.assertEqual(result["openfoam_rerun"], "NOT_PERFORMED")
        self.assertEqual(result["sensitivity_rerun"], "NOT_PERFORMED")
        self.assertEqual(result["calibration"], "CLOSED_NO_REFIT")
        self.assertEqual(result["protected_scoring"], "NOT_PERFORMED")
        self.assertEqual(result["new_governing_physics"], "NOT_AUTHORIZED")

    def test_final_report_manifest_hash_consistency(self):
        manifest = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_REPORT_MANIFEST.json").read_text())
        for member in manifest["members"].values():
            self.assertEqual(reporting.sha256(ROOT / member["path"]), member["sha256"])
        self.assertEqual(manifest["immutable_inputs"]["base_b2_result_sha256"],
                         reporting.BASE_RESULT_SHA256)

    def test_final_result_closed_schema_and_semantics(self):
        schema = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT_SCHEMA.json").read_text())
        result = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(result), set(schema["required"]))
        self.assertEqual(set(schema["properties"]), set(schema["required"]))
        self.assertEqual(reporting.validate_final_package(ROOT)["status"], "PASS")
        for mutation in (
            lambda value: value.update({"bundle_status": "PASS"}),
            lambda value: value.update({"production_matrix_disposition": "PASS"}),
            lambda value: value.update({"authoritative_interpretation": "HISTORICAL_BASE_RESULT"}),
            lambda value: value["interpretation"].clear(),
            lambda value: value["source_lineage"].pop("required_citation"),
            lambda value: value["production_counts"].update({"pass": 45}),
            lambda value: value.update({"extra": "rejected"}),
        ):
            altered = copy.deepcopy(result)
            mutation(altered)
            with self.assertRaises(Exception):
                reporting.validate_final_package(ROOT, altered)

    def test_target_bracketing_is_distinct_from_governed_availability(self):
        value = json.loads((ROOT / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json").read_text())
        row = next(item for item in value["cases"] if item["run_id"] == "SCHM_EXP1_P0_H0")
        self.assertEqual(row["numerical_target_bracketing"], {
            "20_g": "PASS", "40_g": "FAIL_NO_EXTRAPOLATION", "60_g": "FAIL_NO_EXTRAPOLATION"})
        self.assertEqual(row["governed_case_metric_availability"], {
            "20_g": False, "40_g": False, "60_g": False})
        self.assertEqual(row["governed_case_reason"],
                         "COMPLETE_20_40_60_VECTOR_REQUIRED_CASE_TYPED_FAILURE")

    def test_cup_mass_lineage_caveat_is_complete(self):
        required = reporting.LINEAGE
        paths = [
            "validation/cases/val_corpus_002/VAL_CORPUS_002_COHORT_SELECTION_LINEAGE_BINDING.json",
            "validation/cases/val_corpus_002/VAL_CORPUS_002_CALIBRATION_COMPARISON_LEDGER.json",
            "validation/cases/val_corpus_002/VAL_CORPUS_002_EXP7_H1_CALIBRATION_SOURCE_BINDING.json",
            "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_FINAL_RESULT.json",
            "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_NORMALIZED_SPECIES_AUDIT.json",
            "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_PER_CASE_NUMERICAL_SUMMARY.json",
        ]
        for relative in paths:
            text = (ROOT / relative).read_text()
            for key, expected in required.items():
                self.assertIn(f'"{key}"', text, relative)
                if isinstance(expected, str):
                    self.assertIn(expected, text, relative)
        for name in ("schmieder_h1_source_model.svg", "schmieder_h1_axis_contrasts.svg"):
            self.assertIn("post-fit derived", (ROOT / "validation/cases/val_corpus_002/figures" / name).read_text())

    def test_every_governed_cup_mass_reference_carries_lineage(self):
        required = {key: reporting.LINEAGE[key] for key in
                    ("evidence_class", "independent_measurement", "allowed_use",
                     "prohibited_use", "required_citation")}
        found = []
        for path in (ROOT / "validation").rglob("*.json"):
            if "cup_masses.csv" not in path.read_text():
                continue
            value = json.loads(path.read_text())
            stack = [value]
            while stack:
                current = stack.pop()
                if isinstance(current, dict):
                    if any(isinstance(item, str) and item.endswith("cup_masses.csv")
                           for item in current.values()):
                        lineage = current.get("source_lineage", current)
                        self.assertTrue(all(lineage.get(k) == v for k, v in required.items()), path)
                        found.append(path)
                    stack.extend(current.values())
                elif isinstance(current, list):
                    stack.extend(current)
        self.assertGreaterEqual(len(set(found)), 3)

    def test_imported_base_cross_validation_identity_and_metrics(self):
        external = ROOT / "validation/external/puckworks_base_temporal_cv"
        record = json.loads((external / "PUCKWORKS_BASE_TEMPORAL_CV_SOURCE_RECORD.json").read_text())
        self.assertEqual(record["upstream_commit"], "21869fe19feec2dce6af8f4a41f63299473e31c2")
        for member in record["artifacts"]:
            self.assertEqual(reporting.sha256(ROOT / member["local_path"]), member["local_sha256"])
            self.assertEqual(member["upstream_sha256"], member["local_sha256"])
            self.assertTrue(member["byte_identity"])
        model = json.loads((external / "PAPER_A_TEMPORAL_MODEL_COMPARISON_V1.json").read_text())
        expected = {
            "caffeine": (6.773723008023561, 9.956192697201004, 1.5553653242809058, 2.2230231547476897),
            "trigonelline": (10.298791345087212, 15.158854455498721, -3.4686832418065188, 3.1662156395611976),
            "5CQA": (7.196408617674486, 10.016456716398794, 1.3445947506081093, 2.8110375983062417),
        }
        for solute, values in expected.items():
            base = model["solutes"][solute]["BASE"]
            self.assertEqual((base["all_fraction_mape"], base["late_fraction_mape"],
                              base["late_signed_pct"], base["derived_cumulative_mape"]), values)
            self.assertEqual(base["n_folds"], 5)
            self.assertEqual(base["failed_fits"], 0)
        self.assertEqual(record["matched_data"]["shot_count"], 16)
        self.assertEqual(record["matched_data"]["excluded_shot_count"], 3)


if __name__ == "__main__":
    unittest.main()
