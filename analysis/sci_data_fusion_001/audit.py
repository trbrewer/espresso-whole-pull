from datetime import date
from pathlib import Path
from .authority import AuthorityError,SUPERSEDED_FREEZES,git,load_json,sha256,verify_freeze_manifest
PASS="SCI_DATA_FUSION_001_SINGLE_INDEPENDENT_PREEXECUTION_AUDIT_PASS"
REQUIRED={"task_id","audit_type","audit_disposition","reviewed_head","reviewed_tree","reviewed_freeze_content_manifest_sha256","reviewer_identity","reviewer_independence_statement","reviewed_authorities","material_findings","review_record_reference","review_date"}
def validate_audit(root:Path,audit_path:Path,manifest_path:Path)->dict:
    record=load_json(audit_path);missing=REQUIRED-set(record)
    if missing:raise AuthorityError(f"audit record missing fields: {sorted(missing)}")
    if record["task_id"]!="SCI-DATA-FUSION-001" or record["audit_type"]!="SINGLE_INDEPENDENT_PREEXECUTION_AUDIT" or record["audit_disposition"]!=PASS:raise AuthorityError("audit is not an exact enabling pass")
    if record["reviewed_head"] in SUPERSEDED_FREEZES:raise AuthorityError("audit refers to a superseded non-enabling freeze")
    head,tree=git(root,"rev-parse","HEAD"),git(root,"rev-parse","HEAD^{tree}")
    if record["reviewed_head"]!=head or record["reviewed_tree"]!=tree:raise AuthorityError("audit reviewed a different exact head/tree")
    if record["reviewed_freeze_content_manifest_sha256"]!=sha256(manifest_path):raise AuthorityError("audit reviewed a different freeze-content manifest")
    if not isinstance(record["reviewer_identity"],str) or not record["reviewer_identity"].strip() or not isinstance(record["reviewer_independence_statement"],str) or not record["reviewer_independence_statement"].strip():raise AuthorityError("audit lacks reviewer identity or independence statement")
    if record["material_findings"] not in ([],None):raise AuthorityError("audit has unresolved material findings")
    if not isinstance(record["review_record_reference"],str) or not record["review_record_reference"].strip():raise AuthorityError("audit lacks preserved review reference")
    try:date.fromisoformat(record["review_date"])
    except (TypeError,ValueError) as exc:raise AuthorityError("invalid audit review date") from exc
    if not isinstance(record["reviewed_authorities"],dict) or not record["reviewed_authorities"]:raise AuthorityError("audit lacks reviewed authorities")
    verify_freeze_manifest(root,manifest_path);return record
