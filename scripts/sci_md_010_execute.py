#!/usr/bin/env python3
"""Single-use adjudicative executor; deliberately locked until exact review."""
import argparse,json,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--freeze',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 f=json.loads(Path(a.freeze).read_text())
 if f.get('scoring_executed'): raise SystemExit('SCORING_ALREADY_EXECUTED')
 r=f.get('review_receipt')
 if not r or r.get('disposition')!='SCI_MD_010_PRE_SCORE_FREEZE_SINGLE_INDEPENDENT_REVIEW_PASS_READY_FOR_EXECUTION': raise SystemExit('EXACT_FREEZE_INDEPENDENT_REVIEW_REQUIRED')
 raise SystemExit('EXECUTION_REQUIRES_EXACT_REVIEWED_HEAD_AND_REMOTE_VERIFICATION')
if __name__=='__main__': main()
