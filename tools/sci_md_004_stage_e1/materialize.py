#!/usr/bin/env python3
"""Fail-closed Stage E1 materialization and blocked-result writer.

This entry point has no target argument, target loader, scorer import, or
solver-execution path. It decides only whether the frozen hydraulic contract
can be represented by the unchanged production scenario interface.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED = {
    "validation/sci_md_004_stage_e0/FREEZE_MANIFEST.json":
        "997057ac8ec9baaba9d96790b5e2d72cce2d57c76e5ad0b4fcddff3eaad16933",
    "validation/sci_md_004_stage_e0/BLOCKED_WHOLE_EXPERIMENT_CV.csv":
        "8d3c5f4b725351e915a6ce56a7591bc709e8f59e2459dd14b25fc1258251f48a",
    "validation/sci_md_004_stage_e0/COMMON_H0_H1_OBSERVATION_OPERATOR.json":
        "4d2e5347ca876553443d9ba5629b6095679a33a9f4794bed98ea8cc3c63d76fd",
    "validation/sci_md_004_stage_e0/CONDITIONAL_CASE_FREEZE.json":
        "d969d00295443b2861a9f0107c2536ef5283f9e580a1f3fb56a8c2252df47626",
    "validation/sci_md_004_stage_e0/NUMERICAL_APPLICATION_QUALIFICATION.json":
        "e9ffc2f907e5ca3d31e47fdc3c865f8cd63c4fda509d687318979786652b0385",
    "validation/sci_md_004_stage_e0/PARAMETERIZATION_AND_IDENTIFIABILITY.json":
        "ec30b7e0038e092c9b8e0d8e3d5d47de35be4e1afdbc650f826ac72f17e1b051",
    "docs/governance/MINIMUM_NECESSARY_GOVERNANCE_STANDARD.md":
        "58c33923f02ca733d611ddc41173fce0e2f33a20d2908312b572f57822edc364",
    "solver/espressoWholePullFoam/espressoWholePullFoam.C":
        "9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599",
}
RESULT = "SCI_MD_004_STAGE_E1_EXECUTION_CONTRACT_BLOCKED_BEFORE_TARGET_ACCESS"
EXECUTABLE_SHA256 = "d793a731fd2f4f82e623350c61835d0e955d886849f5e363a5abd8dd0fae4c93"
PREDICTION_FIELDS = (
    "sample_id", "variety", "hypothesis", "species_or_aggregate",
    "reference_prediction_kg_m3", "fine_prediction_kg_m3",
    "primary_prediction_kg_m3", "reference_fine_relative_difference",
    "initial_inventory_kg", "cup_mass_kg", "conservation_residual_kg",
    "reference_scenario_sha256", "fine_scenario_sha256",
    "reference_trace_sha256", "fine_trace_sha256",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_empty_csv(path: Path, fields: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=fields, lineterminator="\n").writeheader()


def production_boundary_capabilities(source: str, materializer: str) -> dict[str, Any]:
    modes = [
        mode for mode in ("prescribedPressure", "lumpedMachineCompliance")
        if mode in source and mode in materializer
    ]
    flow_tokens = ("prescribedFlow", "prescribedOutletFlow", "targetOutletMassFlow")
    return {
        "supported_pressure_boundary_models": modes,
        "prescribed_outlet_flow_control": any(token in source or token in materializer for token in flow_tokens),
        "targetBeverageMass_role": "DIAGNOSTIC_EVENT_NOT_FLOW_BOUNDARY",
    }


def build(root: Path, output: Path) -> int:
    observed = {name: sha256(root / name) for name in EXPECTED}
    if observed != EXPECTED:
        raise SystemExit(f"accepted authority mismatch: {observed!r}")
    freeze = load(root / "validation/sci_md_004_stage_e0/CONDITIONAL_CASE_FREEZE.json")
    parameters = load(root / "validation/sci_md_004_stage_e0/PARAMETERIZATION_AND_IDENTIFIABILITY.json")
    if parameters["parameter_count_fitted"] != 4:
        raise SystemExit("fitted parameter count changed")
    cases = freeze["cases"]
    if len(cases) != 66:
        raise SystemExit("case count changed")
    production_source = (root / "solver/espressoWholePullFoam/espressoWholePullFoam.C").read_text()
    materializer_source = (root / "scripts/prepare_case.py").read_text()
    capabilities = production_boundary_capabilities(production_source, materializer_source)
    intents = []
    for case in cases:
        hydraulic = case["hydraulics"]
        if hydraulic["permeability_fit"] is not None:
            raise SystemExit("frozen case unexpectedly contains permeability fit")
        for frozen in case["configurations"]:
            intents.append({
                "configuration_id": frozen["configuration_id"],
                "sample_id": case["sample_id"],
                "hypothesis": frozen["hypothesis"],
                "resolution": frozen["resolution"],
                "pressure_Pa": hydraulic["pressure_Pa"],
                "temperature_K": hydraulic["temperature_K"],
                "shot_duration_s": hydraulic["shot_duration_s"],
                "conditional_outlet_mass_flow_kg_s":
                    hydraulic["conditional_outlet_mass_flow_kg_s"],
                "permeability_fit": None,
                "materialization_status": "BLOCKED_UNREPRESENTABLE_HYDRAULIC_CONTROL",
                "scenario_path": None,
                "scenario_sha256": None,
                "solver_execution_count": 0,
            })
    if len(intents) != 264:
        raise SystemExit("configuration count changed")
    blocker = (
        "The frozen conditional_outlet_mass_flow_kg_s is a mandatory hydraulic "
        "input, but the accepted production interface exposes no prescribed-flow "
        "boundary. prescribedPressure predicts flow from permeability; "
        "lumpedMachineCompliance requires a new machine model. Using inherited "
        "template permeability would ignore the frozen conditional flow, while "
        "fitting permeability or adding a flow boundary is explicitly prohibited."
    )
    representable = capabilities["prescribed_outlet_flow_control"]
    if representable:
        raise SystemExit("unexpected flow control appeared; this blocker writer must be reviewed")
    output.mkdir(parents=True, exist_ok=True)
    materialized = {
        "schema_version": "ewp.sci-md-004-stage-e1-materialization/v1",
        "governance_class": "G3_PROTECTED_HOLDOUT_PREDICTION_AND_SCORING",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "accepted_executable_sha256": EXECUTABLE_SHA256,
        "requested_configuration_count": 264,
        "complete_executable_scenario_count": 0,
        "solver_execution_count": 0,
        "semantic_protected_target_access_count": 0,
        "capabilities": capabilities,
        "blocker": blocker,
        "configuration_intents": intents,
        "disposition": RESULT,
    }
    write_json(output / "MATERIALIZED_CASE_MANIFEST.json", materialized)
    write_empty_csv(output / "PREDICTIONS.csv", PREDICTION_FIELDS)
    write_empty_csv(output / "NUMERICAL_STABILITY.csv", (
        "sample_id", "hypothesis", "observable", "reference", "fine",
        "relative_difference", "status",
    ))
    write_empty_csv(output / "CONDITION_LEVEL_RESULTS.csv", (
        "sample_id", "hypothesis", "observable", "prediction", "observation",
        "signed_error", "absolute_error", "relative_error", "squared_error",
    ))
    write_json(output / "PREDICTION_MANIFEST.json", {
        "state": "NOT_CREATED_EXECUTION_CONTRACT_BLOCKED",
        "prediction_count": 0,
        "prediction_freeze_commit": None,
        "prediction_freeze_tree": None,
        "semantic_protected_target_access_count": 0,
    })
    write_json(output / "DIRECTIONAL_PAIR_MANIFEST.json", {
        "state": "NOT_CREATED_EXECUTION_CONTRACT_BLOCKED",
        "pair_count": 0,
        "target_derived": False,
    })
    write_json(output / "SCORER_INVOCATION_RECEIPT.json", {
        "state": "NOT_INVOKED_PRE_TARGET_EXECUTION_CONTRACT_BLOCK",
        "scorer_process_count": 0,
        "protected_target_scorer_open_count": 0,
        "semantic_protected_target_access_count": 0,
        "preflight_silent_integrity_hash_reads": 1,
        "preflight_integrity_read_materiality":
            "NONSEMANTIC_HASH_ONLY_REQUIRED_BY_AUTHORIZATION_SECTION_C",
    })
    not_computed = {
        "state": "NOT_COMPUTED_EXECUTION_CONTRACT_BLOCKED",
        "reason": RESULT,
    }
    write_json(output / "SPECIES_METRICS.json", not_computed)
    write_json(output / "TOTAL_SOLIDS_METRICS.json", not_computed)
    write_json(output / "FINAL_SCIENTIFIC_RESULT.json", {
        "schema_version": "ewp.sci-md-004-stage-e1-result/v1",
        "authorization":
            "SCI-MD-004-STAGE-E1-OWNER-AUTHORIZATION-SINGLE-PROTECTED-HOLDOUT-"
            "PREDICTION-NUMERICAL-FREEZE-ONE-SCORER-INVOCATION-AND-FINAL-"
            "SCIENTIFIC-DISPOSITION-2026-08-24",
        "governance_class": "G3_PROTECTED_HOLDOUT_PREDICTION_AND_SCORING",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "primary_scientific_result": RESULT,
        "prediction_execution_count": 0,
        "protected_scorer_process_count": 0,
        "semantic_protected_target_access_count": 0,
        "post_holdout_retuning_count": 0,
        "production_solver_changed": False,
        "physical_validation": "NOT_ESTABLISHED",
        "blocker": blocker,
    })
    artifacts = sorted(path for path in output.iterdir() if path.name != "RESULT_MANIFEST.json")
    write_json(output / "RESULT_MANIFEST.json", {
        "schema_version": "ewp.sci-md-004-stage-e1-result-manifest/v1",
        "accepted_ewp_base_commit": "c50c9a6ab122f3668372c7801c004f5fdc27beca",
        "accepted_ewp_base_tree": "c1b66d5a1546fb33dbb3e2fb633a49b6412a9178",
        "accepted_puckworks_commit": "5ce003e751aac516b5de3d9ede4e6910627e2b12",
        "accepted_puckworks_tree": "d50c23028df01d6e1dc0a14ab331d0ea7453cb7f",
        "accepted_executable_sha256": EXECUTABLE_SHA256,
        "authority_hashes": observed,
        "artifact_hashes": {path.name: sha256(path) for path in artifacts},
        "primary_scientific_result": RESULT,
        "prediction_count": 0,
        "solver_execution_count": 0,
        "protected_scorer_process_count": 0,
        "semantic_protected_target_access_count": 0,
    })
    return 3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return build(args.root.resolve(), args.output.resolve())
