#!/usr/bin/env python3
import argparse, os, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(".")); p.add_argument("--puckworks-root",type=Path,default=os.getenv("EWP_REAL_WORLD_BOUNDARIES_PUCKWORKS_ROOT")); p.add_argument("--visualizer-store",type=Path,default=os.getenv("EWP_REAL_WORLD_BOUNDARIES_VISUALIZER_STORE")); p.add_argument("--private-work-dir",type=Path,default=os.getenv("EWP_REAL_WORLD_BOUNDARIES_PRIVATE_WORK_DIR")); p.add_argument("--output",type=Path,required=True); p.add_argument("--expected-protocol-hash",required=True); a=p.parse_args()
    if not a.puckworks_root or not a.visualizer_store or not a.private_work_dir: raise SystemExit("explicit Puckworks, Visualizer store, and private work inputs are required")
    sys.path.insert(0,str(a.root.resolve())); sys.path.insert(0,str(a.puckworks_root.resolve()))
    from analysis.ewp_real_world_boundaries_001.run import execute
    result=execute(a.root.resolve(),a.puckworks_root.resolve(),a.visualizer_store.resolve(),a.private_work_dir.resolve(),a.output.resolve(),a.expected_protocol_hash)
    print(result["decision"]["code"])
if __name__=="__main__": main()
