"""Independent structural audit for the chemistry-blind freeze."""
from __future__ import annotations
import argparse,json,pathlib
from .core import candidate_registry,canonical,sha
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--freeze",type=pathlib.Path,required=True); p.add_argument("--output",type=pathlib.Path,required=True); a=p.parse_args(argv)
 f=json.loads(a.freeze.read_text()); variants=[None,[[0]*6],[[5,4,3,2,1,0]],[[.2]*6]]
 enc=[canonical(candidate_registry(v)) for v in variants]
 checks={"chemistry_variant_registry_byte_identity":len(set(enc))==1,"chemistry_targets_accessed":f["chemistry_targets_accessed"] is False,"phase_b_prohibited":f["phase_b"].startswith("PROHIBITED"),"all_ten_boundaries_reused":f["predecessor_boundary_reference"]["all_ten_boundaries_for_24_shots"],"nonidentity_candidates_ineligible":all(x["candidate_id"]=="Q0_LEGACY_CONSTANT_START" or "INELIGIBLE" in x["eligibility"] for x in f["candidate_registry"])}
 result={"task_id":f["task_id"],"status":"PASS" if all(checks.values()) else "FAIL","audited_pending_freeze_sha256":sha(a.freeze),"checks":checks,"independent_execution_required":"clean worktree or equivalent isolated interpreter"}
 a.output.write_bytes(canonical(result)); print(result["status"],sha(a.output))
if __name__=="__main__":main()

