"""Generate the nonrecursive corrected scientific-file hash inventory."""
from __future__ import annotations
import json
from pathlib import Path
from .core import dump_json,sha256
ROOT=Path(__file__).resolve().parents[2]
EXACT=("docs/validation/sci_md_006/OWNER_ADJUDICATION.md","docs/validation/sci_md_006/SCI_MD_006_CONTRACT.md",
 "tests/test_sci_md_006.py","tools/sci_md_006/__init__.py","tools/sci_md_006/core.py","tools/sci_md_006/freeze.py",
 "tools/sci_md_006/identifiability.py","tools/sci_md_006/numerical.py","tools/sci_md_006/parity.py","tools/sci_md_006/run_analysis.py",
 "validation/sci_md_006/AUTHORITY_AND_INPUT_MANIFEST.json","validation/sci_md_006/BLOCKED_CV_FOLDS.csv",
 "validation/sci_md_006/H0_HIST_REFERENCE.json","validation/sci_md_006/INVENTORY_POLICY.json","validation/sci_md_006/MODEL_CONTRACT.json",
 "validation/sci_md_006/OPTIMIZATION_STARTS.json","validation/sci_md_006/CORRECTED_INSPECTION.json",
 "validation/sci_md_006/CORRECTED_PREFLIGHT.json","validation/sci_md_006/PREFIT_REDUCED_FULL_PARITY.json")
def main():
    bundle=sorted((ROOT/"validation/sci_md_006/training_bundle").glob("*"))
    paths=[ROOT/p for p in EXACT]+bundle
    dump_json(ROOT/"validation/sci_md_006/CORRECTED_SCIENTIFIC_FREEZE_MANIFEST.json",{
      "schema_version":"ewp.sci-md-006-corrected-scientific-freeze/v1","identity_binding":"NONRECURSIVE_F_THEN_B",
      "stopped_candidate_preserved":"d2236022fd7cc9e81ee008be7c932ffd32487efc","scientific_files":[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p)} for p in paths]})
if __name__=="__main__":main()
