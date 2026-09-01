#!/usr/bin/env python3
import argparse, csv, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));p.add_argument("--evidence",type=Path,required=True);a=p.parse_args();e=a.evidence
    d=json.loads((e/"DECISION.json").read_text());r=json.loads((e/"CORPUS_SNAPSHOT_RECEIPT.json").read_text());p=json.loads((e/"RIGHTS_PRIVACY_AND_ATTRIBUTION.json").read_text())
    assert d["code"]=="EWP_REAL_WORLD_BOUNDARIES_001_BLOCKED" and d["gate_inputs"]["all_load_bearing_pressure_mappings_unresolved"]
    assert r["classification_native"]=="current-state" and r["n_logical_records"]==23169 and r["source_state_equal"] and r["no_network"]
    assert not r["raw_files_committed"] and not r["per_record_outputs_committed"]
    assert p["minimum_shots_per_published_cell"]==20 and p["minimum_distinct_users_per_published_cell"]==10 and p["published_cell_count"]==0
    assert p["privacy_suppressed_cell_count"]==0 and p["semantic_unresolved_unpublished_group_count"]==1
    assert p["semantic_unresolved_group"]["numeric_privacy_threshold_passes"] is True
    q=list(csv.DictReader((e/"QUALIFICATION_COUNTS.csv").open())); vals={(x["kind"],x["code"]):int(x["count"]) for x in q}
    assert vals[("eligibility_tier","ewp_pressure_boundary_executable")]==0
    assert vals[("reconciliation","eligible_for_one_or_more_tiers")]+vals[("reconciliation","excluded_from_every_task_tier")]==23169
    forbidden=("/home/", "shard_", "@example.com", "http://localhost")
    for f in e.iterdir():
        if f.suffix in {".json",".csv",".md"}:
            low=f.read_text(errors="ignore").lower()
            assert not any(x in low for x in forbidden), (f, forbidden)
    print("EWP-REAL-WORLD-BOUNDARIES-001 validation: PASS (material stop preserved)")
if __name__=="__main__":main()
