from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import val_corpus_002_b0_tooling as b0


def synthetic_manifest(*, rate=.1, optimizer_status="PASS", **changes):
    log_k = math.log(rate)
    value = {
        "schema_version": "espresso.val_corpus_002.p2_calibration_manifest.v1",
        "status": b0.SYNTHETIC_CALIBRATION_STATUS, "record_class": "SYNTHETIC_B0_TEST_FIXTURE",
        "task": "VAL-CORPUS-002", "stage": "B1_CALIBRATION", "authorization_id": b0.AUTHORIZATION_ID,
        "calibration_case_id": b0.CALIBRATION_CASE_ID, "template_sha256": b0.EXP7_H1_TEMPLATE_SHA256,
        "source_cohort_path": b0.COHORT_PATH.as_posix(), "source_cohort_sha256": b0.COHORT_SHA256,
        "target_masses_g": b0.TARGET_MASSES_G, "source_observations_g": b0.SOURCE_SOLUTE_MASSES_G,
        "objective_identity": b0.OBJECTIVE_ID, "optimizer_algorithm": "GOLDEN_SECTION_LOG_K_V1",
        "log_k_bounds": [b0.LOG_K_LOWER, b0.LOG_K_UPPER],
        "log_k_interval_tolerance": b0.LOG_K_TOLERANCE, "maximum_evaluations": b0.MAX_EVALUATIONS,
        "optimizer_status": optimizer_status, "optimizer_trace_sha256": "1"*64,
        "selected_log_k": log_k, "selected_log_k_hex": log_k.hex(),
        "selected_rate_s_inverse": rate, "selected_rate_hex": rate.hex(), "selected_objective": .01,
        "solver_commit": "0a5c146078da5d5f88b344b20e7b81042bf27ddb",
        "executable_sha256": b0.REFERENCE["executable_sha256"],
        "calibration_configuration_sha256": "3"*64,
        "calibration_artifact_manifest_path": "synthetic/not-present.json",
        "calibration_artifact_manifest_sha256": "4"*64,
        "calibration_artifact_aggregate_sha256": "5"*64,
        "numerical_completion": "PASS", "conservation_disposition": "PASS",
    }
    value.update(changes); return value


def governed_fixture(root: Path, *, authorization_id="B1-TEST-AUTHORIZATION"):
    for relative in (b0.RUN_MATRIX, b0.SENSITIVITY_MATRIX):
        target=root/relative; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,target)
    cohort = root / b0.COHORT_PATH
    cohort.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / b0.COHORT_PATH, cohort)
    rate = .1; log_k = math.log(rate); objective = 0.0
    inventory = b0.build_configuration_inventory(ROOT)
    template = next(row for row in inventory["typed_p2_templates"]
                    if row["id"] == b0.CALIBRATION_CASE_ID)
    configuration = b0._materialize_p2_rate(template["template"], rate,
                                             b0.EXP7_H1_TEMPLATE_SHA256)
    artifacts = root / "runtime"; artifacts.mkdir()
    paths = {
        "OPTIMIZER_TRACE": artifacts / "optimizer.json",
        "CALIBRATION_CONFIGURATION": artifacts / "configuration.json",
        "CALIBRATION_REDUCTION": artifacts / "reduction.json",
        "RETAINED_MODEL_OUTPUT_TRACE": artifacts / "model-trace.json",
        "NUMERICAL_VERIFICATION": artifacts / "verification.json",
    }
    optimizer = {"status": "PASS", "evaluations": 42,
                 "final_log_interval_width": 9e-9,
                 "trace": [{"log_k": log_k, "log_k_hex": log_k.hex(),
                            "rate_s_inverse": rate, "rate_hex": rate.hex(),
                            "objective": objective,
                            "final_selection_status": "SELECTED_FINAL"}]}
    paths["OPTIMIZER_TRACE"].write_text(json.dumps(optimizer, sort_keys=True) + "\n")
    paths["CALIBRATION_CONFIGURATION"].write_bytes(b0.canonical_bytes(configuration))
    paths["CALIBRATION_REDUCTION"].write_text(json.dumps({
        "target_masses_g": b0.TARGET_MASSES_G,
        "model_cup_solute_masses_g": b0.SOURCE_SOLUTE_MASSES_G}, sort_keys=True) + "\n")
    paths["RETAINED_MODEL_OUTPUT_TRACE"].write_text("{}\n")
    paths["NUMERICAL_VERIFICATION"].write_text("{}\n")
    rows = [{"role": role, "path": path.relative_to(root).as_posix(),
             "bytes": path.stat().st_size, "sha256": b0.file_sha256(path)}
            for role, path in paths.items()]
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["path"]):
        digest.update(f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n".encode())
    artifact_record = {"schema_version": "espresso.val_corpus_002.calibration_artifacts.v1",
                       "aggregate_sha256": digest.hexdigest(), "files": rows}
    artifact_path = root / "runtime" / "artifact-manifest.json"
    artifact_path.write_text(json.dumps(artifact_record, sort_keys=True) + "\n")
    manifest = synthetic_manifest(
        status=b0.CALIBRATION_APPROVED_STATUS, record_class=b0.GOVERNED_RECORD_CLASS,
        authorization_id=authorization_id, selected_objective=objective,
        optimizer_trace_sha256=b0.file_sha256(paths["OPTIMIZER_TRACE"]),
        calibration_configuration_sha256=b0.canonical_sha256(configuration),
        calibration_artifact_manifest_path=artifact_path.relative_to(root).as_posix(),
        calibration_artifact_manifest_sha256=b0.file_sha256(artifact_path),
        calibration_artifact_aggregate_sha256=digest.hexdigest())
    return manifest, artifact_path, paths


def rewrite_artifact_manifest(manifest, artifact_path, mutate):
    record = json.loads(artifact_path.read_text())
    mutate(record)
    artifact_path.write_text(json.dumps(record, sort_keys=True) + "\n")
    manifest["calibration_artifact_manifest_sha256"] = b0.file_sha256(artifact_path)


def refresh_artifact_member(manifest, artifact_path, member_path, role):
    record=json.loads(artifact_path.read_text())
    row=next(row for row in record["files"] if row["role"]==role)
    row["bytes"]=member_path.stat().st_size; row["sha256"]=b0.file_sha256(member_path)
    digest=hashlib.sha256()
    for item in sorted(record["files"],key=lambda value:value["path"]):
        digest.update(f"{item['path']}\0{item['sha256']}\0{item['bytes']}\n".encode())
    record["aggregate_sha256"]=digest.hexdigest()
    artifact_path.write_text(json.dumps(record,sort_keys=True)+"\n")
    manifest["calibration_artifact_manifest_sha256"]=b0.file_sha256(artifact_path)
    manifest["calibration_artifact_aggregate_sha256"]=digest.hexdigest()
    if role=="OPTIMIZER_TRACE": manifest["optimizer_trace_sha256"]=row["sha256"]


class CalibrationAndConfigurationTests(unittest.TestCase):
    def test_calibration_manifest_schema_is_closed_and_complete(self):
        schema=b0.calibration_manifest_schema()
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]),b0.CALIBRATION_MANIFEST_KEYS)
        artifact_schema=b0.calibration_artifact_manifest_schema()
        self.assertFalse(artifact_schema["additionalProperties"])
        self.assertEqual(artifact_schema["properties"]["files"]["minItems"],5)

    def test_exact_source_vector_binding(self):
        binding = b0.bind_calibration_source(ROOT)
        self.assertEqual(binding["source_cohort_sha256"], b0.COHORT_SHA256)
        self.assertEqual(binding["target_masses_g"], [20., 40., 60.])
        self.assertEqual(binding["source_observations_g"], b0.SOURCE_SOLUTE_MASSES_G)

    def test_source_hash_and_record_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / b0.COHORT_PATH; path.parent.mkdir(parents=True)
            path.write_text("{}")
            with self.assertRaises(ValueError): b0.bind_calibration_source(root)

    def test_relative_mse_exact_and_zero_source_fails(self):
        self.assertAlmostEqual(b0.calibration_objective([1, 2, 4], [2, 2, 2]), (1 + 0 + .25)/3)
        for source in ([0, 1, 2], [-1, 1, 2], [math.nan, 1, 2]):
            with self.assertRaises(ValueError): b0.calibration_objective(source, [1, 1, 1])
        with self.assertRaises(ValueError): b0.calibration_objective([1, 2, 3], [1, -1, 3])

    def test_relative_mse_and_absolute_rmse_can_select_different_minima(self):
        source = [1., 100., 100.]
        candidates = {"small-relative": [1., 80., 80.], "small-absolute": [2., 99., 99.]}
        relative = min(candidates, key=lambda key: b0.calibration_objective(source, candidates[key]))
        absolute = min(candidates, key=lambda key: math.sqrt(sum((m-s)**2 for s,m in zip(source,candidates[key]))/3))
        self.assertEqual(relative, "small-relative"); self.assertEqual(absolute, "small-absolute")

    def test_inventory_and_manifest_bound_materialization_all_15(self):
        inventory = b0.build_configuration_inventory(ROOT)
        self.assertEqual(inventory["counts"]["final_production_identities"], 45)
        self.assertEqual(len(inventory["numeric_configurations"]), 30)
        result = b0.materialize_all_p2_synthetic(inventory, synthetic_manifest(), allow_synthetic=True)
        self.assertEqual(result["materialized_count"], 15)
        self.assertEqual(result["manifest_bound_rate_s_inverse"], .1)

    def test_raw_rate_and_malformed_manifest_refused(self):
        inventory = b0.build_configuration_inventory(ROOT); row = inventory["typed_p2_templates"][0]
        with self.assertRaises(TypeError): b0.materialize_p2(row["template"], .1, row["canonical_sha256"])
        with self.assertRaises(ValueError): b0.materialize_p2_synthetic(
            row["template"], {}, row["canonical_sha256"], allow_synthetic=True)
        with self.assertRaises(ValueError): b0.materialize_p2_synthetic(
            row["template"], synthetic_manifest(rate=2.0), row["canonical_sha256"],
            allow_synthetic=True)

    def test_wrong_manifest_identities_and_nonconvergence_refused(self):
        for change in ({"template_sha256":"f"*64}, {"source_cohort_sha256":"f"*64},
                       {"executable_sha256":"f"*64}, {"calibration_artifact_aggregate_sha256":"BAD"},
                       {"optimizer_status":"NONCONVERGED_EVALUATION_LIMIT"}):
            with self.assertRaises(ValueError):
                b0.validate_synthetic_calibration_manifest(synthetic_manifest(**change),
                    expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256, allow_synthetic=True)


class GovernedManifestContentTests(unittest.TestCase):
    def validate(self, manifest, root, authorization="B1-TEST-AUTHORIZATION"):
        return b0.validate_governed_calibration_manifest(
            manifest, expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256,
            root=root, expected_b1_authorization_id=authorization)

    def test_exact_status_record_class_pairing_and_synthetic_separation(self):
        with self.assertRaises(ValueError):
            b0.validate_synthetic_calibration_manifest(
                synthetic_manifest(status=b0.CALIBRATION_APPROVED_STATUS),
                expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256, allow_synthetic=True)
        with self.assertRaises(ValueError):
            b0.validate_synthetic_calibration_manifest(
                synthetic_manifest(record_class=b0.GOVERNED_RECORD_CLASS),
                expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256, allow_synthetic=True)
        with self.assertRaises(ValueError):
            b0.validate_synthetic_calibration_manifest(
                synthetic_manifest(), expected_template_sha256=b0.EXP7_H1_TEMPLATE_SHA256,
                allow_synthetic=False)
        barrier=b0.AccessBarrier(); barrier.authorize_b1("SEPARATE_HUMAN_OWNER_B1_AUTHORITY")
        with self.assertRaises(PermissionError):
            barrier.freeze_p2(synthetic_manifest(), root=ROOT,
                              expected_b1_authorization_id="B1-TEST-AUTHORIZATION")

    def test_governed_fixture_reconstructs_configuration_trace_and_objective(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, _, _=governed_fixture(root)
            self.assertEqual(self.validate(manifest, root), .1)
            inventory=b0.build_configuration_inventory(ROOT)
            result=b0.materialize_all_p2(inventory, manifest, root=root,
                expected_b1_authorization_id="B1-TEST-AUTHORIZATION")
            self.assertEqual(result["materialized_count"],15)
            self.assertTrue(result["identical_rate_all_templates"])

    def test_missing_root_wrong_authorization_and_unverified_bulk_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, _, _=governed_fixture(root)
            with self.assertRaises(ValueError): self.validate(manifest, None)
            with self.assertRaises(ValueError): self.validate(manifest, root, "WRONG-B1")
            inventory=b0.build_configuration_inventory(ROOT)
            with self.assertRaises(TypeError): b0.materialize_all_p2(inventory, manifest)

    def test_missing_symlinked_outside_and_wrong_artifact_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, artifact, _=governed_fixture(root)
            missing=copy.deepcopy(manifest); missing["calibration_artifact_manifest_path"]="runtime/missing.json"
            with self.assertRaises(ValueError): self.validate(missing, root)
            link=root/"runtime/link.json"; link.symlink_to(artifact)
            linked=copy.deepcopy(manifest); linked["calibration_artifact_manifest_path"]="runtime/link.json"
            with self.assertRaises(ValueError): self.validate(linked, root)
            outside=copy.deepcopy(manifest); outside["calibration_artifact_manifest_path"]="../outside.json"
            with self.assertRaises(ValueError): self.validate(outside, root)
            wrong=copy.deepcopy(manifest); wrong["calibration_artifact_manifest_sha256"]="f"*64
            with self.assertRaises(ValueError): self.validate(wrong, root)

    def test_wrong_aggregate_and_missing_optimizer_member_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, artifact, _=governed_fixture(root)
            wrong=copy.deepcopy(manifest); wrong["calibration_artifact_aggregate_sha256"]="f"*64
            with self.assertRaises(ValueError): self.validate(wrong, root)
            rewrite_artifact_manifest(manifest, artifact,
                lambda record: record.update(files=[row for row in record["files"]
                                                    if row["role"]!="OPTIMIZER_TRACE"]))
            with self.assertRaises(ValueError): self.validate(manifest, root)

    def test_optimizer_hash_and_final_selection_cardinality_rejected(self):
        for selection_count in (0,2):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory); manifest, artifact, paths=governed_fixture(root)
                if selection_count == 0:
                    optimizer=json.loads(paths["OPTIMIZER_TRACE"].read_text())
                    optimizer["trace"][0]["final_selection_status"]="NOT_FINAL"
                    paths["OPTIMIZER_TRACE"].write_text(json.dumps(optimizer,sort_keys=True)+"\n")
                else:
                    optimizer=json.loads(paths["OPTIMIZER_TRACE"].read_text())
                    optimizer["trace"].append(copy.deepcopy(optimizer["trace"][0]))
                    paths["OPTIMIZER_TRACE"].write_text(json.dumps(optimizer,sort_keys=True)+"\n")
                refresh_artifact_member(manifest,artifact,paths["OPTIMIZER_TRACE"],"OPTIMIZER_TRACE")
                with self.assertRaises(ValueError): self.validate(manifest,root)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, _, _=governed_fixture(root)
            manifest["optimizer_trace_sha256"]="f"*64
            with self.assertRaises(ValueError): self.validate(manifest,root)

    def test_selected_row_negative_objective_and_configuration_hash_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, artifact, paths=governed_fixture(root)
            optimizer=json.loads(paths["OPTIMIZER_TRACE"].read_text())
            optimizer["trace"][0]["objective"]=1.0
            paths["OPTIMIZER_TRACE"].write_text(json.dumps(optimizer,sort_keys=True)+"\n")
            refresh_artifact_member(manifest,artifact,paths["OPTIMIZER_TRACE"],"OPTIMIZER_TRACE")
            with self.assertRaises(ValueError): self.validate(manifest,root)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, _, _=governed_fixture(root)
            manifest["selected_objective"]=-1.0
            with self.assertRaises(ValueError): self.validate(manifest,root)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, _, _=governed_fixture(root)
            manifest["calibration_configuration_sha256"]="f"*64
            with self.assertRaises(ValueError): self.validate(manifest,root)

    def test_retained_model_vector_objective_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); manifest, artifact, paths=governed_fixture(root)
            paths["CALIBRATION_REDUCTION"].write_text(json.dumps({
                "target_masses_g":b0.TARGET_MASSES_G,
                "model_cup_solute_masses_g":[1.,1.,1.]},sort_keys=True)+"\n")
            record=json.loads(artifact.read_text())
            row=next(row for row in record["files"] if row["role"]=="CALIBRATION_REDUCTION")
            row["bytes"]=paths["CALIBRATION_REDUCTION"].stat().st_size
            row["sha256"]=b0.file_sha256(paths["CALIBRATION_REDUCTION"])
            digest=hashlib.sha256()
            for item in sorted(record["files"],key=lambda value:value["path"]):
                digest.update(f"{item['path']}\0{item['sha256']}\0{item['bytes']}\n".encode())
            record["aggregate_sha256"]=digest.hexdigest()
            artifact.write_text(json.dumps(record,sort_keys=True)+"\n")
            manifest["calibration_artifact_manifest_sha256"]=b0.file_sha256(artifact)
            manifest["calibration_artifact_aggregate_sha256"]=digest.hexdigest()
            with self.assertRaises(ValueError): self.validate(manifest,root)


class OptimizerTests(unittest.TestCase):
    def test_exact_bounds_log_sequence_and_stopping(self):
        result = b0.golden_section_log_k(lambda k: (math.log(k)-math.log(.2))**2)
        self.assertEqual(result["status"], "PASS")
        self.assertLessEqual(result["final_log_interval_width"], 1e-8)
        self.assertAlmostEqual(result["selected_rate_s_inverse"], .2, places=7)
        first = result["trace"][:2]
        self.assertLess(first[0]["log_k"], first[1]["log_k"])
        self.assertTrue(all(math.isclose(row["rate_s_inverse"], math.exp(row["log_k"]), rel_tol=1e-15)
                            for row in result["trace"]))
        self.assertTrue(all({"sequence","log_k","log_k_hex","rate_s_inverse","rate_hex","objective",
            "evaluation_status","failure_reason","cache_hit","active_log_lower","active_log_upper",
            "active_interior_log_low","active_interior_log_high","decision","final_selection_status"} <= row.keys()
                            for row in result["trace"]))
        self.assertEqual(sum(row["final_selection_status"] == "SELECTED_FINAL" for row in result["trace"]), 1)

    def test_boundaries_ties_failures_and_limit(self):
        self.assertEqual(b0.golden_section_log_k(lambda k:k)["selected_rate_s_inverse"], b0.K_LOWER)
        self.assertEqual(b0.golden_section_log_k(lambda k:1.)["selected_rate_s_inverse"], b0.K_LOWER)
        failed = b0.golden_section_log_k(lambda k: math.nan if k > .5 else (k-.2)**2)
        self.assertTrue(any(row["evaluation_status"] == "FAILED_EVALUATION" for row in failed["trace"]))
        limited = b0.golden_section_log_k(lambda k:(k-.2)**2, max_evaluations=2)
        self.assertEqual(limited["status"], "NONCONVERGED_EVALUATION_LIMIT")
        barrier = b0.AccessBarrier(); barrier.authorize_b1("SEPARATE_HUMAN_OWNER_B1_AUTHORITY")
        with self.assertRaises(PermissionError): barrier.freeze_p2(
            synthetic_manifest(optimizer_status="NONCONVERGED_EVALUATION_LIMIT"),
            root=ROOT, expected_b1_authorization_id="B1-TEST-AUTHORIZATION")


class ReferenceArtifactAndIntervalTests(unittest.TestCase):
    @staticmethod
    def row(time, scale=1.): return {f:(time if f=="time_s" else scale) for f in b0.PARITY_FIELDS}

    def test_reference_binding_and_full_1500_parity(self):
        review = ROOT.parent / ".wp03-002-exact-head-review"
        trace = review / "corrected-runs-v2/cases/WASZ-9-COMPACT/postProcessing/wholePull/0/traces.csv"
        if not trace.is_file(): self.skipTest("retained artifact absent in portable CI")
        binding = b0.bind_reference(ROOT, review); self.assertEqual(binding["trace_rows"], 1500)
        reference = b0._read_parity_csv(trace)
        self.assertEqual(b0.compare_bound_predecessor_parity(trace, reference)["compared_reference_states"], 1500)
        with self.assertRaises(ValueError): b0.compare_parity(reference[:-1], reference[:-1], required_reference_count=1500)

    def test_synthetic_parity_t0_extrapolation_and_subset_rejected(self):
        with self.assertRaises(ValueError): b0.compare_parity([self.row(0.)], [self.row(0.)])
        with self.assertRaises(ValueError): b0.compare_parity([self.row(.02)], [self.row(.03)])
        with self.assertRaises(ValueError): b0.compare_parity([self.row(.02)], [self.row(.02)], required_reference_count=1500)

    def test_raw_interval_mapping_clamp_failure_and_boundary(self):
        initial = {"simulation_start_time_s":0., "initial_cup_water_kg":0., "initial_cup_solute_kg":0.,
                   "initial_outlet_flow_m3_s":0., "initial_solute_flux_kg_s":0.}
        samples = [{"time_s":5., "outlet_flow_m3_s":2e-3, "totalSoluteFluxKgS":1.}]
        self.assertAlmostEqual(b0.interval_chemistry_raw(samples, 1000., 0., 5., initial), 1/3)
        tiny = [{"time_s":0., "outlet_flow_m3_s":-1e-19, "totalSoluteFluxKgS":-1e-16},
                {"time_s":5., "outlet_flow_m3_s":1e-3, "totalSoluteFluxKgS":1.}]
        self.assertGreater(b0.interval_chemistry_raw(tiny, 1000., 0., 5.), 0)
        bad = [{"time_s":0., "outlet_flow_m3_s":-1e-3, "totalSoluteFluxKgS":0.},
               {"time_s":5., "outlet_flow_m3_s":1e-3, "totalSoluteFluxKgS":1.}]
        with self.assertRaises(ValueError): b0.interval_chemistry_raw(bad, 1000., 0., 5.)
        with self.assertRaises(TypeError): b0.interval_chemistry([], 0, 5)

    def test_symlink_and_duplicate_alias_rejected_before_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); target=root/"target"; target.write_text("x"); link=root/"link"; link.symlink_to(target)
            with self.assertRaises(ValueError): b0.external_inventory(root,[link])
            alias=root/"sub"/".."/"target"
            with self.assertRaises(ValueError): b0.external_inventory(root,[target,alias])


class ReducerAndBarrierTests(unittest.TestCase):
    def test_schmieder_replicates_counts_zero_ratio_and_axes(self):
        reduced=b0.schmieder_three_mass_reduction([1,2,3],[1.1,2,2.8],[[.9,1.1],[1.9,2.1],[2.5,3.5]])
        self.assertEqual(reduced["replicate_statistics"][0]["count"],2)
        ratio=b0.paired_error_ratio(.2,0.); self.assertIsNone(ratio["ratio"])
        self.assertEqual(ratio["disposition"],"UNDEFINED_ZERO_DENOMINATOR_WITH_PAIRED_ERRORS_REPORTED")
        cases={"HIGH_FLOW":[2,3,4],"LOW_FLOW":[1,1,1],"COARSE_GRIND":[3,3,3],"FINE_GRIND":[1,2,3],
               "HIGH_TEMPERATURE":[4,5,6],"LOW_TEMPERATURE":[2,2,2]}
        contrasts=b0.all_axis_contrasts(cases); self.assertEqual(len(contrasts),3)

    def test_waszkiewicz_windows_uncertainty(self):
        result=b0.waszkiewicz_series_metrics([1,2,3,4,5,6],[2,2,2,5,5,5],
            {"early":[0,1],"middle":[2,3],"late":[4,5]},[.1,None,.2,None,.5,None])
        self.assertIn("rmse",result); self.assertEqual(set(result["window_mean_residual"]),{"early","middle","late"})
        self.assertEqual(result["uncertainty_weighted_secondary"]["count"],3)

    def test_complete_sensitivity_matrix_rank_correlations_and_species(self):
        cases={f"p{i}":{"low_parameter":1.,"high_parameter":2.,"low_outputs":[1.,1.,1.],
                         "high_outputs":[2.**(i+1),2.**(i+2),2.**(i+3)]} for i in range(4)}
        result=b0.sensitivity_matrix(cases); self.assertEqual(len(result["matrix"]),3)
        self.assertLessEqual(result["rank"],3); self.assertEqual(result["rank_ceiling"],3)
        self.assertEqual(len(result["parameter_correlations"]),4); self.assertTrue(result["equifinality_warning"])
        audit=b0.source_species_limitation_audit({"caffeine":[1,2]},[3,4]); self.assertFalse(audit["solver_predicted_named_species"])

    def test_exact_action_allowlist_and_b0_access(self):
        barrier=b0.AccessBarrier()
        with self.assertRaises(PermissionError): barrier.require_result_access(b0.CALIBRATION_CASE_ID)
        b0.AccessBarrier.validate_action("VERIFY_METADATA",b0.CALIBRATION_CASE_ID)
        for pair in (("LOAD_PROTECTED_FLOW",b0.CALIBRATION_CASE_ID),("VERIFY_METADATA","WASZ_9")):
            with self.assertRaises(PermissionError): b0.AccessBarrier.validate_action(*pair)


if __name__ == "__main__": unittest.main()
