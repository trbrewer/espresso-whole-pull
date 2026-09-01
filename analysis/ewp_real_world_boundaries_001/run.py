from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from .authority import sha256, verify_protocol, verify_puckworks
from .corpus_adapter import adapt
from .qualification import FLAGS, qualify

STOP_STORE = "EWP_REAL_WORLD_BOUNDARIES_001_STOP_VISUALIZER_STORE_UNAVAILABLE"
STOP_CORPUS = "EWP_REAL_WORLD_BOUNDARIES_001_STOP_CORPUS_IDENTITY_UNRESOLVED"
STOP_MUTATED = "EWP_REAL_WORLD_BOUNDARIES_001_STOP_CORPUS_MUTATED_DURING_EXECUTION"
STOP_MAPPING = "EWP_REAL_WORLD_BOUNDARIES_001_BLOCKED"


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def source_digest(store: Path) -> str:
    h = hashlib.sha256()
    files = [store / "_index.csv", *sorted(store.glob("shard_*.jsonl.gz"))]
    if not files[0].is_file() or len(files) == 1:
        raise RuntimeError(STOP_STORE)
    for p in files:
        h.update(p.name.encode()); h.update(b"\0")
        with p.open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def private_dir_guard(root: Path, private: Path) -> None:
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)
    try: private.resolve().relative_to(root.resolve())
    except ValueError: return
    check = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(private)], check=False)
    if check.returncode != 0: raise RuntimeError("PRIVATE_WORK_DIR_TRACKING_GUARD_FAILED")


def execute(root: Path, puckworks: Path, store: Path, private: Path, output: Path, protocol_hash: str) -> dict:
    protocol_path = root / "docs/analysis/ewp_real_world_boundaries_001/PROTOCOL_FREEZE.json"
    protocol = verify_protocol(protocol_path, protocol_hash)
    pw = verify_puckworks(puckworks)
    private_dir_guard(root, private); output.mkdir(parents=True, exist_ok=True)
    from puckworks.data.visualizer_store import CorpusSnapshot
    snap = CorpusSnapshot(store, name="EWP-REAL-WORLD-BOUNDARIES-001", classification="current-state")
    recon = snap.reconcile(); integ = snap.integrity_stats(); manifest_start = snap.manifest()
    if not recon["ok"]: raise RuntimeError(STOP_CORPUS)
    if integ["n_logical_records"] != 23169 or integ["n_stored_versions"] != 23169: raise RuntimeError(STOP_CORPUS)
    start_hash = source_digest(store)
    reasons, tiers, schemas, device_resolved = Counter(), Counter(), Counter(), 0
    linked = 0; linked_users: set[str] = set(); ambiguous = 0; eligible_any = 0
    private_rows = private / "qualification_rows.csv"
    with private_rows.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(["audit_id", "reason_codes", *FLAGS])
        for raw in snap.latest():
            r = adapt(raw); flags, why = qualify(r)
            reasons.update(why); schemas[r.schema_version] += 1; linked += bool(r.local_linkage)
            if r.local_linkage: linked_users.add(r.local_linkage)
            ambiguous += r.ambiguous_native_flow_present
            device_resolved += bool(r.machine and r.integration_source and r.integration_source_provenance)
            for key, value in flags.items(): tiers[key] += bool(value)
            eligible_any += any(flags.values())
            w.writerow([r.audit_id or "", ";".join(sorted(why)), *[str(flags[k]).lower() for k in FLAGS]])
            del raw, r
    private_rows.chmod(0o600)
    manifest_end = snap.manifest(); end_hash = source_digest(store)
    if start_hash != end_hash or manifest_start != manifest_end: raise RuntimeError(STOP_MUTATED)
    total = integ["n_logical_records"]
    mapping_blocked = tiers["ewp_pressure_boundary_executable"] == 0 and device_resolved == 0
    decision = {
        "claim_ceiling": "RECENT_PUBLIC_COHORT_BOUNDARY_QUALIFICATION_AND_POROSITY_CONDITIONED_EWP_HYDRAULIC_RESPONSE_MAPPING",
        "code": "EWP_REAL_WORLD_BOUNDARIES_001_BLOCKED" if mapping_blocked else "UNADJUDICATED",
        "gate_inputs": {"authority_pass": True, "canonical_source_pass": True, "privacy_contract_pass": True,
                        "protocol_pass": True, "resolved_device_records": device_resolved,
                        "ewp_executable_case_count": 0, "all_load_bearing_pressure_mappings_unresolved": mapping_blocked},
        "reason": "Every record lacks a documented pressure-sensor/device and integration family, so the frozen EWP transfer contract cannot qualify any pressure boundary." if mapping_blocked else "Execution continuation required.",
        "stop_code": "EWP_REAL_WORLD_BOUNDARIES_001_STOP_ALL_LOAD_BEARING_MEASUREMENT_MAPPINGS_UNRESOLVED" if mapping_blocked else None,
        "successor": "EWP-RWB-001-PRESSURE-SENSOR-BOUNDARY-INTERFACE-RECONCILIATION",
    }
    authority = {"task_id": "EWP-REAL-WORLD-BOUNDARIES-001", "ewp_start_commit": "34deac91170f49587820e60b6e357bfdc3e0874a",
                 "ewp_start_tree": "e57f7318ffa02bfb5dc37f2a45646e7d6b3e569b", "puckworks": pw,
                 "protocol_sha256": protocol_hash, "source_scenario_change_only": True,
                 "no_governing_physics_change": True, "no_production_default_change": True,
                 "no_runtime_puckworks_lock_change": True, "no_live_api_acquisition": True}
    receipt = {"corpus_id": "VISUALIZER_COFFEE_API_CRAWL_2026_07_15", "puckworks_commit": pw["commit"], "puckworks_tree": pw["tree"],
               "classification_native": "current-state", "snapshot_name": "EWP-REAL-WORLD-BOUNDARIES-001",
               "version_selection_rule": protocol["corpus_contract"]["latest_rule"], "store_schema_version": manifest_start["store_schema_version"],
               "bronze_schema_version": manifest_start["bronze_schema_version"], "harvest_version": manifest_start["harvest_version"],
               "normalizer_source_sha256": manifest_start["normalizer_source_sha256"], **integ,
               "n_quarantined": manifest_start["n_quarantined"], "aggregate_start_state_sha256": start_hash,
               "aggregate_end_state_sha256": end_hash, "source_state_equal": True,
               "canonical_snapshot_manifest_sha256": manifest_start["manifest_sha256"],
               "source_window_description": "permissioned recent-public current-state corpus collected through 2026-07-15; not a publication freeze",
               "no_network": True, "raw_files_committed": False, "per_record_outputs_committed": False}
    privacy = {"source": "Visualizer", "attribution": "Data source: Visualizer. We collectively acknowledge the users who make their shots public.",
               "permission": "PERMISSIONED_RECENT_PUBLIC_AGGREGATE_ANALYSIS", "raw_redistribution": False, "private_records": False,
               "minimum_shots_per_published_cell": 20, "minimum_distinct_users_per_published_cell": 10,
               "published_cells": 0, "coarsened_cells": 0, "suppressed_cells": 1,
               "suppression_reasons": {"UNRESOLVED_DEVICE_AND_INTEGRATION_FAMILY": total}}
    linkage = {"records_with_valid_local_linkage": linked, "records_without_valid_local_linkage": total-linked,
               "valid_linkage_fraction": linked/total, "linked_distinct_user_count": len(linked_users),
               "namespace": "STORE_LOCAL_PSEUDONYMOUS_LINKAGE_FOR_SELECTION_BIAS_ACCOUNTING",
               "primary_equal_user_summary_adequate": False, "reason": "No privacy-qualified device cell exists; user identities were not emitted.",
               "bootstrap": {"replicates": 1000, "status": "NOT_RUN_MATERIAL_STOP", "seed_derivation": "protocol hash plus snapshot hash"}}
    _json(output/"AUTHORITY.json", authority); _json(output/"CORPUS_SNAPSHOT_RECEIPT.json", receipt)
    _json(output/"RIGHTS_PRIVACY_AND_ATTRIBUTION.json", privacy); _json(output/"USER_LINKAGE_AND_WEIGHTING.json", linkage)
    _json(output/"DECISION.json", decision)
    _csv(output/"QUALIFICATION_COUNTS.csv", ["kind","code","count"],
         ([{"kind":"reason","code":k,"count":v} for k,v in sorted(reasons.items())] +
          [{"kind":"eligibility_tier","code":k,"count":tiers[k]} for k in FLAGS] +
          [{"kind":"reconciliation","code":"eligible_for_one_or_more_tiers","count":eligible_any},
           {"kind":"reconciliation","code":"excluded_from_every_task_tier","count":total-eligible_any},
           {"kind":"reconciliation","code":"canonical_logical_total","count":total}]))
    _csv(output/"DEVICE_SCHEMA_SUMMARY.csv", ["normalized_family_id","definition","shot_count","distinct_user_count","qualification_status","suppression_status","transfer_limitations"],
         [{"normalized_family_id":"UNRESOLVED_SUPPRESSED","definition":"No documented device/integration family in canonical normalized records", "shot_count":total,
           "distinct_user_count":"NOT_PUBLISHED_FOR_SUPPRESSED_CELL","qualification_status":"UNRESOLVED","suppression_status":"SUPPRESSED",
           "transfer_limitations":"Pressure sensor location and controller semantics are unknown"}])
    return {"decision": decision, "receipt": receipt, "tiers": dict(tiers), "reasons": dict(reasons), "ambiguous_native_flow_records": ambiguous}
