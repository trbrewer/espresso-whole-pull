"""Canonical deterministic WP-0.3B runner."""
from __future__ import annotations
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

from . import liang2021 as l, matias2023 as m, moroney2017 as r
from .observables import RetainedLiquidDryingObservation, drying_kernel
from .provenance import SOURCES


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
    p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    result=run(a.root.resolve(),a.implementation_commit,a.implementation_tree)
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    a.output.write_text(text)
    print(hashlib.sha256(text.encode()).hexdigest())
    return 0 if result["overall_disposition"].endswith("_PASS") else 1

if __name__=="__main__": raise SystemExit(main())
