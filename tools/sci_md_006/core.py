"""Pure, deterministic contracts and calculations for SCI-MD-006."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import least_squares

from tools.sci_md_005.reduced import interpolate_cup, simulate

SPECIES = ("caffeine", "trigonelline")
DIFFUSIVITY = {"caffeine": 1.0e-10, "trigonelline": 9.687426142431468e-11}
BOUNDS = {"k_1_s": (0.002, 0.5), "csat_kg_m3": (0.2, 100.0)}
H0_STARTS = ((.004, .4), (.004, 10.), (.004, 60.), (.02, .4), (.02, 10.),
             (.02, 60.), (.1, .4), (.1, 10.), (.1, 60.), (.35, .4), (.35, 10.), (.35, 60.))
H1_OFFSETS = ((0., 0., 0., 0.), (-.7, -.7, .7, .7), (.7, .7, -.7, -.7),
              (-.7, .7, .7, -.7), (.7, -.7, -.7, .7))
DOSE_KG = .020
CLAIM_CEILING = ("SCI-MD-006 may establish only whether four species-specific production "
                 "parameters outperform two shared production parameters under the frozen "
                 "same-lineage Schmieder training evidence, the fold-safe pooled inventory "
                 "policy, the frozen reduced/full application, and the declared blocked-CV "
                 "decision rule. It does not establish independent predictive or physical validation.")


@dataclass(frozen=True)
class Observation:
    experiment_id: int
    fraction_id: int
    species_id: str
    flow_m3_s: float
    lower_mass_kg: float
    upper_mass_kg: float
    observed_kg_per_kg: float


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_evidence(bundle: Path) -> tuple[list[Observation], dict[tuple[int, str], float]]:
    """Consume only the immutable Stage-E0-R1 bundle; never reconstruct it."""
    verify_bundle(bundle)
    summary = read_csv(bundle / "schmieder_fraction_summary.csv")
    long_rows = read_csv(bundle / "schmieder_species_fractions_long.csv")
    coordinates: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    for row in long_rows:
        coordinates[(int(row["experiment_id"]), int(row["fraction_id"]))].append(row)
    observations=[]
    for row in summary:
        if not row["mean_concentration_kg_per_kg_beverage"]:
            continue
        exp, fraction = int(row["experiment_id"]), int(row["fraction_id"])
        source = coordinates[(exp, fraction)]
        masses=[float(r["fraction_mass_kg"]) for r in source if r["fraction_mass_kg"]]
        mids=[float(r["accumulated_mass_coordinate_kg"]) for r in source if r["accumulated_mass_coordinate_kg"]]
        flows=[float(r["flow_m3_s"]) for r in source]
        mass, midpoint, flow = fmean(masses), fmean(mids), fmean(flows)
        observations.append(Observation(exp,fraction,row["species_id"],flow,
            midpoint-mass/2,midpoint+mass/2,float(row["mean_concentration_kg_per_kg_beverage"])))
    inventories={(int(r["experiment_id"]),r["species_id"]):float(r["inventory_mass_fraction_kg_per_kg_dry_coffee"])
        for r in read_csv(bundle/"schmieder_training_inventories.csv")}
    return sorted(observations,key=lambda r:(r.experiment_id,r.fraction_id,r.species_id)),inventories


def verify_bundle(bundle: Path) -> dict:
    manifest_path=bundle/"bundle_manifest.json"
    if sha256(manifest_path)!="112f8b3b943a5cea3399746fde512048e3898f99c8079433dae86bd142db8709":
        raise ValueError("FROZEN_BUNDLE_MANIFEST_HASH_MISMATCH")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    required={"training_contract.json","schmieder_species_fractions_long.csv","schmieder_fraction_summary.csv",
              "schmieder_training_inventories.csv","pannusch_scaling_priors.csv","target_access_policy.json"}
    if not required <= set(manifest.get("artifacts",{})):
        raise ValueError("FROZEN_BUNDLE_MEMBER_MISSING")
    for name, expected in sorted(manifest["artifacts"].items()):
        if sha256(bundle/name)!=expected: raise ValueError("FROZEN_BUNDLE_MEMBER_HASH_MISMATCH:"+name)
    if manifest.get("semantic_target_access") is not False: raise ValueError("TARGET_ACCESS_POLICY_INVALID")
    return manifest


def pooled_inventory(source: Mapping[tuple[int, str], float], training: Sequence[int]) -> dict[str, float]:
    ids = tuple(sorted(training))
    if not ids:
        raise ValueError("inventory training set is empty")
    return {s: fmean(source[(e, s)] for e in ids) for s in SPECIES}


def model_parameters(model: str, x: Sequence[float]) -> dict[str, tuple[float, float]]:
    p = np.exp(np.asarray(x, dtype=float))
    if model == "H0-SHARED" and len(p) == 2:
        return {s: (float(p[0]), float(p[1])) for s in SPECIES}
    if model == "H1-SPECIES" and len(p) == 4:
        return {"caffeine": (float(p[0]), float(p[1])), "trigonelline": (float(p[2]), float(p[3]))}
    raise ValueError("invalid model parameter vector")


def predict(rows: Sequence[Observation], inventory: Mapping[str, float], model: str,
            log_parameters: Sequence[float], *, cells: int = 32, dt_s: float = .1) -> tuple[dict[tuple[int,int,str], float], dict]:
    params = model_parameters(model, log_parameters)
    values, diagnostics = {}, {}
    grouped: dict[tuple[int, str], list[Observation]] = defaultdict(list)
    for row in rows:
        grouped[(row.experiment_id, row.species_id)].append(row)
    for (exp, species), obs in sorted(grouped.items()):
        flow = obs[0].flow_m3_s
        end = max(r.upper_mass_kg for r in obs) / (1000.0 * flow)
        k, csat = params[species]
        result = simulate(flow_m3_s=flow, end_s=end, dose_kg=DOSE_KG,
            inventory_fraction=inventory[species], k_1_s=k, csat_kg_m3=csat,
            diffusivity_m2_s=DIFFUSIVITY[species], cells=cells, dt_s=dt_s)
        diagnostics[(exp, species)] = {k: v for k, v in result.items() if k != "history"}
        for row in obs:
            lo = interpolate_cup(result["history"], row.lower_mass_kg)
            hi = interpolate_cup(result["history"], row.upper_mass_kg)
            value = (hi-lo)/(row.upper_mass_kg-row.lower_mass_kg)
            if not math.isfinite(value) or value <= 0:
                raise FloatingPointError("NONPOSITIVE_OR_NONFINITE_PREDICTION")
            values[(exp, row.fraction_id, species)] = value
    return values, diagnostics


def residuals(rows: Sequence[Observation], prediction: Mapping[tuple[int,int,str], float]) -> np.ndarray:
    by_species = []
    for species in SPECIES:
        selected = [r for r in rows if r.species_id == species]
        raw = np.asarray([math.log(prediction[(r.experiment_id,r.fraction_id,species)]/r.observed_kg_per_kg) for r in selected])
        by_species.append(raw / math.sqrt(len(raw)))
    return np.concatenate(by_species) / math.sqrt(2.0)


def objective(rows: Sequence[Observation], prediction: Mapping[tuple[int,int,str], float]) -> float:
    r = residuals(rows, prediction)
    return float(np.dot(r, r))


def log_bounds(model: str) -> tuple[np.ndarray, np.ndarray]:
    lo = [BOUNDS["k_1_s"][0], BOUNDS["csat_kg_m3"][0]]
    hi = [BOUNDS["k_1_s"][1], BOUNDS["csat_kg_m3"][1]]
    if model == "H1-SPECIES": lo *= 2; hi *= 2
    return np.log(lo), np.log(hi)


def starts(model: str, embedded_h0: Sequence[float] | None = None) -> tuple[tuple[float, ...], ...]:
    if model == "H0-SHARED": return tuple(tuple(np.log(s)) for s in H0_STARTS)
    if embedded_h0 is None: raise ValueError("H1 requires same-fit H0 embedding")
    base = np.asarray([embedded_h0[0], embedded_h0[1], embedded_h0[0], embedded_h0[1]])
    lo, hi = log_bounds(model)
    return tuple(tuple(np.clip(base + np.asarray(offset), lo+.05, hi-.05)) for offset in H1_OFFSETS)


def fit(rows: Sequence[Observation], inventory: Mapping[str,float], model: str,
        fit_starts: Sequence[Sequence[float]]) -> dict:
    lo, hi = log_bounds(model)
    records = []
    for index, start in enumerate(fit_starts):
        def fun(x):
            pred, _ = predict(rows, inventory, model, x)
            return residuals(rows, pred)
        sol = least_squares(fun, np.asarray(start), bounds=(lo,hi), method="trf",
                            xtol=1e-9, ftol=1e-9, gtol=1e-9, max_nfev=300)
        records.append({"start_index":index,"start_log":list(map(float,start)),"success":bool(sol.success),
            "status":int(sol.status),"nfev":int(sol.nfev),"objective":float(np.dot(sol.fun,sol.fun)),
            "log_parameters":list(map(float,sol.x)),"parameters":list(map(float,np.exp(sol.x))),"message":str(sol.message)})
    eligible = [r for r in records if r["success"] and math.isfinite(r["objective"])]
    if not eligible: raise RuntimeError("NO_FINITE_SUCCESSFUL_SOLUTION")
    best = min(eligible, key=lambda r:(r["objective"],r["start_index"]))
    near = [r for r in eligible if r["objective"] <= 1.01*best["objective"] + 1e-15]
    return {"model_id":model,"best":best,"starts":records,"within_one_percent_count":len(near),
            "optimizer_qualified":len(near)>=3}


def bound_distance(value: float, name: str) -> float:
    lower, upper = BOUNDS[name]
    return min((math.log(value)-math.log(lower))/(math.log(upper)-math.log(lower)),
               (math.log(upper)-math.log(value))/(math.log(upper)-math.log(lower)))


def blocked_metrics(rows: Sequence[Observation], predictions: Mapping[tuple[int,int,str], Mapping[str,float]]) -> dict:
    errors = {}
    for species in SPECIES:
        selected = [r for r in rows if r.species_id == species]
        for model in ("H0-SHARED","H1-SPECIES"):
            pred = np.asarray([predictions[(r.experiment_id,r.fraction_id,species)][model] for r in selected])
            obs = np.asarray([r.observed_kg_per_kg for r in selected])
            errors[(species,model)] = float(np.sqrt(np.mean((pred-obs)**2))/np.mean(obs))
    j0=.5*(errors[("caffeine","H0-SHARED")]+errors[("trigonelline","H0-SHARED")])
    j1=.5*(errors[("caffeine","H1-SPECIES")]+errors[("trigonelline","H1-SPECIES")])
    return {"species":{s:{m:errors[(s,m)] for m in ("H0-SHARED","H1-SPECIES")} for s in SPECIES},
            "J_H0_SHARED":j0,"J_H1_SPECIES":j1,"improvement":(j0-j1)/j0,
            "joint_improvement_pass":j1<=.85*j0,
            "species_noninferiority_pass":{s:errors[(s,"H1-SPECIES")]<=1.05*errors[(s,"H0-SHARED")] for s in SPECIES}}


REQUIRED_GATES=("training_bundle_integrity","inventory_policy","exact_nesting","prefit_application_parity",
 "h0_optimizer","h1_optimizer","h0_identifiability","h1_identifiability","h0_no_bounds","h1_no_bounds",
 "h0_postfit_parity","h1_postfit_parity","h0_numerical","h1_numerical","joint_improvement",
 "caffeine_noninferiority","trigonelline_noninferiority","nesting_inequality","h0_hist_immutable",
 "production_solver_immutable","puckworks_read_only","angeloni_nonaccess","holdout_noncreation","governance_integrity")


def decision(g: Mapping[str,bool]) -> str:
    if set(g) != set(REQUIRED_GATES): raise ValueError("DECISION_GATE_SCHEMA_MISMATCH")
    contract = all(g[k] for k in ("training_bundle_integrity","inventory_policy","exact_nesting","prefit_application_parity"))
    if not contract: return "SCI_MD_006_TRAINING_APPLICATION_CONTRACT_BLOCKED"
    integrity=all(g[k] for k in ("h0_hist_immutable","production_solver_immutable","puckworks_read_only","angeloni_nonaccess","holdout_noncreation","governance_integrity"))
    h0 = integrity and all(g[k] for k in ("h0_optimizer","h0_identifiability","h0_no_bounds","h0_postfit_parity","h0_numerical"))
    if not h0: return "SCI_MD_006_SHARED_NULL_NOT_QUALIFIED"
    h1keys=("joint_improvement","caffeine_noninferiority","trigonelline_noninferiority","h1_identifiability","h1_no_bounds","h1_optimizer","nesting_inequality","h1_postfit_parity","h1_numerical")
    if all(g[k] for k in h1keys):
        return "SCI_MD_006_SPECIES_SPECIFIC_PRODUCTION_LAW_ELIGIBLE_FOR_NEW_INDEPENDENT_DATASET_TEST"
    return "SCI_MD_006_SHARED_PARAMETER_PRODUCTION_BASELINE_RETAINED"
