#!/usr/bin/env python3
"""Pre-score structural audit: emits only pass/fail diagnostics."""
import argparse,hashlib,json,pathlib
p=argparse.ArgumentParser(); p.add_argument("freeze",type=pathlib.Path); p.add_argument("--expected-sha256",required=True); a=p.parse_args()
actual=hashlib.sha256(a.freeze.read_bytes()).hexdigest(); x=json.loads(a.freeze.read_text())
checks={"hash":actual==a.expected_sha256,"qualification":x.get("qualification_result")=="FULL_24_QUALIFIED;SAME_SOURCE_LINEAGE_IDENTITY","target_independent":x.get("operator_construction_target_independent") is True,"fraction_ids":x.get("source_fraction_ids")==[1,2,3,5,7,10],"no_retuning":x.get("post_score_retuning_permitted") is False,"thresholds_frozen":bool(x.get("tolerances") and x.get("decision_rules"))}
print(json.dumps({"status":"PASS" if all(checks.values()) else "FAIL","checks":checks},sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)

