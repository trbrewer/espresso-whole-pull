#!/usr/bin/env python3
"""Fail-closed deterministic validator for the SCI-ED-003 G0 contract."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path

PIN = "2058d0e947ee9eb92c52d64f6165b810f1fb4732"
TREE = "a6ffb312473b15be43c1571a893b19873ea47c5a"
BASE = "bd031c5acfbfb41e378424e5358a932a8f2f5a50"
RESULT = "SCI_ED_003_MINIMUM_DECISION_RELEVANT_CLOSURE_CONTRACT_DEFINED_SEPARATE_EXECUTION_AUTHORIZATION_REQUIRED"
DIR = Path("docs/analysis/sci_ed_003")
AUTH_ARTIFACTS = ["ISSUE_CONTRACT.md", "DATA_AVAILABILITY_PREFLIGHT.json", "DECISION_ESTIMAND_REGISTER.json", "MEASUREMENT_MODULES.json", "DECISION_IMPACT_MATRIX.csv", "PRIORITIZATION_MATRIX.csv", "MINIMUM_PROGRAMME.json", "MINIMUM_PROGRAMME.md", "DATA_PACKAGE_PROFILE.json", "DATA_DICTIONARY.csv", "RESULT.md", "summary.json"]
HOME_LAB = "DEFER_HOME_LAB_PENDING_SEPARATE_EXECUTION_AUTHORIZATION"

def load(root: Path, name: str): return json.loads((root / DIR / name).read_text(encoding="utf-8"))
def require(ok: bool, msg: str):
    if not ok: raise ValueError(msg)
def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def current_sections(root: Path):
    specs = {
        "AGENTS.md": "Scientific-development governance",
        "docs/PROJECT_STATE.md": "## XSV-PANNUSCH",
        "docs/CLAIM_CEILING.md": "`EWP-REAL-WORLD",
        "docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md": "## Pannusch-to-EWP",
        "docs/strategy/AVAILABLE_DATA_FIRST_POLICY.md": "Before substantive",
        "docs/ONBOARDING.md": "For validation work",
    }
    return {name: (root/name).read_text(encoding="utf-8").split(stop, 1)[0] for name, stop in specs.items()}

def validate(root: Path) -> None:
    pre, reg, mods = load(root,"DATA_AVAILABILITY_PREFLIGHT.json"), load(root,"DECISION_ESTIMAND_REGISTER.json"), load(root,"MEASUREMENT_MODULES.json")
    prog, profile, summary = load(root,"MINIMUM_PROGRAMME.json"), load(root,"DATA_PACKAGE_PROFILE.json"), load(root,"summary.json")
    require(pre["live_ewp_base"]["commit"] == BASE, "wrong EWP base")
    require(pre["puckworks_pin"] == {"commit":PIN,"tree":TREE}, "wrong Puckworks pin/tree")
    require(PIN in json.dumps(profile) and "puckworks/main" not in json.dumps(profile), "Puckworks references must be immutable")
    decisions = reg.get("decisions",[]); require(len(decisions) >= 10, "incomplete decision register")
    ids = {d["decision_id"] for d in decisions}; require(len(ids)==len(decisions), "duplicate decision ID")
    for d in decisions:
        for key in ("estimand","observation_operator","candidate_module","outcomes","actions"):
            require(d.get(key), f"{d['decision_id']} missing {key}")
        require(set(d["outcomes"]) == {"positive","negative","null","blocked"}, f"{d['decision_id']} outcome coverage")
        require(set(d["actions"]) == {"positive","negative","null","blocked"}, f"{d['decision_id']} action coverage")
    require(reg["distinctness_assertions"]["I_ref_EQUALS_PRODUCTION_M0"]=="NOT_ESTABLISHED", "I_ref equality promoted")
    require(reg["distinctness_assertions"]["c_s0_MAPPING"]=="NOT_ESTABLISHED", "c_s0 mapping promoted")
    require(reg["distinctness_assertions"]["T_total_I_ref_Q_production_solid_initial_c_s0"]=="FOUR_DISTINCT_QUANTITIES", "quantity collapse")
    statuses=set(mods["apparatus_status_vocabulary"])
    for m in mods["modules"]:
        for a in m["apparatus_performance"]:
            require(a["status"] in statuses, f"bad apparatus status {m['module_id']}")
            for key in ("range","resolution","accuracy","repeatability","drift_stability","response_time_sample_rate","clock_sync","calibration","raw_native","uncertainty_contribution","failure_mode"):
                require(key in a, f"incomplete apparatus requirement {m['module_id']}:{key}")
    selected={"M01","M02_CONTEXT"}; require(set(summary["selected"])==selected, "selected programme drift")
    for x in prog["mandatory_measurements"]:
        require(x["decisions"] and all(any(full == ref or full.startswith(ref + "_") for full in ids) for ref in x["decisions"]), f"measurement has no named decision: {x['measurement_id']}")
        require("remov" in x["necessity"].lower(), f"missing removable-item proof: {x['measurement_id']}")
    require(prog["stage_f"]["adjudicative"] is False, "Stage F must be nonadjudicative")
    require(prog["stage_d"]["requires_separate_owner_authorization"] is True, "Stage D authorization fail-open")
    for flag in ("operation_authorized","procurement_authorized","data_collection_authorized","model_change_authorized","parameter_adoption_authorized"):
        require(prog[flag] is False and summary[flag] is False, f"authorization fail-open: {flag}")
    require(prog["separate_owner_authorization_required"] is True, "separate authorization absent")
    require("not independent shots" in json.dumps(mods).lower() or "not_independent_shots" in mods["replication_contract"], "technical replicate rule absent")
    require(any("never assumed zero" in d["observation_operator"].lower() or "never implicitly zero" in json.dumps(reg["common_basis"]).lower() for d in decisions), "missing-term zero fail-open")
    endpoint=next(d for d in decisions if d["decision_id"]=="D02_REFERENCE_ENDPOINT")
    require(not any(endpoint["prohibited_endpoint_adoption"].values()), "SCI-ED-002 unsupported endpoint adopted")
    require(all(k in summary["deferred"] for k in ("M03","M04","M05")), "deferred triggers incomplete")
    classes={f["class"] for f in profile["logical_files"]}; require("raw" in classes and "processed" in classes, "raw/processed not separate")
    text="\n".join((root/DIR/f).read_text(encoding="utf-8") for f in AUTH_ARTIFACTS)
    forbidden=[r"/home/[A-Za-z0-9_.-]+/", r"file://", r"AKIA[0-9A-Z]{16}", r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY", r"HOME_LAB_READY_TO_RUN"]
    for pat in forbidden: require(re.search(pat,text,re.I) is None, f"forbidden/private/claim pattern: {pat}")
    require("pretend" not in text.lower() and "fabricated observation" not in text.lower(), "fabricated-data language")
    require(summary["result"]==prog["result"]==RESULT and RESULT in (root/DIR/"RESULT.md").read_text(), "result/summary disagreement")
    manifest=load(root,"RESULT_ARTIFACT_MANIFEST.json")
    listed={x["path"]:x["sha256"] for x in manifest["artifacts"]}
    require(set(listed)==set(AUTH_ARTIFACTS), "result manifest membership drift")
    for rel,digest in listed.items(): require(sha(root/DIR/rel)==digest, f"stale result hash: {rel}")
    ledger=(root/"docs/analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv").read_text(); programme=(root/"docs/strategy/EXISTING_DATA_LEVERAGE_PROGRAMME.md").read_text(); state=(root/"docs/PROJECT_STATE.md").read_text(); ceiling=(root/"docs/CLAIM_CEILING.md").read_text()
    for surface in (ledger,programme,state,ceiling): require("SCI-ED-003" in surface, "current-state surface missing SCI-ED-003")
    require("CLOSURE_CONTRACT_DEFINED_EXECUTION_NOT_AUTHORIZED" in programme+state+ceiling, "status surfaces not reconciled")
    machine=json.loads((root/"provenance/EXISTING_DATA_LEVERAGE_PROGRAMME.json").read_text())
    require(machine["home_lab_status"] == HOME_LAB, "stale home-lab current status")
    selected=next(x for x in machine["opportunities"] if x["opportunity_id"]==machine["current_priority"])
    require(selected["status"].startswith("COMPLETE_") and machine["last_completed_opportunity_review"]==machine["current_priority"], "current priority is not the completed owner-decision item")
    require(machine["laboratory_gate"]["operation_authorized"] is False and machine["laboratory_gate"]["separate_owner_authorization_required"] is True, "laboratory authorization fail-open")
    stale = [r"SCI-ED-003.{0,40}(?:is|`)\s*(?:`)?READY", r"SCI-ED-003.{0,50}not implemented", r"SCI-MD-PANNUSCH-FLOW-HISTORY-001.{0,60}current"]
    for name, section in current_sections(root).items():
        lower=section.lower()
        normalized=re.sub(r"\s+", " ", lower).replace("_", " ")
        require("sci-ed-003" in lower and "complete" in lower, f"{name}: completion absent from active block")
        require("closure contract defined execution not authorized" in normalized, f"{name}: completion status absent from active block")
        require("separate owner authorization" in normalized, f"{name}: separate authorization absent from active block")
        require("owner decision" in normalized, f"{name}: bounded owner decision absent from active block")
        require("automatically selected" in normalized or "automatic successor" in normalized, f"{name}: no-automatic-successor boundary absent")
        require("physical validation" in normalized and "not established" in normalized, f"{name}: physical-validation ceiling absent")
        for pat in stale: require(re.search(pat, section, re.I|re.S) is None, f"{name}: stale active-state language: {pat}")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); args=p.parse_args()
    try: validate(args.root.resolve())
    except (KeyError,ValueError,TypeError,json.JSONDecodeError) as exc: raise SystemExit(f"SCI-ED-003 FAIL: {exc}")
    print("SCI-ED-003 PASS")
if __name__=="__main__": main()
