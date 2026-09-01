#!/usr/bin/env python3
import argparse,csv,json,pathlib
p=argparse.ArgumentParser(); p.add_argument("root",type=pathlib.Path); a=p.parse_args(); r=a.root
required=("TASK_CONTRACT.json","DATA_AVAILABILITY_PREFLIGHT.json","DATA_AUTHORITY.json","SOURCE_LINEAGE.json","SHOT_JOIN_QUALIFICATION.csv","WINDOW_QUALIFICATION.csv","QUALIFICATION_FREEZE.json","DECISION.json","RESULT.md","summary.json")
assert all((r/x).is_file() for x in required)
for x in r.glob("*.json"): json.loads(x.read_text())
with (r/"SHOT_JOIN_QUALIFICATION.csv").open(newline="") as f: joins=list(csv.DictReader(f))
with (r/"WINDOW_QUALIFICATION.csv").open(newline="") as f: windows=list(csv.DictReader(f))
assert len(joins)==24 and all(x["qualification_result"]=="PASS" for x in joins)
assert len(windows)==240 and {int(x["source_fraction_id"]) for x in windows if x["profile_position"]}=={1,2,3,5,7,10}
print("VALID")
