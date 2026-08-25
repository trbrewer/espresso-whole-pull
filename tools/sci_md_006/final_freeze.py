"""Generate F-final inventory and atomic nonrecursive B-final binding."""
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
from .core import sha256
ROOT=Path(__file__).resolve().parents[2]
def canonical(v):return (json.dumps(v,indent=2,sort_keys=True)+"\n").encode()
def scientific_paths():
    groups=[ROOT/"tools/sci_md_006",ROOT/"validation/sci_md_006/training_bundle"]
    paths=[p for g in groups for p in g.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    paths += [ROOT/"tests/test_sci_md_006.py",ROOT/"docs/validation/sci_md_006/SCI_MD_006_CONTRACT.md",ROOT/"docs/validation/sci_md_006/OWNER_ADJUDICATION.md"]
    for name in ("AUTHORITY_AND_INPUT_MANIFEST.json","BLOCKED_CV_FOLDS.csv","H0_HIST_REFERENCE.json","INVENTORY_POLICY.json","MODEL_CONTRACT.json","OPTIMIZATION_STARTS.json","CORRECTED_INSPECTION.json","CORRECTED_PREFLIGHT.json","GAUGE_INVARIANCE.json","PREFIT_REDUCED_FULL_PARITY.json","APPLICATION_MAPPING_CONTRACT.json","EVIDENCE_REUSE_MANIFEST.json"):
        paths.append(ROOT/"validation/sci_md_006"/name)
    return sorted(set(paths))
def write_atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);data=canonical(value)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+".",suffix=".tmp")
    try:
        with os.fdopen(fd,"wb") as h:h.write(data);h.flush();os.fsync(h.fileno())
        parsed=json.loads(Path(tmp).read_bytes());assert parsed==value and Path(tmp).stat().st_size>0
        os.replace(tmp,path);parsed2=json.loads(path.read_bytes());assert parsed2==value and path.stat().st_size>0
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def freeze():
    files=[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p)} for p in scientific_paths()]
    write_atomic(ROOT/"validation/sci_md_006/FINAL_SCIENTIFIC_FREEZE_MANIFEST.json",{"schema_version":"ewp.sci-md-006-final-scientific-freeze/v1","authorization":"SCI-MD-006-OWNER-ADJUDICATION-UPHOLD-CORRECTED-REREVIEW-STOP-INVOKE-SCI-GOV-001-CIRCUIT-BREAKER-AND-AUTHORIZE-ONE-CONSOLIDATED-FINAL-APPLICATION-REPRESENTABILITY-AND-COMPLETION-2026-08-25","scientific_files":files,"adjudicative_fit_count":0})
def bind(commit,tree):
    freeze_manifest=ROOT/"validation/sci_md_006/FINAL_SCIENTIFIC_FREEZE_MANIFEST.json";science=json.loads(freeze_manifest.read_text());inspection=json.loads((ROOT/"validation/sci_md_006/CORRECTED_INSPECTION.json").read_text())
    value={"schema_version":"ewp.sci-md-006-final-binding/v1","authorization":"SCI-MD-006-OWNER-ADJUDICATION-UPHOLD-CORRECTED-REREVIEW-STOP-INVOKE-SCI-GOV-001-CIRCUIT-BREAKER-AND-AUTHORIZE-ONE-CONSOLIDATED-FINAL-APPLICATION-REPRESENTABILITY-AND-COMPLETION-2026-08-25","scientific_freeze_commit":commit,"scientific_freeze_tree":tree,"scientific_files":science["scientific_files"],"inputs":{"bundle_manifest_sha256":inspection["bundle_manifest_sha256"],"bundle_members":inspection["bundle_members"],"transitive_sources":inspection["transitive_source_hashes"],"production":inspection["production"],"puckworks":inspection["puckworks"]},"evidence_reuse":json.loads((ROOT/"validation/sci_md_006/EVIDENCE_REUSE_MANIFEST.json").read_text()),"issue":104,"branch":"research/sci-md-006-nested-production-law","pull_request":105,"allowed_delta_paths":["validation/sci_md_006/FINAL_FREEZE_BINDING.json","docs/validation/sci_md_006/INDEPENDENT_REVIEW.md"],"prohibited_stopped_commits":["d2236022fd7cc9e81ee008be7c932ffd32487efc","ea78ce48efd126a823b5262b172ed4d590bcdeee","47994a63dfd1835644d721321e351ae9ae2da12b","d52376d59599739714f73c45d4316319c4ae2831","1ccf757dfac2762dbe0e69c34a2f5b7e5567ccc4"],"self_identity":"B-final does not and cannot contain its own commit hash"}
    write_atomic(ROOT/"validation/sci_md_006/FINAL_FREEZE_BINDING.json",value)
def main():
    p=argparse.ArgumentParser();p.add_argument("operation",choices=("freeze","bind"));p.add_argument("--commit");p.add_argument("--tree");a=p.parse_args();freeze() if a.operation=="freeze" else bind(a.commit,a.tree)
if __name__=="__main__":main()
