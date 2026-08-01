#!/usr/bin/env python3
"""Non-writing, non-scoring journal-to-summary verification."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from tools.validation.val001.journal import verify_summary
def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",required=True,type=Path); a=p.parse_args(); root=a.root.resolve()
    verify_summary(root/"validation/val001/VAL_001_INVOCATION_EVENTS.jsonl",root/"validation/val001/schemas/invocation_event.schema.json",root/"validation/val001/VAL_001_INVOCATION_SUMMARY_V2.json")
    print("VAL001_INVOCATION_JOURNAL_SUMMARY_PASS")
if __name__=="__main__": main()
