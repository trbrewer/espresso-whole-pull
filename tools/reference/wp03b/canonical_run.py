"""Separate historical and amended deterministic WP-0.3B builders."""
import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from . import liang2021 as l, matias2023 as m, moroney2017 as r
from .moroney2017_derivation import build_derivation
from .observables import (EYConvention, RetainedLiquidDryingObservation,
                          TDSMeasurement, assert_compatible, drying_kernel)
from .provenance import SOURCES


MODULES = ("canonical_run.py", "liang2021.py", "matias2023.py",
           "moroney2017.py", "moroney2017_derivation.py", "observables.py",
           "provenance.py")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _modules(root):
    return {name: _sha(root/"tools/reference/wp03b"/name) for name in MODULES}


def run(root, implementation_commit, implementation_tree):
    """Reconstruct the original governed WP-0.3B calculation unchanged."""
    contract_path = root/"validation/contracts/WP_0_3B_NONPROTECTED_EXTRACTION_VERIFICATION_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    mc = contract["canonical"]["moroney"]
    moroney = {}
    for name, p in (("fine", r.FINE), ("coarse", r.COARSE)):
        traces = [r.solve(p, mc["end_time_dimensionless"], h) for h in mc["steps"]]
        inventories = [r.inventory(row[1:], p) for row in traces[-1]]
        conservation = max(abs(x-inventories[0]) for x in inventories)
        endpoints = [trace[-1][1] for trace in traces]
        refine = abs(endpoints[2]-endpoints[1])/max(
            abs(endpoints[1]-endpoints[0]), 1e-30)
        equilibrium_error = abs(endpoints[-1]-r.equilibrium(p)[0])/r.equilibrium(p)[0]
        passed = (conservation <= mc["conservation_absolute_tolerance"] and
                  refine <= mc["refinement_ratio_maximum"] and
                  equilibrium_error <= mc["equilibrium_relative_tolerance"])
        moroney[name] = {"conservation_residual": conservation,
                         "refinement_ratio": refine,
                         "equilibrium_relative_error": equilibrium_error,
                         "status": "PASS" if passed else "FAIL"}
    matias = _matias(contract["canonical"]["matias"])
    liang, liang_gates = _liang(contract["canonical"]["liang"])
    observation, observable_gates = _observables()
    gates = {"moroney": all(x["status"] == "PASS" for x in moroney.values()),
             "matias": matias["status"] == "PASS",
             "liang": all(liang_gates.values()),
             "observables": all(observable_gates.values())}
    return {
        "schema_version": contract["result_schema"], "task": "WP-0.3B",
        "implementation": {"commit": implementation_commit,
                           "tree": implementation_tree},
        "contract_sha256": _sha(contract_path), "source_identities": SOURCES,
        "module_sha256": _modules(root), "environment": _environment(),
        "moroney2017": moroney, "matias2023": matias,
        "liang2021": dict(liang, cases=liang["cases"],
                          endpoint_only_tau_identifiable=False),
        "observables": {"kernel": observation, "status":
                        "PASS" if all(observable_gates.values()) else "FAIL"},
        "gates": {k: "PASS" if v else "FAIL" for k, v in gates.items()},
        "overall_disposition":
            ("NONPROTECTED_EXTRACTION_REFERENCE_AND_OBSERVABLE_VERIFICATION_PASS"
             if all(gates.values()) else "NONPROTECTED_REFERENCE_VERIFICATION_FAIL"),
        "execution_counts": {"canonical_reference": 1, "puckworks_code": 0,
                             "openfoam": 0, "protected_access": 0,
                             "wp02_analyzer": 0, "scientific_scores": 0},
        "source_or_holdout_fit": False, "runtime_wp02_coupling": False,
        "physical_validation": "NOT_ESTABLISHED",
        "claim_ceiling": contract["claim_ceiling"],
    }


def _matias(contract):
    low = [abs(m.full_outlet(1, pe, 1, 1)-m.low_pe(1, 1, 1))/m.low_pe(1, 1, 1)
           for pe in contract["low_pe_sequence"]]
    high = [abs(m.full_outlet(1, pe, 1, 1)-m.high_pe(1, pe, 1, 1)) /
            max(m.high_pe(1, pe, 1, 1), 1e-30)
            for pe in contract["high_pe_sequence"]]
    gating = [m.front_gating_error(x) for x in contract["sh_over_pe_sweep"]]
    sub = {
        "full_reference": all(math.isfinite(x) for x in low+high+gating),
        "low_pe_limit": all(a > b for a, b in zip(low, low[1:])) and
                        low[-1] < contract["limit_final_relative_tolerance"],
        "high_pe_limit": all(a > b for a, b in zip(high, high[1:])) and
                         high[-1] < contract["limit_final_relative_tolerance"],
        "sh_pe_sweep": len(gating) == len(contract["sh_over_pe_sweep"]),
        "front_gating_trend": all(a < b for a, b in zip(gating, gating[1:])),
    }
    return {"parameters": contract, "low_pe_relative_errors": low,
            "high_pe_relative_errors": high, "front_gating_errors": gating,
            "subgates": {k: "PASS" if v else "FAIL" for k, v in sub.items()},
            "status": "PASS" if all(sub.values()) else "FAIL"}


def _liang(contract):
    cases = []
    roundtrip = True
    noise_free = True
    perturbed = True
    for K, tau, seed in zip(contract["K_values"], contract["tau_s_values"],
                            contract["seeds"]):
        rates = l.rates_from_K_tau(K, tau)
        back = l.K_tau_from_rates(*rates)
        roundtrip = roundtrip and abs(back[0]-K) <= contract["roundtrip_relative_tolerance"] \
            and abs(back[1]/tau-1) <= contract["roundtrip_relative_tolerance"]
        exact = l.synthetic(K, tau, contract["times_s"], 1, 0, seed)
        noisy = l.synthetic(K, tau, contract["times_s"], 1,
                            contract["noise_sigma"], seed)
        e0, en = l.estimate(contract["times_s"], exact), l.estimate(
            contract["times_s"], noisy)
        nf = abs(e0["K"]-K) < contract["noise_free_relative_tolerance"] and \
            abs(e0["tau_s"]/tau-1) < contract["noise_free_relative_tolerance"]
        pt = abs(en["K"]-K) < contract["perturbed_K_absolute_tolerance"] and \
            abs(en["tau_s"]/tau-1) < contract["perturbed_tau_relative_tolerance"]
        noise_free = noise_free and nf
        perturbed = perturbed and pt
        cases.append({"K": K, "tau_s": tau, "seed": seed, "rates_s-1": rates,
                      "noise_free": e0, "perturbed": en,
                      "status": "PASS" if nf and pt else "FAIL"})
    identity = l.endpoint_identifiability(.7, [2.0, 12.0],
                                          [.5, 1, 2, 4, 8], 1.0)
    degenerate = True
    for args in (([0, 1, 2], [1, 1, 1]), ([0, 0, 0], [0, .1, .2])):
        try:
            l.estimate(*args)
            degenerate = False
        except ValueError:
            pass
    gates = {"rate_roundtrip": roundtrip, "noise_free_recovery": noise_free,
             "perturbed_recovery": perturbed,
             "endpoint_nonidentifiability":
                 not identity["endpoint_only_tau_identifiable"],
             "transient_identifiability":
                 identity["transient_tau_information_demonstrated"],
             "degenerate_detection": degenerate}
    return {"parameters": contract, "cases": cases,
            "endpoint_identifiability": identity, "fit_status": l.FIT_STATUS}, gates


def _observables():
    tds = TDSMeasurement(
        "REFRACTOMETRIC", "SYNTHETIC", "SYNTHETIC", "MASS", .001,
        "NONPROTECTED_SYNTHETIC_VERIFICATION", 589.0, 293.15, "RECORDED",
        "WATER", "SUCROSE", "ICUMSA", "UNDILUTED", "FILTERED", "FRESH")
    compatible = assert_compatible(tds, tds)
    ey = EYConvention("BEVERAGE_TDS_TIMES_BEVERAGE_MASS_OVER_DRY_DOSE",
                      tds.method_id, "MASS", None, "DRY_MASS", False, False,
                      "FILTERED", "DETERMINISTIC_JACOBIAN")
    obs = RetainedLiquidDryingObservation(
        .018, .300, .250, .060, .016, .0002, .02,
        .0001, .0001, .0001, .0001, .0001, .00001, .0001)
    kernel = drying_kernel(obs)
    negative = False
    try:
        drying_kernel(replace(obs, dry_spent_grounds_kg=.2))
    except ValueError:
        negative = True
    gates = {
        "method_schema": tds.method_id == "REFRACTOMETRIC",
        "compatibility": compatible is True,
        "ey_vocabulary": ey.definition_id.startswith("BEVERAGE_TDS"),
        "retained_liquid": kernel["retained_liquid_mass"] == .044,
        "oven_dry": kernel["oven_dry_extracted_mass"] > 0,
        "corrected_extraction":
            kernel["retained_liquid_corrected_extracted_mass"] >
            kernel["oven_dry_extracted_mass"],
        "uncertainty": all(kernel[k] >= 0 for k in
                           ("retained_liquid_uncertainty_kg",
                            "oven_dry_uncertainty_kg",
                            "corrected_extracted_uncertainty_kg",
                            "water_balance_uncertainty_kg")),
        "water_balance": math.isfinite(kernel["water_balance_residual_kg"]),
        "negative_inventory": negative,
        "dimensional_consistency": kernel["units"] == "kg",
    }
    return kernel, gates


def _moroney(contract):
    cases = {}
    gate_totals = {name: True for name in (
        "trajectory_refinement", "roundoff_guard", "reduced_system",
        "all_level_conservation", "all_state_equilibrium",
        "literal_derived_diagnostic", "composite_convergence")}
    for name, p in (("fine", r.FINE), ("coarse", r.COARSE)):
        traces = [r.solve(p, contract["end_time_dimensionless"], h)
                  for h in contract["steps"]]
        refinement = r.trajectory_refinement(traces)
        reduced_errors = {}
        conservation = {}
        equilibria = {}
        eq = r.equilibrium(p)
        for h, trace in zip(contract["steps"], traces):
            reduced = r.solve_reduced(p, contract["end_time_dimensionless"], h)
            reduced_errors[str(h)] = max(max(abs(a[j]-b[j]) for j in range(1, 4))
                                         for a, b in zip(trace, reduced))
            base = r.inventory(trace[0][1:], p)
            conservation[str(h)] = max(abs(r.inventory(row[1:], p)-base)
                                       for row in trace)
            endpoint = trace[-1][1:]
            equilibria[str(h)] = {
                "C_h_relative": abs(endpoint[0]-eq[0])/abs(eq[0]),
                "C_v_relative": abs(endpoint[1]-eq[1])/abs(eq[1]),
                "Psi_s_absolute": abs(endpoint[2]),
                "finite_time_distance_not_discretization_error": True,
            }
        composite = []
        for divisor in contract["composite_epsilon_divisors"]:
            q = replace(p, epsilon=p.epsilon/divisor)
            reference = r.solve(q, contract["composite_end_time_dimensionless"],
                                contract["composite_ode_step"])
            error = max(max(abs(row[j+1] -
                r.governing_ode_consistent_second_order_composite(row[0], q)[j])
                for j in range(3)) for row in reference)
            composite.append({"epsilon": q.epsilon, "trajectory_linf_error": error})
        ratios = [composite[i+1]["trajectory_linf_error"] /
                  composite[i]["trajectory_linf_error"] for i in range(2)]
        endpoint = [trace[-1][1] for trace in traces]
        literal = r.published_truncated_composite(.1, p)
        derived = r.governing_ode_consistent_second_order_composite(.1, p)
        local = {
            "trajectory_refinement":
                refinement["D_12"] < refinement["D_01"] and
                refinement["refinement_ratio"] <= contract["refinement_ratio_maximum"] and
                contract["observed_order_range"][0] <= refinement["observed_order"] <=
                contract["observed_order_range"][1],
            "roundoff_guard":
                refinement["D_01"] > refinement["roundoff_floor"] and
                refinement["D_12"] > refinement["roundoff_floor"],
            "reduced_system":
                max(reduced_errors.values()) <= contract["reduced_full_absolute_tolerance"],
            "all_level_conservation":
                max(conservation.values()) <= contract["conservation_absolute_tolerance"],
            "all_state_equilibrium":
                all(x["C_h_relative"] <= contract["equilibrium_relative_tolerance"] and
                    x["C_v_relative"] <= contract["equilibrium_relative_tolerance"] and
                    x["Psi_s_absolute"] <= contract["equilibrium_zero_state_absolute_tolerance"]
                    for x in equilibria.values()),
            "literal_derived_diagnostic":
                all(math.isfinite(x) for x in literal+derived) and literal != derived,
            "composite_convergence":
                all(a > b for a, b in zip(
                    [x["trajectory_linf_error"] for x in composite],
                    [x["trajectory_linf_error"] for x in composite][1:])) and
                max(ratios) <= contract["composite_ratio_maximum"],
        }
        for key, value in local.items():
            gate_totals[key] = gate_totals[key] and value
        cases[name] = {
            "parameters": p.__dict__, "steps": contract["steps"],
            "trajectory_refinement": refinement,
            "endpoint_roundoff_diagnostic": {
                "values": endpoint,
                "differences": [abs(endpoint[1]-endpoint[0]),
                                abs(endpoint[2]-endpoint[1])],
                "diagnostic_status": "ROUND_OFF_SATURATED_NOT_A_GATE"},
            "reduced_full_errors": reduced_errors,
            "conservation_by_step": conservation,
            "numerical_equilibrium_by_step": equilibria,
            "literal_derived_at_tau_0_1": {"literal": literal, "derived": derived},
            "composite_convergence": {"points": composite, "ratios": ratios},
            "subgates": {k: "PASS" if v else "FAIL" for k, v in local.items()},
        }
    return cases, gate_totals


def _environment():
    return {"python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform()}


def build_a1_amended_result(root, implementation_commit, implementation_tree):
    """Build every P1-frozen component and gate in memory."""
    contract_path = root/"validation/contracts/WP_0_3B_A1_P1_PREEXECUTION_CORRECTION_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    moroney, moroney_gates = _moroney(contract["moroney"])
    matias = _matias(contract["matias"])
    liang, liang_gates = _liang(contract["liang"])
    observable, observable_gates = _observables()
    gates = {
        "moroney": {k: "PASS" if v else "FAIL" for k, v in moroney_gates.items()},
        "matias": matias["subgates"],
        "liang": {k: "PASS" if v else "FAIL" for k, v in liang_gates.items()},
        "observables": {k: "PASS" if v else "FAIL"
                        for k, v in observable_gates.items()},
    }
    passed = all(value == "PASS" for component in gates.values()
                 for value in component.values())
    evidence = root/"validation/evidence"
    amendment = root/"validation/amendments/WP_0_3B_A1_MORONEY_VERIFICATION_AMENDMENT.json"
    return {
        "schema_version": contract["result"]["schema_version"],
        "task": "WP-0.3B-A1-P1",
        "identity": {
            "implementation_commit": implementation_commit,
            "implementation_tree": implementation_tree,
            "p1_contract_sha256": _sha(contract_path),
            "amendment_sha256": _sha(amendment),
            "transcription_sha256": _sha(evidence/"MORONEY2016_EQUATIONS_87_97_GOVERNED_TRANSCRIPTION.json"),
            "derivation_sha256": _sha(evidence/"MORONEY2016_SECOND_ORDER_COMPOSITE_DERIVATION.json"),
            "original_contract_sha256": contract["preserved"]["original_contract_sha256"],
            "original_failed_result_sha256":
                contract["preserved"]["original_failed_result_sha256"],
            "module_sha256": _modules(root),
        },
        "source_identities": SOURCES, "frozen_contract": contract,
        "moroney2017": moroney, "matias2023": matias,
        "liang2021": liang, "observables": observable,
        "symbolic_derivation": build_derivation(), "component_gates": gates,
        "environment": _environment(),
        "execution_counts": {"amended_canonical": 1, "openfoam": 0,
                             "protected_access": 0, "puckworks_code": 0,
                             "scientific_scores": 0, "source_or_holdout_fits": 0,
                             "wp02_analyzer": 0},
        "runtime_wp02_coupling": False, "physical_validation": "NOT_ESTABLISHED",
        "overall_disposition":
            (contract["result"]["required_disposition"] if passed else
             "NONPROTECTED_REFERENCE_VERIFICATION_FAIL_AFTER_GOVERNED_AMENDMENT"),
        "claim_ceiling": contract["claim_ceiling"],
    }


def atomic_write_result(output, result):
    """Atomically write a complete deterministic result with fsync."""
    if not output.parent.is_dir():
        raise FileNotFoundError("output parent must exist before calculation")
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=output.name+".",
                                             dir=str(output.parent))
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, str(output))
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return hashlib.sha256(text.encode()).hexdigest()


def _git_identity(root):
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                            capture_output=True, check=True).stdout.strip()
    tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=root,
                          text=True, capture_output=True,
                          check=True).stdout.strip()
    return commit, tree


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--implementation-tree", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("historical", "a1-amended"),
                        required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not args.output.parent.is_dir():
        raise SystemExit("output parent does not exist")
    if _git_identity(root) != (args.implementation_commit,
                               args.implementation_tree):
        raise SystemExit("implementation commit/tree mismatch")
    if args.mode == "historical":
        result = run(root, args.implementation_commit, args.implementation_tree)
    else:
        result = build_a1_amended_result(
            root, args.implementation_commit, args.implementation_tree)
    digest = atomic_write_result(args.output, result)
    print(digest)
    return 0 if (result["overall_disposition"].endswith("_PASS") or
                 result["overall_disposition"].endswith(
                     "PASS_AFTER_GOVERNED_AMENDMENT")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
