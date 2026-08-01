#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validation.val001.administrative import verify_closure
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);a=p.parse_args()
    print(json.dumps(verify_closure(a.root.resolve()),sort_keys=True))
if __name__=="__main__":main()
