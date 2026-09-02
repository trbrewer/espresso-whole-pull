import argparse,json
from pathlib import Path
from .audit import validate_audit
from .authority import AuthorityError,load_json,verify_consumed,verify_freeze_manifest,verify_frozen_ewp,verify_puckworks
from .phase_b import execute
from .preexecution import build_manifest,generate
def verify(root,puckworks,output):
    authority=load_json(output/"AUTHORITY.json");ewp=verify_frozen_ewp(root,authority);puck=verify_puckworks(puckworks,authority["puckworks"]);verify_consumed(root,load_json(output/"CONSUMED_RESULT_ARTIFACTS.json"));manifest=verify_freeze_manifest(root,output/"FREEZE_CONTENT_MANIFEST.json");family=load_json(output/"PUCKWORKS_FAMILY_SCREEN.json")
    if family["declared_family_count"]!=family["screened_family_count"] or len(family["families"])!=family["declared_family_count"]:raise AuthorityError("committed family census is incomplete")
    if not (root/"analysis/sci_data_fusion_001/phase_b.py").is_file():raise AuthorityError("Phase B implementation absent")
    return {"status":"PASS","scientific_result_emitted":False,"ewp":ewp,"puckworks":puck,"freeze_content_file_count":len(manifest["files"]),"family_count":len(family["families"])}
def main():
    parser=argparse.ArgumentParser();parser.add_argument("operation",choices=("prepare-freeze","verify-freeze","execute"));parser.add_argument("--root",type=Path,required=True);parser.add_argument("--puckworks-root",type=Path,required=True);parser.add_argument("--output",type=Path,required=True);parser.add_argument("--audit-record",type=Path);args=parser.parse_args();root=args.root.resolve();output=(root/args.output).resolve() if not args.output.is_absolute() else args.output.resolve();puckworks=args.puckworks_root.resolve()
    if args.operation=="prepare-freeze":
        generate(root,puckworks,output);build_manifest(root,output);return
    verify(root,puckworks,output)
    if args.operation=="verify-freeze":return
    if not args.audit_record:raise AuthorityError("execute requires an independent exact-freeze audit record")
    validate_audit(root,args.audit_record.resolve(),output/"FREEZE_CONTENT_MANIFEST.json")
    execute(root,output)
if __name__=="__main__":main()
