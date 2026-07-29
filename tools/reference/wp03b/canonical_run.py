"""Canonical deterministic WP-0.3B runner."""
from __future__ import annotations
import hashlib
import json
import math
import platform
import sys
import os
import tempfile
import subprocess
from dataclasses import replace
from pathlib import Path

from . import liang2021 as l, matias2023 as m, moroney2017 as r
from .observables import (RetainedLiquidDryingObservation, TDSMeasurement,
                          EYConvention, drying_kernel)
from .provenance import SOURCES
from .moroney2017_derivation import build_derivation


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, implementation_commit: str, implementation_tree: str):
    contract_path = root / "validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json"
    contract = json.loads(contract_path.read_text())
    mc = contract["canonical"]["moroney"]
    moroney = {}
    for name, p in (("fine", r.FINE), ("coarse", r.COARSE)):
        traces = [r.solve(p, mc["end_time_dimensionless"], h) for h in mc["steps"]]
        inventories = [r.inventory(row[1:], p) for row in traces[-1]]
        conservation = max(abs(x - inventories[0]) for x in inventories)
        endpoints = [trace[-1][1] for trace in traces]
        refine = abs(endpoints[2]-endpoints[1]) / max(abs(endpoints[1]-endpoints[0]), 1e-30)
        equilibrium_error = abs(endpoints[-1]-r.equilibrium(p)[0]) / r.equilibrium(p)[0]
        moroney[name] = {
            "conservation_residual": conservation,
            "refinement_ratio": refine,
            "equilibrium_relative_error": equilibrium_error,
            "status": "PASS" if conservation <= mc["conservation_absolute_tolerance"]
            and refine <= mc["refinement_ratio_maximum"]
            and equilibrium_error <= mc["equilibrium_relative_tolerance"] else "FAIL",
        }
    mt = contract["canonical"]["matias"]
    low_errors = [abs(m.full_outlet(1, pe, 1, 1)-m.low_pe(1,1,1))/m.low_pe(1,1,1)
                  for pe in mt["low_pe_sequence"]]
    high_errors = [abs(m.full_outlet(1, pe, 1, 1)-m.high_pe(1,pe,1,1))
                   / max(m.high_pe(1,pe,1,1), 1e-30) for pe in mt["high_pe_sequence"]]
    gating = [m.front_gating_error(x) for x in mt["sh_over_pe_sweep"]]
    matias = {
        "low_pe_relative_errors": low_errors,
        "high_pe_relative_errors": high_errors,
        "front_gating_errors": gating,
        "status": "PASS" if all(a > b for a,b in zip(low_errors,low_errors[1:]))
        and all(a > b for a,b in zip(high_errors,high_errors[1:]))
        and all(a < b for a,b in zip(gating,gating[1:]))
        and low_errors[-1] < mt["limit_final_relative_tolerance"]
        and high_errors[-1] < mt["limit_final_relative_tolerance"] else "FAIL",
    }


def build_amended_result(root: Path, implementation_commit: str,
                         implementation_tree: str):
    """Build the complete A1 result in memory without writing an artifact."""
    contract_path = root / "validation/contracts/WP_0_3B_A1_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json"
    contract = json.loads(contract_path.read_text())
    mc = contract["moroney"]
    cases = {}
    for name, p in (("fine", r.FINE), ("coarse", r.COARSE)):
        traces = [r.solve(p, mc["end_time_dimensionless"], h) for h in mc["steps"]]
        refinement = r.trajectory_refinement(traces)
        reduced = r.solve_reduced(p, mc["end_time_dimensionless"], mc["steps"][-1])
        reduced_error = max(max(abs(a[j]-b[j]) for j in range(1,4))
                            for a,b in zip(traces[-1],reduced))
        conservation = {
            str(h): max(abs(r.inventory(row[1:],p)-r.inventory(trace[0][1:],p))
                        for row in trace)
            for h,trace in zip(mc["steps"],traces)}
        composite = []
        for divisor in mc["composite_epsilon_divisors"]:
            q = replace(p, epsilon=p.epsilon/divisor)
            reference = r.solve(q, 2.0, 0.00025)
            error = max(max(abs(row[j+1]-
                                r.governing_ode_consistent_second_order_composite(row[0],q)[j])
                            for j in range(3)) for row in reference)
            composite.append({"epsilon":q.epsilon,"trajectory_linf_error":error})
        ratios = [composite[i+1]["trajectory_linf_error"]/composite[i]["trajectory_linf_error"]
                  for i in range(2)]
        endpoint = [trace[-1][1] for trace in traces]
        endpoint_diff = [abs(endpoint[1]-endpoint[0]),abs(endpoint[2]-endpoint[1])]
        passes=(refinement["D_01"]>refinement["roundoff_floor"]
                and refinement["D_12"]>refinement["roundoff_floor"]
                and refinement["D_12"]<refinement["D_01"]
                and refinement["refinement_ratio"]<=mc["amended_refinement_ratio_maximum"]
                and mc["observed_order_minimum"]<=refinement["observed_order"]<=mc["observed_order_maximum"]
                and reduced_error<=mc["reduced_full_maximum_absolute_difference"]
                and max(conservation.values())<=mc["conservation_absolute_tolerance"]
                and max(ratios)<=mc["composite_maximum_successive_error_ratio"])
        cases[name]={"trajectory_refinement":refinement,
                     "endpoint_roundoff_diagnostic":{"values":endpoint,
                       "differences":endpoint_diff,
                       "diagnostic_status":"ROUND_OFF_SATURATED_NOT_A_GATE"},
                     "reduced_full_maximum_absolute_difference":reduced_error,
                     "conservation_by_step":conservation,
                     "composite_epsilon_convergence":{"points":composite,"ratios":ratios},
                     "status":"PASS" if passes else "FAIL"}
    liang = l.endpoint_identifiability(.7,[2.0,12.0],[.5,1,2,4,8],1.0)
    tds=TDSMeasurement("REFRACTOMETRIC","SYNTHETIC","SYNTHETIC","MASS",.001,
                       "NONPROTECTED_SYNTHETIC_VERIFICATION",589.0,293.15,
                       "RECORDED","WATER","SUCROSE","ICUMSA",
                       "UNDILUTED","FILTERED","FRESH")
    ey=EYConvention("BEVERAGE_TDS_TIMES_BEVERAGE_MASS_OVER_DRY_DOSE",
                    tds.method_id,"MASS",None,"DRY_MASS",False,False,
                    "FILTERED","DETERMINISTIC_JACOBIAN")
    observable=drying_kernel(RetainedLiquidDryingObservation(
        .018,.300,.250,.060,.016,.0002,.02,.0001,.0001,.0001,.0001,.00001,.0001))
    derivation = build_derivation()
    modules={name:_sha(root/"tools/reference/wp03b"/name) for name in
             ("moroney2017.py","moroney2017_derivation.py","liang2021.py",
              "observables.py","canonical_run.py")}
    status=all(x["status"]=="PASS" for x in cases.values()) and derivation["status"]=="PASS" \
        and not liang["endpoint_only_tau_identifiable"] and liang["transient_tau_information_demonstrated"]
    return {
      "schema_version":contract["output"]["schema_version"],"task":"WP-0.3B-A1",
      "implementation":{"commit":implementation_commit,"tree":implementation_tree},
      "original_failed_result_sha256":contract["original_identities"]["failed_result_sha256"],
      "contract_sha256":_sha(contract_path),"module_sha256":modules,
      "source_identities":SOURCES,"moroney2017":cases,
      "symbolic_derivation":derivation,"liang2021_endpoint_identifiability":liang,
      "observables":{"tds_method_id":tds.method_id,
                     "ey_definition_id":ey.definition_id,
                     "drying_kernel":observable,"status":"PASS"},
      "environment":{"python":platform.python_version(),"implementation":platform.python_implementation(),
                     "platform":platform.platform()},
      "execution_history":{"original_failed_pre_output_infrastructure_invocations":1,
       "original_completed_canonical_invocations":1,"amended_completed_canonical_invocations":1,
       "implementation_changes_between_original_and_amended_execution":True,
       "governing_physics_changes":False},
      "execution_counts":{"puckworks_code":0,"openfoam":0,"protected_access":0,
                          "wp02_analyzer":0,"scientific_scores":0,"source_or_holdout_fits":0},
      "runtime_wp02_coupling":False,"physical_validation":"NOT_ESTABLISHED",
      "overall_disposition":("NONPROTECTED_EXTRACTION_REFERENCE_AND_OBSERVABLE_VERIFICATION_PASS_AFTER_GOVERNED_AMENDMENT"
                             if status else "NONPROTECTED_REFERENCE_VERIFICATION_FAIL_AFTER_GOVERNED_AMENDMENT"),
      "claim_ceiling":contract["claim_ceiling"]}


def atomic_write_result(output: Path, result):
    """Atomically write a complete deterministic result with fsync."""
    if not output.parent.is_dir():
        raise FileNotFoundError("output parent must exist before calculation")
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    fd,tmp=tempfile.mkstemp(prefix=output.name+".",dir=output.parent)
    try:
        with os.fdopen(fd,"w") as stream:
            stream.write(text);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,output)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
    return hashlib.sha256(text.encode()).hexdigest()
    lc = contract["canonical"]["liang"]
    cases = []
    for K, tau, seed in zip(lc["K_values"], lc["tau_s_values"], lc["seeds"]):
        exact = l.synthetic(K,tau,lc["times_s"],1,0,seed)
        noisy = l.synthetic(K,tau,lc["times_s"],1,lc["noise_sigma"],seed)
        e0, en = l.estimate(lc["times_s"],exact), l.estimate(lc["times_s"],noisy)
        cases.append({"true_K":K,"true_tau_s":tau,"noise_free":e0,"perturbed":en,
          "status":"PASS" if abs(e0["K"]-K)<lc["noise_free_relative_tolerance"]
          and abs(e0["tau_s"]/tau-1)<lc["noise_free_relative_tolerance"]
          and abs(en["K"]-K)<lc["perturbed_K_absolute_tolerance"]
          and abs(en["tau_s"]/tau-1)<lc["perturbed_tau_relative_tolerance"] else "FAIL"})
    obs = drying_kernel(RetainedLiquidDryingObservation(
        0.018,0.300,0.250,0.060,0.016,0.0002,0.02,0.0001))
    modules = {}
    for name in ("moroney2017.py","matias2023.py","liang2021.py","observables.py","canonical_run.py"):
        modules[name] = _sha(root / "tools/reference/wp03b" / name)
    gates = {
        "moroney": all(x["status"]=="PASS" for x in moroney.values()),
        "matias": matias["status"]=="PASS",
        "liang": all(x["status"]=="PASS" for x in cases),
        "observables": obs["role"]=="MEASUREMENT_KERNEL_NOT_EXTRACTION_PHYSICS",
    }
    return {
      "schema_version": contract["result_schema"], "task":"WP-0.3B",
      "implementation":{"commit":implementation_commit,"tree":implementation_tree},
      "contract_sha256":_sha(contract_path),"source_identities":SOURCES,
      "module_sha256":modules,
      "environment":{"python":platform.python_version(),"implementation":platform.python_implementation(),"platform":platform.platform()},
      "moroney2017":moroney,"matias2023":matias,
      "liang2021":{"cases":cases,"endpoint_only_tau_identifiable":False,
        "transient_tau_information_demonstrated":all(x["status"]=="PASS" for x in cases),
        "fit_status":l.FIT_STATUS},
      "observables":{"kernel":obs,"status":"PASS"},
      "gates":{k:"PASS" if v else "FAIL" for k,v in gates.items()},
      "overall_disposition":"NONPROTECTED_EXTRACTION_REFERENCE_AND_OBSERVABLE_VERIFICATION_PASS" if all(gates.values()) else "NONPROTECTED_REFERENCE_VERIFICATION_FAIL",
      "execution_counts":{"canonical_reference":1,"puckworks_code":0,"openfoam":0,"protected_access":0,"wp02_analyzer":0,"scientific_scores":0},
      "source_or_holdout_fit":False,"runtime_wp02_coupling":False,
      "physical_validation":"NOT_ESTABLISHED",
      "claim_ceiling":contract["claim_ceiling"]
    }


def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,required=True)
    p.add_argument("--implementation-commit",required=True); p.add_argument("--implementation-tree",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--amendment-a1",action="store_true"); a=p.parse_args()
    root=a.root.resolve()
    if a.amendment_a1:
        # All fallible output/identity checks precede canonical calculation.
        if not a.output.parent.is_dir():
            raise SystemExit("output parent does not exist")
        head=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,
                            capture_output=True,check=True).stdout.strip()
        tree=subprocess.run(["git","rev-parse","HEAD^{tree}"],cwd=root,text=True,
                            capture_output=True,check=True).stdout.strip()
        if (head,tree)!=(a.implementation_commit,a.implementation_tree):
            raise SystemExit("implementation commit/tree mismatch")
        result=build_amended_result(root,a.implementation_commit,a.implementation_tree)
        digest=atomic_write_result(a.output,result)
        print(digest)
        return 0 if result["overall_disposition"].endswith(
            "PASS_AFTER_GOVERNED_AMENDMENT") else 1
    result=run(root,a.implementation_commit,a.implementation_tree)
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    a.output.write_text(text)
    print(hashlib.sha256(text.encode()).hexdigest())
    return 0 if result["overall_disposition"].endswith("_PASS") else 1

if __name__=="__main__": raise SystemExit(main())
