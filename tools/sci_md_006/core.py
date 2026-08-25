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


def load_evidence(puckworks: Path) -> tuple[list[Observation], dict[tuple[int, str], float]]:
    raw_path = puckworks / "data/schmieder2023/raw_fractions.csv"
    fit_path = puckworks / "data/schmieder2023/kinetics_fit_params_avg.csv"
    raw = read_csv(raw_path)
    fits = {(int(float(r["exp"])), r["component"]): r for r in read_csv(fit_path)}
    cols = {"caffeine": "c_caffeine_mg_g", "trigonelline": "c_trigonelline_mg_g"}
    grouped: dict[tuple[int, int, str], list[dict[str, str]]] = defaultdict(list)
    for row in raw:
        for species, column in cols.items():
            if row[column] and row["mass_fraction_g"] and row["mass_accumulated_g"]:
                grouped[(int(float(row["exp"])), int(float(row["fraction"])), species)].append(row)
    observations: list[Observation] = []
    first: dict[tuple[int, str], list[tuple[float, float]]] = defaultdict(list)
    for (exp, fraction, species), rows in sorted(grouped.items()):
        mass = fmean(float(r["mass_fraction_g"]) * 1e-3 for r in rows)
        midpoint = fmean(float(r["mass_accumulated_g"]) * 1e-3 for r in rows)
        concentration = fmean(float(r[cols[species]]) * 1e-3 for r in rows)
        observations.append(Observation(exp, fraction, species,
            float(rows[0]["flow_set_ml_s"]) * 1e-6, midpoint-mass/2, midpoint+mass/2, concentration))
        if fraction == 1:
            first[(exp, species)].append((mass, concentration))
    inventories = {}
    for key, values in sorted(first.items()):
        fit = fits[key]
        first_mass_g = fmean(v[0] for v in values) * 1e3
        first_species_mg = fmean(m * 1e3 * c * 1e3 for m, c in values)
        tail_mg = float(fit["c0"]) * float(fit["lambda_g"]) * math.exp(-first_mass_g/float(fit["lambda_g"]))
        inventories[key] = (first_species_mg + tail_mg) / 20.0 * 1e-3
    return observations, inventories


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


def decision(g: Mapping[str,bool]) -> str:
    contract = all(g.get(k,False) for k in ("data_contract","inventory_policy","nesting","parity"))
    if not contract: return "SCI_MD_006_TRAINING_APPLICATION_CONTRACT_BLOCKED"
    h0 = all(g.get(k,False) for k in ("h0_optimizer","h0_identifiable","h0_no_bounds","numerical","governance"))
    if not h0: return "SCI_MD_006_SHARED_NULL_NOT_QUALIFIED"
    h1keys=("joint_improvement","species_noninferiority","h1_identifiable","h1_no_bounds","h1_optimizer","nesting_inequality")
    if all(g.get(k,False) for k in h1keys):
        return "SCI_MD_006_SPECIES_SPECIFIC_PRODUCTION_LAW_ELIGIBLE_FOR_NEW_INDEPENDENT_DATASET_TEST"
    return "SCI_MD_006_SHARED_PARAMETER_PRODUCTION_BASELINE_RETAINED"
