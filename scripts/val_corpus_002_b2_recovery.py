#!/usr/bin/env python3
"""Closed Stage-B2 materialization recovery, cache verification and execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import val_corpus_002_b0_tooling as b0
import val_corpus_002_b1_calibration as b1
import val_corpus_002_b2 as b2


RECOVERY_SOURCE_HEAD = "8979d8b4b4bea5d119695e4685556f9d2909da61"
ORIGINAL_PARTIAL_AGGREGATE = "db510fb5b0431152b39a7513d99cf2604702573948fe3f2f3d326bb4bfade999"
ORIGINAL_PRODUCTION_AGGREGATE = "21e16604072de4b4b5e86561f41b0fd5a28c1c4c486b1e4964b6ef8844279c47"
ORIGINAL_WASZ_P2_HASH = "7e7a8977cc45641c6e22b90922a5b370e9e0e81179ad0e1022c371c863c79dbc"
WASZ_P2_ID = "WASZ_9_COMPACT_P2_FIXED_AFTER_EXP7_CALIBRATION_CHEMISTRY"
TARGET_FAILURE = "REQUIRED_TARGET_BEVERAGE_MASS_NOT_REACHED_NO_EXTRAPOLATION"


def _dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def configuration_maps(repo: Path, b1_root: Path) -> tuple[dict[str, dict], dict]:
    _, materialized = b2.verify_b1(repo, b1_root)
    inventory = b0.build_configuration_inventory(repo)
    configs = {row["id"]: row["configuration"] for row in inventory["numeric_configurations"]}
    configs.update(materialized["configurations"])
    hashes = {key: b0.canonical_sha256(value) for key, value in configs.items()}
    return configs, hashes


def corrected_inventory(repo: Path, b1_root: Path, old_path: Path) -> dict:
    old = json.loads(old_path.read_text())
    configs, hashes = configuration_maps(repo, b1_root)
    old_hashes = {**old["numeric_configuration_sha256"],
                  **old["materialized_p2_configuration_sha256"]}
    changed = sorted(key for key in hashes if hashes[key] != old_hashes[key])
    if changed != [WASZ_P2_ID]:
        raise ValueError(f"correction changed members outside Waszkiewicz P2: {changed}")
    if old_hashes[WASZ_P2_ID] != ORIGINAL_WASZ_P2_HASH:
        raise ValueError("superseded Waszkiewicz P2 identity mismatch")
    digest = hashlib.sha256()
    for key in sorted(hashes):
        digest.update(f"{key}\0{hashes[key]}\n".encode())
    value = {
        "schema_version": "espresso.val_corpus_002.b2_corrected_configuration_inventory.v1",
        "authorization_id": b2.AUTHORIZATION_ID,
        "fixed_rate_s_inverse": b2.RATE, "fixed_rate_hex": b2.RATE_HEX,
        "supersedes_inventory_sha256": b0.file_sha256(old_path),
        "superseded_production_aggregate_sha256": ORIGINAL_PRODUCTION_AGGREGATE,
        "corrected_production_aggregate_sha256": digest.hexdigest(),
        "superseded_waszkiewicz_p2_sha256": ORIGINAL_WASZ_P2_HASH,
        "corrected_waszkiewicz_p2_sha256": hashes[WASZ_P2_ID],
        "unchanged_numeric_count": 30, "unchanged_schmieder_p2_count": 14,
        "changed_configuration_ids": changed,
        "numeric_configuration_sha256": {key: hashes[key] for key in old["numeric_configuration_sha256"]},
        "materialized_p2_configuration_sha256": {
            key: hashes[key] for key in old["materialized_p2_configuration_sha256"]},
        "waszkiewicz_p2_rate_is_scalar": type(configs[WASZ_P2_ID]["extraction"]["rate_constant_1_s"]) is float,
        "historical_inventory": "RETAINED_IMMUTABLE",
    }
    if configs[WASZ_P2_ID]["extraction"]["rate_constant_1_s"].hex() != b2.RATE_HEX:
        raise ValueError("corrected Waszkiewicz rate identity mismatch")
    return value


def preflight_all_p2(repo: Path, b1_root: Path, output_root: Path) -> dict:
    configs, _ = configuration_maps(repo, b1_root)
    p2_ids = sorted(key for key in configs if "_P2_FIXED_" in key)
    if len(p2_ids) != 15:
        raise ValueError("exact 15-member P2 preflight required")
    output_root.mkdir(parents=True, exist_ok=False)
    rows = []
    for run_id in p2_ids:
        config = configs[run_id]
        rate_path = (config["chemistry"]["extractionRateConstant_s_inverse"]
                     if run_id.startswith("SCHM_") else config["extraction"]["rate_constant_1_s"])
        if type(rate_path) is not float or rate_path.hex() != b2.RATE_HEX:
            raise ValueError(f"non-scalar or wrong P2 rate: {run_id}")
        scenario = b2.solver_scenario(repo, config)
        member = output_root / run_id
        scenario_path = member / "solver-scenario.json"
        b2._dump(scenario_path, scenario, canonical=True)
        case = member / "temporary-case"
        subprocess.run([sys.executable, str(repo / "scripts/prepare_case.py"), "--root", str(repo),
                        "--config", str(scenario_path), "--case-dir", str(case), "--nprocs", "16"],
                       check=True, stdout=subprocess.DEVNULL)
        properties = case / "constant/espressoModelProperties"
        line = next(line.strip() for line in properties.read_text().splitlines()
                    if line.strip().startswith("extractionRateConstant"))
        if line != "extractionRateConstant     0.3439597024835067;":
            raise ValueError(f"generated scalar extraction rate mismatch: {run_id}")
        manifest = case / "ESPRESSO_WHOLE_PULL_CASE_CASE_MANIFEST_V0_1_4.json"
        rows.append({"run_id": run_id, "configuration_sha256": b0.canonical_sha256(config),
                     "scenario_sha256": b0.file_sha256(scenario_path),
                     "prepare_case": "PASS", "extraction_rate_type": "SCALAR",
                     "extraction_rate_s_inverse": rate_path,
                     "case_manifest_sha256": b0.file_sha256(manifest)})
        shutil.rmtree(case)
    digest = hashlib.sha256()
    for row in rows:
        digest.update(b0.canonical_bytes(row))
    result = {"schema_version": "espresso.val_corpus_002.b2_p2_prepare_preflight.v1",
              "status": "PASS", "configuration_count": len(rows),
              "solver_launch_count": 0, "protected_source_access": False,
              "aggregate_sha256": digest.hexdigest(), "configurations": rows}
    _dump(output_root / "P2_PREPARE_CASE_PREFLIGHT.json", result)
    return result


def _record_location(original_root: Path, run_id: str) -> tuple[Path, Path, Path]:
    reuse = original_root / "reuses" / run_id
    if (reuse / "execution-record.json").is_file():
        return reuse, reuse / "production-configuration.json", reuse / "retained-model-output-trace.csv"
    for attempt in (2, 1):
        base = original_root / "executions" / run_id / f"attempt-{attempt}"
        if (base / "execution-record.json").is_file():
            return base, base / "production-configuration.json", base / "case/postProcessing/wholePull/0/traces.csv"
    raise ValueError(f"terminal record missing: {run_id}")


def verify_partial_cache(repo: Path, b1_root: Path, original_root: Path) -> dict:
    configs, hashes = configuration_maps(repo, b1_root)
    ids = sorted(set(configs) - {WASZ_P2_ID})
    if len(ids) != 44:
        raise ValueError("exact 44-identity recovery cache required")
    rows, typed = [], []
    for run_id in ids:
        base, config_path, trace_path = _record_location(original_root, run_id)
        record_path = base / "execution-record.json"
        record = json.loads(record_path.read_text())
        if record.get("run_id") != run_id:
            raise ValueError(f"cache run identity mismatch: {run_id}")
        if b0.file_sha256(config_path) != hashes[run_id] or not trace_path.is_file():
            raise ValueError(f"cache content missing or changed: {run_id}")
        trace_sha, trace_bytes = b0.file_sha256(trace_path), trace_path.stat().st_size
        if record["status"] == "PASS" and (record.get("configuration_sha256") != hashes[run_id]
                or record.get("trace_sha256") != trace_sha or record.get("trace_bytes") != trace_bytes
                or record.get("solver_commit") != b2.SOLVER_COMMIT
                or record.get("executable_sha256") != b2.EXECUTABLE_SHA256
                or record.get("solver_exit_code") != 0):
            raise ValueError(f"passing cache binding mismatch: {run_id}")
        trace = b1._trace_rows(trace_path)
        expected_end = 63.0 if run_id.startswith("WASZ_") else 90.0
        if abs(trace[-1]["time_s"] - expected_end) > 1e-9:
            raise ValueError(f"cache terminal time mismatch: {run_id}")
        if record["status"] == "PASS":
            if run_id.startswith("SCHM_"):
                model, gates = b1.reduce_evaluation(trace, configs[run_id])
                if model != record["model_cup_solute_masses_g"] or gates != record["numerical_gates"]:
                    raise ValueError(f"cache reduction mismatch: {run_id}")
            elif run_id == "WASZ_9_COMPACT_P0_CHEMISTRY":
                reference = Path("/home/tim/espresso-development/.wp03-002-exact-head-review") / b2.REFERENCE_TRACE
                parity = b0.compare_bound_predecessor_parity(reference, b0._read_parity_csv(trace_path))
                if parity["status"] != "PASS" or parity["compared_reference_states"] != 1500:
                    raise ValueError("cached predecessor parity mismatch")
        elif record["status"] == "TYPED_NUMERICAL_CASE_FAILURE":
            solver_log = base / "log.solver"
            log_text = solver_log.read_text(errors="replace")
            if (record.get("failure_reason") != TARGET_FAILURE or record.get("objective") is not None
                    or not run_id.startswith("SCHM_") or log_text.count("\nEnd\n") != 1
                    or "FOAM FATAL" in log_text or "Floating point exception" in log_text):
                raise ValueError(f"typed cache disposition mismatch: {run_id}")
            try:
                b1.reduce_evaluation(trace, configs[run_id])
            except ValueError as exc:
                if str(exc) != "fixed-mass extrapolation is prohibited":
                    raise
            else:
                raise ValueError(f"typed target failure no longer reconstructs: {run_id}")
            typed.append(run_id)
        else:
            raise ValueError(f"nonterminal status in recovery cache: {run_id}")
        rows.append({"run_id": run_id, "status": record["status"],
                     "record_sha256": b0.file_sha256(record_path),
                     "configuration_sha256": hashes[run_id],
                     "trace_sha256": trace_sha, "trace_bytes": trace_bytes})
    if len(typed) != 18 or sum(row["status"] == "PASS" for row in rows) != 26:
        raise ValueError("partial cache disposition counts mismatch")
    digest = hashlib.sha256()
    for row in rows:
        digest.update(b0.canonical_bytes(row))
    return {"schema_version": "espresso.val_corpus_002.b2_partial_matrix_cache.v1",
            "status": "PASS", "identity_count": 44, "passing_count": 26,
            "typed_failure_count": 18, "typed_failure_identities": typed,
            "aggregate_sha256": digest.hexdigest(), "identities": rows,
            "original_partial_aggregate_sha256": ORIGINAL_PARTIAL_AGGREGATE}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("inventory", "preflight", "cache"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--b1-root", type=Path, required=True)
    parser.add_argument("--original-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, b1_root = args.root.resolve(), args.b1_root.resolve()
    if args.command == "inventory":
        value = corrected_inventory(root, b1_root, root / "validation/cases/val_corpus_002/VAL_CORPUS_002_STAGE_B2_CONFIGURATION_INVENTORY.json")
        _dump(args.output, value)
    elif args.command == "preflight":
        preflight_all_p2(root, b1_root, args.output.resolve())
    else:
        if not args.original_root:
            raise SystemExit("--original-root required")
        _dump(args.output, verify_partial_cache(root, b1_root, args.original_root.resolve()))


if __name__ == "__main__":
    main()
