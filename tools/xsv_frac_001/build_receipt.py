"""Create and fail-closed validate XSV-FRAC-001 external build receipts."""
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path

SCHEMA="espresso.xsv_frac_001.build_receipt.v1"
SOURCES=("solver/espressoWholePullFoam/espressoWholePullFoam.C","solver/espressoWholePullFoam/Make/files","solver/espressoWholePullFoam/Make/options")
REQUIRED=("schema","role","repository_remote_url","source_root","git_commit","git_tree","clean_worktree","production_solver_source_sha256","make_files_sha256","make_options_sha256","executable_source_bundle_sha256","openfoam_project","openfoam_version","build_command","executable_filename","executable_path","executable_sha256")

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(root,*args): return subprocess.check_output(["git",*args],cwd=root,text=True).strip()
def bundle(hashes): return hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def source_hashes(root):
    values={name:sha(Path(root)/name) for name in SOURCES}
    return values,bundle(values)
def tracked_clean(root): return not subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],cwd=root,text=True).strip()

def create_receipt(source_root,executable,role,build_command):
    root=Path(source_root).resolve(); executable=Path(executable).resolve()
    hashes,aggregate=source_hashes(root)
    receipt={"schema":SCHEMA,"role":role,"repository_remote_url":git(root,"remote","get-url","origin"),"source_root":str(root),"git_commit":git(root,"rev-parse","HEAD"),"git_tree":git(root,"rev-parse","HEAD^{tree}"),"clean_worktree":tracked_clean(root),"production_solver_source_sha256":hashes[SOURCES[0]],"make_files_sha256":hashes[SOURCES[1]],"make_options_sha256":hashes[SOURCES[2]],"executable_source_bundle_sha256":aggregate,"openfoam_project":os.environ.get("WM_PROJECT"),"openfoam_version":os.environ.get("WM_PROJECT_VERSION"),"build_command":build_command,"executable_filename":executable.name,"executable_path":str(executable),"executable_sha256":sha(executable)}
    return receipt

def validate_receipt(path,role,expected_commit,expected_tree):
    receipt=json.loads(Path(path).read_text(encoding="utf-8"))
    missing=[key for key in REQUIRED if key not in receipt]
    if missing: raise ValueError("missing receipt fields: "+", ".join(missing))
    if receipt["schema"]!=SCHEMA or receipt["role"]!=role: raise ValueError("receipt schema or role mismatch")
    if receipt["git_commit"]!=expected_commit or receipt["git_tree"]!=expected_tree: raise ValueError(f"{role} source authority mismatch")
    root=Path(receipt["source_root"])
    if git(root,"rev-parse","HEAD")!=expected_commit or git(root,"rev-parse","HEAD^{tree}")!=expected_tree: raise ValueError("source root Git identity mismatch")
    if not receipt["clean_worktree"] or not tracked_clean(root): raise ValueError("source root is not tracked-clean")
    hashes,aggregate=source_hashes(root)
    expected=(receipt["production_solver_source_sha256"],receipt["make_files_sha256"],receipt["make_options_sha256"])
    if tuple(hashes[name] for name in SOURCES)!=expected or aggregate!=receipt["executable_source_bundle_sha256"]: raise ValueError("source bundle mismatch")
    if receipt["openfoam_project"]!="OpenFOAM" or receipt["openfoam_version"]!="12": raise ValueError("Foundation OpenFOAM 12 receipt required")
    executable=Path(receipt["executable_path"])
    if not executable.is_file() or executable.name!=receipt["executable_filename"] or sha(executable)!=receipt["executable_sha256"]: raise ValueError("executable missing, stale, or altered")
    public={key:value for key,value in receipt.items() if key not in {"source_root","executable_path"}}
    return receipt,public

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--source-root",required=True,type=Path); parser.add_argument("--executable",required=True,type=Path); parser.add_argument("--role",required=True,choices=("candidate","baseline")); parser.add_argument("--build-command",required=True); parser.add_argument("--output",required=True,type=Path); args=parser.parse_args(argv)
    receipt=create_receipt(args.source_root,args.executable,args.role,args.build_command)
    if not receipt["clean_worktree"]: raise SystemExit("source worktree is not tracked-clean")
    args.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
if __name__=="__main__": main()
