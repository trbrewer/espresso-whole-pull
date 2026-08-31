#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={"EXISTING_DATA_SUFFICIENT_FOR_CURRENT_DECISION","EXISTING_DATA_PARTIALLY_SUFFICIENT","SPECIFIC_DATA_GAP_REMAINS","INDEPENDENT_VALIDATION_DATA_GAP_REMAINS","EXISTING_DATA_NOT_YET_EXHAUSTED","NO_RELEVANT_DATA_FOUND_AFTER_REGISTER_CHECK","NOT_APPLICABLE"}
LAB={"NONE","DEFER_EXISTING_DATA_NOT_EXHAUSTED","REDESIGN_FOR_SPECIFIC_REMAINING_GAP","PROCEED_TO_BOUNDED_LOCAL_METHOD_QUALIFICATION","PROCEED_TO_INDEPENDENCE_TIER_AFTER_METHOD_QUALIFICATION","NOT_APPLICABLE"}
def validate(d, enforce_current_authority=True):
 required=set(json.loads((ROOT/"schemas/data_availability_preflight.schema.json").read_text())["required"])
 if required-set(d): raise ValueError(f"missing fields: {sorted(required-set(d))}")
 if d["data_sufficiency_status"] not in ALLOWED: raise ValueError("unscoped data-gap status")
 if enforce_current_authority:
  a=json.loads((ROOT/"provenance/AVAILABLE_DATA_AUTHORITY.json").read_text()); p=d["puckworks_authority"]
  for x,y in (("commit","puckworks_commit"),("tree","puckworks_tree"),("manifest_sha256","puckworks_manifest_sha256"),("available_data_register_sha256","puckworks_available_data_register_sha256")):
   if p.get(x)!=a[y]: raise ValueError(f"producer authority mismatch: {x}")
 lab=d["home_lab_recommendation"]
 if lab.get("status") not in LAB or lab.get("operational_authorization") is not False: raise ValueError("invalid laboratory status or authorization")
 if lab["status"] not in {"NONE","NOT_APPLICABLE"} and (not d["datasets_reviewed"] or not d["external_data_check"].get("performed") or not d["remaining_scoped_gaps"] or not lab.get("specific_decision") or not lab.get("why_existing_data_cannot_answer") or not lab.get("minimum_measurement_set") or not lab.get("marginal_information_value")): raise ValueError("laboratory recommendation lacks specific decision/minimum measurement set")
 if re.search(r"/(home|Users)/",json.dumps(d)): raise ValueError("local absolute path in committed payload")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("path");a=ap.parse_args();validate(json.loads(Path(a.path).read_text()));print("VALID")
if __name__=="__main__":main()
