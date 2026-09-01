#!/usr/bin/env python3
"""Validate the committed reduced result package."""
import argparse,csv,json,pathlib,sys
REQ=("TASK_CONTRACT.json","DATA_AVAILABILITY_PREFLIGHT.json","DATA_AUTHORITY.json","FLOW_SEMANTICS.csv","FLOW_CLOCK_QUALIFICATION.json","FLOW_CANDIDATE_REGISTRY.json","QUALIFICATION_FREEZE.json","QUALIFICATION_AUDIT.json","CONSTANT_FLOW_PARITY.csv","FLOW_HISTORY_RESULTS.csv","METRIC_RESULTS.csv","DECISION.json","RESULT.md","ATTEMPT_LOG.json","summary.json")
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=pathlib.Path,default=pathlib.Path("."));a=p.parse_args();d=a.root/"docs/analysis/sci_md_pannusch_flow_history_001"
 missing=[x for x in REQ if not (d/x).is_file()]
 if missing:raise SystemExit("missing artifacts: "+",".join(missing))
 for x in d.glob("*.json"):json.loads(x.read_text())
 decision=json.loads((d/"DECISION.json").read_text());freeze=json.loads((d/"QUALIFICATION_FREEZE.json").read_text());audit=json.loads((d/"QUALIFICATION_AUDIT.json").read_text())
 assert decision["scientific_disposition"]=="SCI_MD_PANNUSCH_FLOW_HISTORY_001_FLOW_AUTHORITY_INELIGIBLE"
 assert freeze["chemistry_targets_accessed"] is False and freeze["phase_b"].startswith("PROHIBITED") and audit["status"]=="PASS"
 assert all(float(r["normalized_share_max_abs"])<=1e-8 and r["status"]=="PASS" for r in csv.DictReader((d/"CONSTANT_FLOW_PARITY.csv").open()))
 print("SCI-MD-PANNUSCH-FLOW-HISTORY-001 artifacts: PASS")
if __name__=="__main__":main()
