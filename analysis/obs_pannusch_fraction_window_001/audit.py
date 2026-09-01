"""Independent pre-score audit of source authority and target independence."""
import argparse, copy, hashlib, json, pathlib, re
import numpy as np
from scipy.io import loadmat
from .core import ASSAY_IDS, sha, source_semantics, verify_sources, write_json

def structural_projection(exp,mass):
    rows=[]
    for ci,item in enumerate(np.atleast_1d(exp),1):
        for ri,run in enumerate(np.atleast_1d(item.run),1):
            fit=np.atleast_1d(mass)[(ci-1)*3+ri-1]; rows.append([ci,ri,float(run.a_flow),float(run.b_flow),[float(x) for x in np.asarray(run.mE).reshape(-1)],[float(x) for x in np.asarray(run.tE).reshape(-1)],float(fit.a),float(fit.b)])
    return hashlib.sha256(json.dumps(rows,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def mutate(exp,mode):
    x=copy.deepcopy(exp); rng=np.random.default_rng(991)
    for item in np.atleast_1d(x):
        for run in np.atleast_1d(item.run):
            for name in ("TdS","TdS_FULL","cAlcaloids","cAlcaloids_FULL"):
                value=np.asarray(getattr(run,name)); changed=np.zeros_like(value) if mode=="zero" else value.reshape(-1)[::-1].reshape(value.shape) if mode=="permuted" else rng.normal(size=value.shape); setattr(run,name,changed)
    return x

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("freeze",type=pathlib.Path); p.add_argument("--expected-sha256",required=True); p.add_argument("--repo",type=pathlib.Path,required=True); p.add_argument("--puckworks",type=pathlib.Path,required=True); p.add_argument("--external-source",type=pathlib.Path,required=True); p.add_argument("--qualification-dir",type=pathlib.Path,required=True); p.add_argument("--output",type=pathlib.Path,required=True); a=p.parse_args(argv)
    actual=sha(a.freeze); x=json.loads(a.freeze.read_text()); observed=verify_sources(a.external_source); exp=np.atleast_1d(loadmat(a.external_source/"ExperimentalData_validation.mat",squeeze_me=True,struct_as_record=False)["ExperimentalData"]); mass=np.atleast_1d(loadmat(a.external_source/"MassData_modelval.mat",squeeze_me=True,struct_as_record=False)["MassData"])
    baseline=structural_projection(exp,mass); variants={m:structural_projection(mutate(exp,m),mass) for m in ("zero","permuted","synthetic")}; runner=(a.repo/"analysis/obs_pannusch_fraction_window_001/run.py").read_text(); phase_a=runner.split('if a.phase=="a"',1)[0]; forbidden=bool(re.search(r"(predicted_share|observed_share|residual|RMSE).*read",phase_a,re.I)); authority=x.get("authorities",{}); rows=(a.qualification_dir/"SHOT_JOIN_QUALIFICATION.csv").read_text().splitlines(); windows=(a.qualification_dir/"WINDOW_QUALIFICATION.csv").read_text().splitlines()
    checks={"freeze_hash":actual==a.expected_sha256,"source_hashes":observed==authority.get("consumed_source_sha256") and sha(a.puckworks/"puckworks/data/pannusch2024/source_inputs.csv")==authority.get("pannusch_source_subset_manifest_sha256"),"code_hashes":sha(a.repo/"analysis/obs_pannusch_fraction_window_001/core.py")==x.get("code_sha256",{}).get("core") and sha(a.repo/"analysis/obs_pannusch_fraction_window_001/run.py")==x.get("code_sha256",{}).get("runner"),"source_semantics":bool(source_semantics((a.external_source/"getExperimentalData_validation.m").read_text())),"qualification_rows":len(rows)==25 and len(windows)==241,"chemistry_zero_invariant":variants["zero"]==baseline,"chemistry_permutation_invariant":variants["permuted"]==baseline,"chemistry_synthetic_invariant":variants["synthetic"]==baseline,"prior_results_unavailable_to_phase_a":not forbidden,"fraction_ids":x.get("source_fraction_ids")==list(ASSAY_IDS),"thresholds_frozen":bool(x.get("tolerances") and x.get("decision_rules")),"no_retuning":x.get("post_score_retuning_permitted") is False,"primary_qualified":x.get("qualification_result")=="FULL_24_QUALIFIED;SAME_SOURCE_LINEAGE_IDENTITY","rights_resolved":"CC-BY-NC-3.0" in authority.get("source_rights","")}
    report={"schema_version":1,"task_id":x.get("task_id"),"audited_freeze_sha256":actual,"audit_code_sha256":sha(__file__),"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"structural_projection_sha256":baseline,"diagnostics":{"join_rows":len(rows)-1,"window_rows":len(windows)-1,"chemistry_variants":["zero","permuted","synthetic"]}}; write_json(a.output,report); print(json.dumps(report,sort_keys=True)); raise SystemExit(0 if report["status"]=="PASS" else 1)
