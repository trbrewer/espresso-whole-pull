import csv,json
from pathlib import Path
NEXT={
 "SCI_DATA_FUSION_001_POSITIVE_AT_LEAST_ONE_COMMON_EWP_CONSTRAINT":("COMPLETE_POSITIVE","SCI-DATA-FUSION-001-CONSUMER-CONTRACT",True,"qualified common support requires separate bounded consumer authorization"),
 "SCI_DATA_FUSION_001_COMMON_SUPPORT_IDENTIFIED_NO_QUANTITATIVE_EWP_NARROWING":("COMPLETE_POSITIVE","SCI-DATA-FUSION-001-BASELINE-CONTRACT",True,"common support recorded without uncertainty-reduction claim"),
 "SCI_DATA_FUSION_001_COMPLEMENTARY_SOURCE_CONDITIONED_SUPPORTS_ONLY":("COMPLETE_NEGATIVE","SCI-ED-003",True,"cross-corpus route exhausted; sources remain conditioned alternatives"),
 "SCI_DATA_FUSION_001_NEGATIVE_NO_COMMON_CROSS_CORPUS_CONSTRAINT":("COMPLETE_NEGATIVE","SCI-ED-003",True,"no qualified common constraint; route exhausted"),
 "SCI_DATA_FUSION_001_CONFLICTING_SAME_SCOPE_COMPONENT_EVIDENCE":("BLOCKED_DATA_JOIN","SCI-DATA-FUSION-001-CONFLICT-ADJUDICATION-CONTRACT",False,"same-scope conflict preserved; minimum adjudication authority required; no averaging"),
 "SCI_DATA_FUSION_001_BLOCKED_DECISION_MATERIAL_SEMANTIC_OR_AUTHORITY":("BLOCKED_DATA_JOIN","SCI-DATA-FUSION-001-BOUNDED-RECONCILIATION",False,"one bounded reconciliation only when the frozen blocker is decision-material")}
def append_once(path:Path,marker:str,text:str):
    old=path.read_text()
    if marker not in old:path.write_text(old.rstrip()+"\n\n"+text.rstrip()+"\n")
def apply(root:Path,decision:dict,result_manifest_sha256:str):
    disposition=decision["disposition"];status,next_task,exhausted,exhaustion=NEXT[disposition];programme_path=root/"provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json";programme=json.loads(programme_path.read_text());task=next(row for row in programme["opportunities"] if row["task_id"]=="SCI-DATA-FUSION-001");task.update(status=status,completion_evidence=["docs/analysis/sci_data_fusion_001/DECISION.json",f"RESULT_ARTIFACT_MANIFEST_SHA256:{result_manifest_sha256}"],exhausted_for_decision=exhausted,exhaustion_decision=exhaustion,notes="Completed under CROSS_CORPUS_COMPONENT_EVIDENCE; no production adoption or physical validation.");programme["current_priority"]=next_task;programme["current_claim_ceiling"]="CLOSURE_CONTRACT_ONLY" if next_task=="SCI-ED-003" else "CROSS_CORPUS_COMPONENT_EVIDENCE";programme_path.write_text(json.dumps(programme,indent=2)+"\n")
    marker="SCI-DATA-FUSION-001 result (2026-09-02)";section=f"## {marker}\n\n`{disposition}`. {exhaustion}. Selected next action: `{next_task}`. No production adoption, physical validation, OpenFOAM, or laboratory operation."
    append_once(root/"docs/PROJECT_STATE.md",marker,section);append_once(root/"docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md",marker,section);append_once(root/"docs/CLAIM_CEILING.md",marker,section);append_once(root/"docs/strategy/AVAILABLE_DATA_FIRST_POLICY.md",marker,section)
    agent_marker="SCI-DATA-FUSION-001 deterministic closeout";append_once(root/"AGENTS.md",agent_marker,f"## {agent_marker}\n\nCompleted as `{disposition}`; next action is `{next_task}`. Home-lab operation remains unauthorized.")
    ledger=root/"docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv"
    with ledger.open(newline="") as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row.get("task_id")=="SCI-DATA-FUSION-001" or row.get("opportunity_id")=="SCI-DATA-FUSION-001":row.update(status=status,result=disposition,next_action=next_task,exhausted_for_decision=str(exhausted).lower(),exhaustion_decision=exhaustion,completion_evidence="docs/analysis/sci_data_fusion_001/DECISION.json")
    with ledger.open("w",newline="") as stream:writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n",extrasaction="ignore");writer.writeheader();writer.writerows(rows)
