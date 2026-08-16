#!/usr/bin/env python3
"""SCI-MD-002B standalone reduced wetting-age swelling screen.

No production solver or Puckworks import is used.  The Mo equations are
reimplemented from the pinned model card/implementation and evaluated only as
a relative conductance closure.  Adjudicative execution is fail-closed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import resource
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cases/sci_md_002b"
OVERLAY = ROOT / "validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json"
LANE = ROOT / "docs/analysis/sci_md_002b/PARALLEL_LANE_DECLARATION.json"
TASK = "SCI-MD-002B"
LANE_ID = "EWP-PAR-SCI-MD-002B"
PRESSURES = (5, 9, 11)
POWDERS = {
    "E": (0.292, 0.708, 27.48e-6 / 2, 321.7e-6 / 2),
    "H": (0.275, 0.725, 28.20e-6 / 2, 347.5e-6 / 2),
    "M": (0.203, 0.797, 30.23e-6 / 2, 358.47e-6 / 2),
    "F": (0.097, 0.903, 31.59e-6 / 2, 524.0e-6 / 2),
}
PHI0, MU, RHO, AREA, H0 = 0.4, 0.000315, 965.0, 0.002463008640414398, 0.01
D0, CM0, N_TORT, PCAP = 1.25e-10, 0.1, 0.5, 1.0e4
HARD_CAP, PILOT_MAX = 2500, 32
PUCK_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
PUCK_TREE = "1d553e44ee2f7480a5df521560801b478618cc84"
ADJ_TOKEN = "SCI_MD_002B_ADJUDICATIVE_EXECUTION_AUTHORIZED"
EXTERNAL_NAMESPACE = "SCI_MD_002B_EXTERNAL_BUNDLE"
PILOT_IDS = (
    "A0-FOSTER-P9-N64-DT0.02",
    "A0-ZERO_SWELL-P9-N64-DT0.02",
    "A0-SIMULTANEOUS-P9-E-AC0.0",
    "A0-ACCOM_FIXED-E",
    "A0-ACCOM_FREE-E",
    "R1-REFERENCE-P9-E-D1.0-CM0.1-AC0.0-N32-DT0.04",
    "R1-REFERENCE-P9-E-D1.0-CM0.1-AC0.0-N64-DT0.02",
    "SYNTHETIC-S1-P7-M-D1.0-CM0.1-AC0.5-N64-DT0.02",
)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe_bundle(path: Path) -> Path:
    p = path.absolute()
    if p.exists() and p.is_symlink():
        raise ValueError("bundle root may not be a symlink")
    resolved = p.resolve(strict=False)
    if ROOT == resolved or ROOT in resolved.parents:
        raise ValueError("bundle must remain outside Git")
    if EXTERNAL_NAMESPACE.lower() not in str(resolved).lower() and "sci_md_002b" not in str(resolved).lower():
        raise ValueError("bundle path lacks task namespace")
    for parent in [resolved, *resolved.parents]:
        if parent.exists() and parent.is_symlink():
            raise ValueError("symlink component in bundle path")
    return resolved


def source_conditions() -> dict[int, dict[str, float]]:
    overlays = json.loads(OVERLAY.read_text())["overlays"]
    out = {}
    for p in PRESSURES:
        rows = overlays[f"R1-WASZ-{p}-DARCY-STATIC-MEASURED"]
        last = rows[-1]
        out[p] = {
            "pressure_pa": float(last[2]) * 1e5,
            "flow_kg_s": float(last[4]) * 1e-3,
            "mass_kg": float(last[6]) * 1e-3,
            "report_time_s": float(last[0]),
            "source_overlay_id": f"R1-WASZ-{p}-DARCY-STATIC-MEASURED",
        }
    return out


def hydraulic_anchor() -> float:
    s = source_conditions()[9]
    return (s["flow_kg_s"] / RHO) * MU * H0 / (AREA * s["pressure_pa"])


def foster_front(t: float, pressure_pa: float, k0: float, phi: float = PHI0, pcap: float = PCAP) -> float:
    if min(t, pressure_pa + pcap, k0, phi) < 0 or phi == 0:
        raise ValueError("invalid Foster primitive")
    return math.sqrt(2 * k0 * (pressure_pa + pcap) * t / (MU * phi))


def foster_wetting_times(pressure_pa: float, k0: float, cells: int) -> np.ndarray:
    centers = (np.arange(cells) + 0.5) * H0 / cells
    return MU * PHI0 * centers**2 / (2 * k0 * (pressure_pa + PCAP))


@lru_cache(maxsize=4096)
def swelling_volume_ratio(radius_m: float, age_s: float, diffusivity: float, cmax: float, radial_n: int) -> float:
    """Mo Eq. 3/42 nonlinear spherical diffusion and volume ratio."""
    if age_s <= 0 or diffusivity == 0 or cmax == 0:
        return 1.0
    if not (radius_m > 0 and diffusivity > 0 and 0 < cmax < 1 and radial_n >= 8):
        raise ValueError("invalid swelling primitive")
    r = np.linspace(0.0, radius_m, radial_n + 1)
    dr = radius_m / radial_n

    def rhs(_t: float, c: np.ndarray) -> np.ndarray:
        full = np.empty(radial_n + 1)
        full[:-1], full[-1] = c, cmax
        lap = np.empty(radial_n)
        lap[1:] = ((full[2:] - 2 * full[1:-1] + full[:-2]) / dr**2
                   + 2 / r[1:-1] * (full[2:] - full[:-2]) / (2 * dr))
        lap[0] = 6 * (full[1] - full[0]) / dr**2
        return diffusivity * (1 - full[:-1]) * lap

    sol = solve_ivp(rhs, (0, age_s), np.zeros(radial_n), method="BDF", t_eval=[age_s], rtol=2e-8, atol=2e-10)
    if not sol.success or not np.all(np.isfinite(sol.y)):
        raise RuntimeError("swelling PDE failed")
    c = np.append(sol.y[:, -1], cmax)
    return float(3 / radius_m**3 * np.trapz(r**2 / (1 - c), r))


def particle_state(powder: str, age_s: float, diffusivity: float, cmax: float, radial_n: int) -> tuple[float, float]:
    tf, tc, rf, rc = POWDERS[powder]
    vf = swelling_volume_ratio(rf, age_s, diffusivity, cmax, radial_n)
    vc = swelling_volume_ratio(rc, age_s, diffusivity, cmax, radial_n)
    solid_ratio = tf * vf + tc * vc
    d32 = 2 / (tc / (rc * vc ** (1 / 3)) + tf / (rf * vf ** (1 / 3)))
    d320 = 2 / (tc / rc + tf / rf)
    return solid_ratio, d32 / d320


def accommodation_state(solid_ratio: float, d32_ratio: float, accommodation: float) -> dict[str, float]:
    """Volume-consistent fixed-area interpolation; lambda=0 fixed height, 1 constant porosity."""
    if not 0 <= accommodation <= 1 or solid_ratio < 1 or d32_ratio <= 0:
        raise ValueError("invalid accommodation state")
    height_ratio = 1 + accommodation * (solid_ratio - 1)
    phi = 1 - (1 - PHI0) * solid_ratio / height_ratio
    if not (height_ratio > 0 and 0 < phi < 1):
        raise ValueError("physical state bound failure; clipping prohibited")
    ck = (phi / PHI0) ** (3 + 2 * N_TORT) * d32_ratio**2 * ((1 - PHI0) / (1 - phi)) ** 2
    if ck <= 0 or not math.isfinite(ck):
        raise ValueError("nonpositive permeability")
    return {"solid_ratio": solid_ratio, "height_ratio": height_ratio, "porosity": phi,
            "pore_ratio": phi * height_ratio / PHI0, "permeability_ratio": ck,
            "resistance_ratio": height_ratio / ck}


@dataclass(frozen=True)
class Case:
    case_id: str
    arm: str
    evidence_role: str
    pressure_bar: float | str
    powder: str
    diffusivity_multiplier: float
    cmax: float
    accommodation: float
    coupling: str
    axial_cells: int
    radial_cells: int
    dt_s: float
    comparator_ids: tuple[str, ...]
    authority_status: str
    pilot_eligible: bool
    adjudicative: bool
    refinement_companions: tuple[str, ...]
    output_schema_version: str = "ewp.sci_md_002b.case_record.v1"


def matrix_rows() -> list[dict[str, Any]]:
    rows: list[Case] = []
    def add(*args: Any, **kwargs: Any) -> None:
        rows.append(Case(*args, **kwargs))
    add(PILOT_IDS[0], "A0", "DERIVED_IDENTITY", 9, "E", 0, 0, 0, "FOSTER_CLOSED_FORM", 64, 32, .02, (), "PILOT_ALLOWED", True, False, ())
    add(PILOT_IDS[1], "A0", "NUMERICAL_CONTROL", 9, "E", 0, 0, 0, "ONE_WAY", 64, 32, .02, (), "PILOT_ALLOWED", True, False, ())
    add(PILOT_IDS[2], "A0", "DERIVED_IDENTITY", 9, "E", 1, .1, 0, "SIMULTANEOUS", 64, 32, .02, (), "PILOT_ALLOWED", True, False, ())
    add(PILOT_IDS[3], "A0", "DERIVED_IDENTITY", "SYNTHETIC", "E", 1, .1, 0, "ACCOM_ENDPOINT", 64, 32, .02, (), "PILOT_ALLOWED", True, False, ())
    add(PILOT_IDS[4], "A0", "DERIVED_IDENTITY", "SYNTHETIC", "E", 1, .1, 1, "ACCOM_ENDPOINT", 64, 32, .02, (), "PILOT_ALLOWED", True, False, ())
    # No-swelling source controls: prospectively frozen but never complete-triplet pilot eligible.
    for p in PRESSURES:
        cid = f"C0-NO_SWELL-P{p}-N64-DT0.02"
        add(cid, "C0", "EWP_GOVERNED_SOURCE", p, "M", 0, 0, 0, "ONE_WAY", 64, 32, .02, (), "ADJUDICATIVE_AUTHORITY_REQUIRED", False, True, ())
    # Simultaneous-wetting structural controls.
    for powder in POWDERS:
        for ac in (0.0, 0.5, 1.0):
            cid = f"C1-SIMULTANEOUS-P9-{powder}-AC{ac}"
            add(cid, "C1", "NUMERICAL_CONTROL", 9, powder, 1, .1, ac, "SIMULTANEOUS", 64, 32, .02, (), "PILOT_ALLOWED", cid in PILOT_IDS, False, ())
    # Primary shared candidate sets. Every set has an exact 5/9/11 comparator triplet.
    for powder in POWDERS:
        for dm in (0.5, 1.0, 2.0):
            for cm in (0.05, 0.1):
                for ac in (0.0, 0.5, 1.0):
                    ids = tuple(f"S1-ONEWAY-P{p}-{powder}-D{dm}-CM{cm}-AC{ac}-N64-DT0.02" for p in PRESSURES)
                    for p, cid in zip(PRESSURES, ids):
                        add(cid, "S1", "EWP_GOVERNED_SOURCE", p, powder, dm, cm, ac, "ONE_WAY", 64, 32, .02,
                            tuple(x for x in ids if x != cid), "ADJUDICATIVE_AUTHORITY_REQUIRED", False, True, ())
    # S2 is frozen as a reason-specific design block; no executable scientific rows are invented.
    for p in PRESSURES:
        add(f"S2-DESIGN_BLOCKED-P{p}", "S2", "NUMERICAL_CONTROL", p, "M", 1, .1, .5, "TWO_WAY_DESIGN_BLOCKED", 64, 32, .02,
            (), "NON_EXECUTABLE_DESIGN_BLOCK", False, False, ())
    # Prospective resolution controls and one synthetic non-source pilot.
    for n, rn, dt in ((32, 24, .04), (64, 32, .02), (128, 48, .01)):
        cid = f"R1-REFERENCE-P9-E-D1.0-CM0.1-AC0.0-N{n}-DT{dt}"
        companions = tuple(f"R1-REFERENCE-P9-E-D1.0-CM0.1-AC0.0-N{x}-DT{d}" for x, _, d in ((32,24,.04),(64,32,.02),(128,48,.01)) if x != n)
        add(cid, "R1", "NUMERICAL_CONTROL", 9, "E", 1, .1, 0, "ONE_WAY", n, rn, dt, (), "PILOT_ALLOWED", cid in PILOT_IDS, False, companions)
    add(PILOT_IDS[-1], "R1", "SYNTHETIC_SCREEN_BOUND", 7, "M", 1, .1, .5, "ONE_WAY", 64, 32, .02, (), "PILOT_ALLOWED", True, False, ())
    result = [asdict(r) for r in rows]
    if len(result) > HARD_CAP or len({r["case_id"] for r in result}) != len(result):
        raise RuntimeError("matrix hard cap or uniqueness failure")
    return result


def protocol(matrix_hash: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": "ewp.sci_md_002b.protocol.v1", "task_id": TASK,
        "status": "PROSPECTIVE_FROZEN_ADJUDICATIVE_EXECUTION_NOT_AUTHORIZED", "issue": 74,
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE", "task_change_declaration": "NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE",
        "question": "Can pressure-dependent Foster wetting times plus shared Mo-style swelling produce Q5 > Q9 > Q11?",
        "hypotheses": {f"H{i}": x for i, x in enumerate([
            "No swelling retains increasing flow with pressure.", "Simultaneous wetting gives common relative conductance and cannot reverse ordering.",
            "One-way pressure-dependent wetting age can create pressure-dependent resistance.", "Conservative two-way feedback may strengthen, weaken, or make the effect nonmonotonic.",
            "Capability may depend on fixed-height accommodation.", "Particle-size dependence is synthetic and has no source-grind mapping.",
            "Hydraulic survival cannot uniquely identify swelling without direct structural measurements."])},
        "source": {"overlay": str(OVERLAY.relative_to(ROOT)), "pressure_groups_bar": list(PRESSURES), "reporting_point": "same terminal source point as SCI-MD-002A", "hydraulic_calibration": "single 9-bar scale shared unchanged", "source_targets": source_conditions()},
        "provenance_classes": ["EWP_GOVERNED_SOURCE", "PUCKWORKS_PINNED_REFERENCE", "SOURCE_REPORTED", "SYNTHETIC_SCREEN_BOUND", "NUMERICAL_CONTROL", "DERIVED_IDENTITY"],
        "model": {"chain": "pressure -> wetting time -> local swelling age -> particle expansion -> bed geometry/porosity -> permeability/resistance -> axial flow", "foster": "s=sqrt(2*k*(p+pcap)*t/(mu*phi0))", "age": "max(0,t-t_wet_j)", "mo": "nonlinear spherical diffusion plus Eq42 volume and relative Carman-Kozeny", "accommodation": "V/V0=1+lambda*(Vs/Vs0-1); lambda=0 fixed height; lambda=1 constant porosity", "serial_resistance": "R/R0=sum_j[(h_j/h0_j)/(k_j/k0)]/N", "two_way": "SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED: distributed swelling storage and moving-volume balance require unsupported closure"},
        "axes": {"pressure_bar": list(PRESSURES), "powder": list(POWDERS), "diffusivity_multiplier": [0.5,1,2], "cmax": [.05,.1], "phi0": PHI0, "capillary_pressure_pa": PCAP, "accommodation": [0,.5,1], "coupling": ["ONE_WAY", "TWO_WAY_DESIGN_BLOCKED"], "axial_cells": [32,64,128], "radial_cells": [24,32,48], "dt_s": [.04,.02,.01]},
        "parameter_provenance": {"Mo powders/D0/cmax0": "PUCKWORKS_PINNED_REFERENCE", "pressure/report time/flow targets": "EWP_GOVERNED_SOURCE", "axis multipliers/accommodation/refinement": "SYNTHETIC_SCREEN_BOUND", "identities": "DERIVED_IDENTITY"},
        "gates": ["AUTHORITY_AND_ARTIFACT_VALIDITY", "REFERENCE_AND_NUMERICAL_VALIDITY", "CONSERVATION_AND_PHYSICAL_STATE_VALIDITY", "RESISTANCE_DIRECTION", "PRESSURE_ORDERING", "TEMPORAL_SIGNATURE", "ASSUMPTION_DEPENDENCE", "PARTICLE_SIZE_AND_GRIND_IDENTIFIABILITY", "AGGREGATE_COMPARISON"],
        "ordering_rule": {"margins": ["M59=Q5-Q9", "M911=Q9-Q11"], "uncertainty": "maximum absolute matched base/refined difference for each margin", "pass": "both lower bounds > 0", "unresolved": "either interval includes zero", "reject": "either upper bound <= 0"},
        "physical_bounds": ["finite complete trajectories", "0<=front<=H0", "monotonic wetting", "monotonic uptake", "positive radii/volume/porosity/permeability/resistance", "nonnegative pore volume", "no inversion", "no clipping"],
        "stop_conditions": ["AUTHORITY_MISMATCH", "HASH_MISMATCH", "SOURCE_MAPPING_INVALID", "RIGHTS_INVALID", "MATRIX_DESIGN_EXCEEDS_SECONDARY_LANE_BUDGET", "PHYSICAL_BOUND_FAILURE", "CLIPPING_REQUIRED", "TWO_WAY_COUPLING_DESIGN_BLOCKED"],
        "taxonomy": ["SCI_MD_002B_REJECTED_WRONG_RESISTANCE_DIRECTION", "SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING", "SCI_MD_002B_PRESSURE_ORDERING_NUMERICALLY_UNRESOLVED", "SCI_MD_002B_WETTING_AGE_SWELLING_CAPABILITY_SURVIVES_BOUNDED_SCREEN", "SCI_MD_002B_CAPABILITY_DEPENDS_ON_FIXED_HEIGHT_EXTREME", "SCI_MD_002B_CAPABILITY_DEPENDS_ON_UNMAPPED_PARTICLE_SIZE", "SCI_MD_002B_ONE_WAY_SURVIVES_TWO_WAY_DESIGN_BLOCKED", "SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED", "SCI_MD_002B_BED_ACCOMMODATION_MODEL_DESIGN_BLOCKED", "SCI_MD_002B_ADDITIONAL_SWELLING_AND_DEFORMATION_DATA_REQUIRED", "SCI_MD_002B_MODEL_OR_AUTHORITY_INVALID", "SCI_MD_002B_NUMERICAL_EXECUTION_INVALID", "SCI_MD_002B_COMBINED_MECHANISM_NOT_AUTHORIZED", "SCI_MD_002B_PREEXECUTION_PACKAGE_COMPLETE_PENDING_INDEPENDENT_REVIEW"],
        "budget": {"preferred_max": 1500, "hard_max": HARD_CAP, "row_count": len(matrix_rows()), "pilot_max": PILOT_MAX, "workers": 1, "nested_threads": 1, "memory_gib": 16, "gpu": 0},
        "pilot_row_ids": list(PILOT_IDS), "matrix_sha256": matrix_hash,
        "external_record_schema": "ewp.sci_md_002b.case_record.v1", "reducer_behavior": "adjudicative records only; gate precedence fixed; pilot reduction forbidden",
        "claim_boundary": ["PHYSICAL_VALIDATION_NOT_ESTABLISHED", "POST_OBSERVATION_MECHANISM_DISCRIMINATION", "NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE", "NO_COMBINED_MECHANISM_AUTHORIZATION", "NO_SCI_LC_001B_AUTHORIZATION", "GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED"],
    }


def generate() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = matrix_rows()
    matrix = {"schema_version": "ewp.sci_md_002b.matrix.v1", "row_count": len(rows), "rows": rows}
    jp = OUT / "SCI_MD_002B_CASE_MATRIX.json"
    jp.write_text(canonical(matrix))
    fields = list(rows[0])
    with (OUT / "SCI_MD_002B_CASE_MATRIX.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            row = dict(row)
            for k in ("comparator_ids", "refinement_companions"):
                row[k] = "|".join(row[k])
            w.writerow(row)
    (OUT / "SCI_MD_002B_PROTOCOL.json").write_text(json.dumps(protocol(sha(jp)), indent=2, sort_keys=True) + "\n")
    print(canonical({"row_count": len(rows), "matrix_sha256": sha(jp)}), end="")


def verify_generated() -> None:
    rows = matrix_rows()
    disk = json.loads((OUT / "SCI_MD_002B_CASE_MATRIX.json").read_text())
    proto = json.loads((OUT / "SCI_MD_002B_PROTOCOL.json").read_text())
    normalized_rows = json.loads(canonical(rows))
    expected_protocol = json.loads(canonical(protocol(sha(OUT / "SCI_MD_002B_CASE_MATRIX.json"))))
    if disk["rows"] != normalized_rows or disk["row_count"] != len(rows) or proto != expected_protocol:
        raise RuntimeError("generated artifacts differ from canonical generator")
    with (OUT / "SCI_MD_002B_CASE_MATRIX.csv").open(newline="") as f:
        if sum(1 for _ in csv.DictReader(f)) != len(rows):
            raise RuntimeError("CSV/JSON row mismatch")
    print(canonical({"status": "PASS", "row_count": len(rows)}), end="")


def simulate(row: dict[str, Any]) -> dict[str, Any]:
    if row["coupling"] == "TWO_WAY_DESIGN_BLOCKED":
        return {"status": "DESIGN_BLOCKED", "stop_reason": "SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED"}
    pbar = 7.0 if row["pressure_bar"] == "SYNTHETIC" else float(row["pressure_bar"])
    p = pbar * 1e5
    k0 = hydraulic_anchor()
    report_t = source_conditions().get(int(pbar), {"report_time_s": 30.0})["report_time_s"]
    cells = int(row["axial_cells"])
    wet = np.zeros(cells) if row["coupling"] == "SIMULTANEOUS" else foster_wetting_times(p, k0, cells)
    if row["coupling"] == "FOSTER_CLOSED_FORM":
        return {"status": "PASS", "front_m": min(H0, foster_front(report_t, p, k0)), "full_wetting_s": MU * PHI0 * H0**2 / (2*k0*(p+PCAP))}
    resistances, states = [], []
    for tw in wet:
        age = max(0.0, report_t - float(tw))
        sr, dr = particle_state(row["powder"], age, D0 * row["diffusivity_multiplier"], row["cmax"], row["radial_cells"])
        state = accommodation_state(sr, dr, row["accommodation"])
        resistances.append(state["resistance_ratio"])
        states.append(state)
    rrel = float(np.mean(resistances))
    q = k0 * AREA * p / (MU * H0 * rrel)
    full = MU * PHI0 * H0**2 / (2*k0*(p+PCAP))
    return {"status": "PASS", "pressure_bar": pbar, "report_time_s": report_t, "first_drip_s": full,
            "full_wetting_s": full, "inlet_flow_m3_s": q, "front_filling_flow_m3_s": 0.0 if report_t >= full else q,
            "swelling_storage_uptake_m3_s": 0.0, "outlet_flow_m3_s": q if report_t >= full else 0.0,
            "outlet_flow_kg_s": q * RHO if report_t >= full else 0.0, "relative_resistance": rrel,
            "min_porosity": min(s["porosity"] for s in states), "max_height_ratio": max(s["height_ratio"] for s in states),
            "min_permeability_ratio": min(s["permeability_ratio"] for s in states), "wetting_times_s": wet.tolist(),
            "liquid_balance_residual_m3": 0.0, "clipping": False}


def references() -> None:
    k = hydraulic_anchor()
    checks = []
    for p in (5e5, 9e5):
        t = 3.2
        s = foster_front(t, p, k)
        tw = MU * PHI0 * s*s / (2*k*(p+PCAP))
        checks.append(abs(tw-t) < 2e-14)
    checks += [accommodation_state(1.05, 1.01, 0)["height_ratio"] == 1,
               abs(accommodation_state(1.05, 1.01, 1)["porosity"]-PHI0) < 1e-14]
    sr0, _ = particle_state("M", 30, 0, .1, 24)
    checks.append(sr0 == 1)
    if not all(checks):
        raise RuntimeError("reference verification failed")
    print(canonical({"status": "PASS", "checks": len(checks)}), end="")


def pilot_selection() -> None:
    rows = {r["case_id"]: r for r in matrix_rows()}
    selected = [rows[x] for x in PILOT_IDS]
    for p in PRESSURES:
        if any(r["adjudicative"] and r["pressure_bar"] == p for r in selected):
            raise RuntimeError("pilot contains adjudicative source row")
    print(canonical({"pilot_row_ids": list(PILOT_IDS), "count": len(selected), "complete_source_triplet": False}), end="")


def record_atomic(directory: Path, case_id: str, record: dict[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    final = directory / f"{case_id}.json"
    if final.exists():
        raise FileExistsError(f"immutable record exists: {case_id}")
    body = dict(record)
    body["record_sha256"] = hashlib.sha256(canonical(record).encode()).hexdigest()
    tmp = directory / f".{case_id}.{os.getpid()}.tmp"
    tmp.write_text(canonical(body))
    os.replace(tmp, final)
    return final


def execute_pilot(bundle_arg: str) -> None:
    bundle = safe_bundle(Path(bundle_arg))
    records = bundle / "case_records"
    rows = {r["case_id"]: r for r in matrix_rows()}
    ledger = bundle / "process_ledger.jsonl"
    start_wall, start_utc = time.perf_counter(), utc()
    base = {"task_id": TASK, "lane_id": LANE_ID, "pid": os.getpid(), "parent_pid": os.getppid(), "command": " ".join(sys.argv), "working_directory": str(ROOT), "case_or_pilot": "PILOT_ATTEMPT1", "start_utc": start_utc, "status": "RUNNING"}
    with ledger.open("a") as f: f.write(canonical(base))
    completed, failures = 0, []
    for cid in PILOT_IDS:
        row = rows[cid]
        t0 = time.perf_counter()
        try:
            result = simulate(row)
            status = result["status"]
        except Exception as exc:
            result, status = {"error_type": type(exc).__name__, "error": str(exc)}, "NUMERICAL_FAILURE"
            failures.append(cid)
        record = {"schema_version": "ewp.sci_md_002b.case_record.v1", "task_id": TASK, "lane_id": LANE_ID,
                  "case_id": cid, "source_head": git("rev-parse", "HEAD"), "source_tree": git("rev-parse", "HEAD^{tree}"),
                  "protocol_sha256": sha(OUT/"SCI_MD_002B_PROTOCOL.json"), "matrix_sha256": sha(OUT/"SCI_MD_002B_CASE_MATRIX.json"),
                  "implementation_sha256": sha(Path(__file__)), "parameters": row, "command": " ".join(sys.argv),
                  "owner": "SOLE_SCI_MD_002B_WRITER_AND_EXECUTION_OWNER", "parent_pid": os.getppid(), "worker_pid": os.getpid(),
                  "start_utc": start_utc, "completion_utc": utc(), "wall_s": time.perf_counter()-t0, "numerical_status": status,
                  "stop_reason": None if status == "PASS" else result.get("stop_reason", status), "key_observables": result}
        record_atomic(records, cid, record)
        completed += status == "PASS"
    files = sorted(records.glob("*.json"))
    manifest = {"schema_version": "ewp.sci_md_002b.external_manifest.v1", "record_count": len(files),
                "records": [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in files],
                "ordered_record_aggregate_sha256": hashlib.sha256("".join(sha(p) for p in files).encode()).hexdigest(),
                "scientific_reducer_ran": False, "source_ordering_calculated": False, "complete_source_triplet": False}
    (bundle/"manifest.json").write_text(canonical(manifest))
    timing = {"source_head": git("rev-parse","HEAD"), "source_tree": git("rev-parse","HEAD^{tree}"), "row_count": len(PILOT_IDS),
              "completion_count": completed, "failure_count": len(failures), "failures": failures, "wall_s": time.perf_counter()-start_wall,
              "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024, "manifest_sha256": sha(bundle/"manifest.json"),
              "scientific_reducer_ran": False, "source_ordering_calculated": False}
    (bundle/"timing.json").write_text(canonical(timing))
    with ledger.open("a") as f: f.write(canonical({**base, "completion_utc": utc(), "status": "COMPLETE", "completion_count": completed}))
    print(canonical(timing), end="")


def verify_bundle(bundle_arg: str) -> None:
    bundle = safe_bundle(Path(bundle_arg))
    manifest = json.loads((bundle/"manifest.json").read_text())
    for item in manifest["records"]:
        p = bundle/"case_records"/item["name"]
        if p.stat().st_size != item["bytes"] or sha(p) != item["sha256"]:
            raise RuntimeError("external record mismatch")
    if manifest["complete_source_triplet"] or manifest["scientific_reducer_ran"]:
        raise RuntimeError("pilot authority boundary violated")
    print(canonical({"status":"PASS","record_count":manifest["record_count"],"manifest_sha256":sha(bundle/"manifest.json")}),end="")


def execute_adjudicative(bundle_arg: str, authority_arg: str | None) -> None:
    if not authority_arg:
        raise PermissionError("SCI_MD_002B_ADJUDICATIVE_EXECUTION_NOT_AUTHORIZED")
    a = json.loads(Path(authority_arg).read_text())
    required = {"authorization_token": ADJ_TOKEN, "source_head": git("rev-parse","HEAD"), "source_tree": git("rev-parse","HEAD^{tree}"),
                "protocol_hash": sha(OUT/"SCI_MD_002B_PROTOCOL.json"), "matrix_hash": sha(OUT/"SCI_MD_002B_CASE_MATRIX.json"),
                "implementation_hash": sha(Path(__file__)), "source_overlay_hash": sha(OVERLAY), "puckworks_lock": PUCK_COMMIT,
                "external_result_namespace": EXTERNAL_NAMESPACE, "worker_cap": 1}
    if any(a.get(k) != v for k,v in required.items()) or not a.get("authorized_row_set") or not a.get("authorization_date") or not a.get("owner_role"):
        raise PermissionError("SCI_MD_002B_MODEL_OR_AUTHORITY_INVALID")
    raise PermissionError("adjudicative executor intentionally unavailable in pre-execution tranche")


def reduce_results(bundle_arg: str) -> None:
    bundle = safe_bundle(Path(bundle_arg))
    manifest = json.loads((bundle/"manifest.json").read_text())
    if not manifest.get("adjudicative_authority_sha256"):
        raise PermissionError("pilot records cannot be scientifically reduced")
    raise NotImplementedError("adjudicative reduction awaits separate authority")


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for x in ("generate", "verify", "references", "pilot-select"): sp.add_parser(x)
    p = sp.add_parser("pilot-run"); p.add_argument("--bundle", required=True)
    p = sp.add_parser("execute-adjudicative"); p.add_argument("--bundle", required=True); p.add_argument("--authority")
    p = sp.add_parser("reduce"); p.add_argument("--bundle", required=True)
    p = sp.add_parser("verify-bundle"); p.add_argument("--bundle", required=True)
    a = ap.parse_args()
    {"generate": generate, "verify": verify_generated, "references": references, "pilot-select": pilot_selection}.get(a.cmd, lambda: None)()
    if a.cmd == "pilot-run": execute_pilot(a.bundle)
    elif a.cmd == "execute-adjudicative": execute_adjudicative(a.bundle, a.authority)
    elif a.cmd == "reduce": reduce_results(a.bundle)
    elif a.cmd == "verify-bundle": verify_bundle(a.bundle)


if __name__ == "__main__":
    main()
