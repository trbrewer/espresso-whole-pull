#!/usr/bin/env python3
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validation.val001.framework import load_json
from tools.validation.val001.inventory import INVENTORY_PATH,verify_inventory
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path);a=p.parse_args();root=a.root.resolve();inv=load_json(root/INVENTORY_PATH);verify_inventory(root,inv);print(f"VAL001_GOVERNED_INVENTORY_PASS records={inv['record_count']}")
if __name__=="__main__":main()
