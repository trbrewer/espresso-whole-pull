#!/usr/bin/env python3
import argparse,shutil,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analysis.sci_data_fusion_001.authority import AuthorityError,verify_freeze_manifest
from analysis.sci_data_fusion_001.preexecution import SEED_FILES,build_manifest,generate

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,required=True);parser.add_argument("--puckworks-root",type=Path,required=True);parser.add_argument("--committed-package",type=Path,default=Path("docs/analysis/sci_data_fusion_001"));args=parser.parse_args();root=args.root.resolve();committed=(root/args.committed_package).resolve() if not args.committed_package.is_absolute() else args.committed_package.resolve()
    with tempfile.TemporaryDirectory(prefix="sci-data-fusion-001-replay-") as raw:
        replay=Path(raw)
        for name in SEED_FILES:shutil.copy2(committed/name,replay/name)
        generate(root,args.puckworks_root.resolve(),replay);build_manifest(root,replay);verify_freeze_manifest(root,replay/"FREEZE_CONTENT_MANIFEST.json")
        expected={p.name for p in committed.iterdir() if p.is_file()};actual={p.name for p in replay.iterdir() if p.is_file()}
        if expected!=actual:raise AuthorityError(f"immutable file-set mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
        changed=[name for name in sorted(expected) if (committed/name).read_bytes()!=(replay/name).read_bytes()]
        if changed:raise AuthorityError(f"immutable byte mismatch: {changed}")
        print(f"PASS {len(expected)} immutable pre-execution artifacts byte-identical; runtime identity is stdout-only")
if __name__=="__main__":main()
