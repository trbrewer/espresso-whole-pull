#!/usr/bin/env python3
"""Read-only verification of retained VAL-001 OpenFOAM audit bytes."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,stat
from pathlib import Path
EXPECTED={
"espressoWholePullFoam":"0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c",
"R1_9bar_traces.csv":"89c405675cfa2663109f9150d6d3f8cec6cb76bbcb89b2989e11226815c10385","R1_9bar.log":"af4632577a1ec70c9d6eeded012584fec6d6e57862f8a696b3d3de0d2f1a3650",
"WP02_9bar_traces.csv":"bedbe087c0e758dd54de9724a729d9d99ae199b6569713dfba47adcb57dda7a3","WP02_9bar.log":"74e11d4fba56930d4ccb2a827073d6cec3cde6ab60913a5c77aa9d4b9011a1e9",
"WP02_8bar_traces.csv":"377429d0f0f48913c0072ca8043989127ab444de13a9a55b59d224812fef907c","WP02_8bar.log":"8c8fac5579a2843516a7f7417ec048f4a7ca9dd9136e80525173ca4bd9a4f4fb"}
def main():
 p=argparse.ArgumentParser();p.add_argument("--external-root",required=True,type=Path);a=p.parse_args();root=a.external_root.resolve();rows={}
 for name,digest in EXPECTED.items():
  path=root/name
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit(f"hash mismatch: {name}")
  if path.stat().st_mode & (stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH):raise SystemExit(f"artifact is writable: {name}")
  if name.endswith("traces.csv"):
   with path.open(newline="") as stream:data=list(csv.DictReader(stream))
   if len(data)!=5150:raise SystemExit(f"row count mismatch: {name}")
   for row in data:
    for value in row.values():
     try:number=float(value)
     except (TypeError,ValueError):continue
     if not math.isfinite(number):raise SystemExit(f"nonfinite trace value: {name}")
   endpoint=float(data[-1]["time_s"])
   if abs(endpoint-103)>1e-9:raise SystemExit(f"endpoint mismatch: {name}")
   rows[name]=len(data)
 print(json.dumps({"status":"PASS","hashes":len(EXPECTED),"trace_rows":rows,"openfoam_commands":0},sort_keys=True))
if __name__=="__main__":main()
