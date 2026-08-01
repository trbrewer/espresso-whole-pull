#!/usr/bin/env python3
"""Generate taxonomy-derived deep schema and coverage matrix; never scores."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validation.val001.deep_schema import FAMILY_SCHEMA_PATH,COVERAGE_PATH,build_family_schema,build_coverage
from tools.validation.val001.framework import canonical_json
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);a=p.parse_args();root=a.root.resolve();schema,mapping=build_family_schema(root);(root/FAMILY_SCHEMA_PATH).write_bytes(canonical_json(schema));matrix=build_coverage(root,mapping);(root/COVERAGE_PATH).write_bytes(canonical_json(matrix));print(f"VAL001_DEEP_SCHEMA_GENERATED families={len(schema['anyOf'])} records={matrix['record_count']}")
if __name__=="__main__":main()
