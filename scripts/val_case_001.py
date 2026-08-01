#!/usr/bin/env python3
"""VAL-CASE-001 deterministic input generation, execution, and reduction."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import pathlib
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_COMMIT = "39c7bf0658c344728258ba1b4f8b935a4e889d7d"
BASE_TREE = "85711011a96ebaa46a77b5165aec0ab46e676542"
ARTIFACT_ID = "VAL-CASE-001-OPENFOAM12-20260801"
EXECUTABLE_SHA256 = "0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c"
PRIMARY = 0.05
HALF = 0.025
PRIMARY_FRACTIONS = {"pc": 0.025, "pshut": 0.025}
HALF_FRACTIONS = {"pc": 0.0125, "pshut": 0.0125}
COMMON_TIMES = (10.0, 15.0, 20.0, 25.0, 30.0)
PARAMETERS = {
    "Cu": ("machineBoundary", "upstreamCompliance", 2.0e-11, "m3/Pa"),
    "Qfree": ("machineBoundary", "freeFlowRate", 6.0e-6, "m3/s"),
    "Ru": ("machineBoundary", "upstreamResistance", 2.0e11, "Pa s/m3"),
    "k0": ("poroelasticCompaction", "stressFreePermeabilityM2", 4.74023506749502e-15, "m2"),
    "pc": ("poroelasticCompaction", "criticalCompactionPressurePa", 1239155.0, "Pa"),
    "phi0": ("poroelasticCompaction", "stressFreePorosity", 0.4, "1"),
    "pshut": ("machineBoundary", "shutoffPressure", 1.2e6, "Pa gauge"),
}
STAGE_A_PARAMETERS = tuple(sorted(PARAMETERS))
STAGE_C_PARAMETERS = ("k0", "pc", "phi0")
CONDITIONS = {"LOW": ("PE-4", 5.0e5), "MID": ("PE-3", 9.0e5), "HIGH": ("PE-5", 1.1e6)}
PARENT_HASHES = {
    "config/reference_R0.json": "67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286",
    "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json": "6a9128a1f98ca8b3f87b45592e8d21dda3d77f7325aef43230cdef94402461d4",
    "validation/wp03/WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.json": "dc687f13c8881c481d5674a226c0236d0f0a3d1e53458a9ea5558b02dfcb3456",
}
FEATURES = {
    "SET_A": (("outlet_flow_m3_s", 1.5e-6), ("cup_beverage_mass_kg", 0.04)),
    "SET_B": (("basketPressurePa", 9.0e5),),
    "SET_C": (("deformation", 0.1), ("volumeWeightedMechanicalPorosity", 0.4)),
    "SET_D": (("first_drip_s", 10.0),),
}


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def finite_difference(y_minus: list[float] | None, y_plus: list[float] | None,
                      p_minus: float | None, p_plus: float | None,
                      y_base: list[float] | None = None, p_base: float | None = None) -> list[float]:
    """Central or declared one-sided physical-unit finite difference."""
    if y_minus is not None and y_plus is not None and p_minus is not None and p_plus is not None:
        return [(b - a) / (p_plus - p_minus) for a, b in zip(y_minus, y_plus)]
    if y_base is None or p_base is None:
        raise ValueError("one-sided difference requires baseline")
    if y_plus is not None and p_plus is not None:
        return [(b - a) / (p_plus - p_base) for a, b in zip(y_base, y_plus)]
    if y_minus is not None and p_minus is not None:
        return [(b - a) / (p_base - p_minus) for a, b in zip(y_minus, y_base)]
    raise ValueError("no finite-difference endpoint")


def normalized_sensitivity(physical: list[float], parameter: float,
                           fixed_scales: list[float]) -> list[float]:
    if any(not math.isfinite(x) or x <= 0.0 for x in fixed_scales):
        raise ValueError("normalization scales must be finite and positive")
    return [parameter * value / scale for value, scale in zip(physical, fixed_scales)]


def write_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_root(root: pathlib.Path) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if not subprocess.call(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head], cwd=root) == 0:
        raise SystemExit("authorized base is not an ancestor")
    for rel, expected in PARENT_HASHES.items():
        actual = sha256(root / rel)
        if actual != expected:
            raise SystemExit(f"parent hash mismatch: {rel}: {actual}")
    lock = load_json(root / "dependencies/puckworks.lock.json")
    if (lock["checkout_commit"], lock["checkout_tree_sha"]) != (
        "fc61c4670ec7bf801e40bb391aab16048b8da26b",
        "1d553e44ee2f7480a5df521560801b478618cc84",
    ):
        raise SystemExit("Puckworks lock mismatch")


def parents(root: pathlib.Path) -> tuple[dict, dict, dict]:
    verify_root(root)
    return (
        load_json(root / "config/reference_R0.json"),
        load_json(root / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json"),
        load_json(root / "validation/wp03/WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.json"),
    )


def mechanics(wp03: dict) -> dict:
    ref, controls = wp03["reference"], wp03["nonlinear_controls"]
    return {
        "model": "waszkiewicz2025FinitePhi",
        "stressFreePorosity": ref["stress_free_porosity"],
        "criticalCompactionPressurePa": ref["critical_compaction_pressure_pa"],
        "stressFreePermeabilityM2": ref["matched_stress_free_permeability_m2"],
        "nonlinearRelativeTolerance": controls["nonlinear_relative_tolerance"],
        "nonlinearAbsoluteTolerance": controls["nonlinear_absolute_tolerance"],
        "nonlinearMaximumIterations": controls["nonlinear_maximum_iterations"],
        "nonlinearUnderRelaxation": controls["nonlinear_under_relaxation"],
        "machineFluxRelativeTolerance": controls["machine_flux_relative_tolerance"],
    }


def base_config(root: pathlib.Path, branch: str, condition: str) -> dict:
    base, wp02, wp03 = parents(root)
    cfg = copy.deepcopy(base)
    cfg["scenario_id"] = f"VAL_CASE_001_{condition}_{branch}"
    cfg["governance"] = {
        "task": "VAL-CASE-001",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "case_class": "EXPLORATORY",
        "scientific_purpose": "VALIDATION_DESIGN_AND_PRACTICAL_IDENTIFIABILITY",
    }
    cfg["claim_ceiling"] = "VALIDATION_SUPPORT_ONLY; PHYSICAL_VALIDATION NOT_ESTABLISHED"
    if condition == "MACHINE_MID":
        cfg["pressureBoundaryModel"] = "lumpedMachineCompliance"
        cfg["machineBoundary"] = copy.deepcopy(wp02["case_matrix"]["MC-2"]["machineBoundary"])
    else:
        _, pressure = CONDITIONS[condition]
        cfg["pressureBoundaryModel"] = "prescribedPressure"
        cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = pressure
    if branch == "finite":
        cfg["bedMechanicsModel"] = "waszkiewiczQuasiStaticCompaction"
        cfg["poroelasticCompaction"] = mechanics(wp03)
        if condition == "HIGH":
            cfg["poroelasticCompaction"]["nonlinearUnderRelaxation"] = 0.7
    else:
        cfg["bedMechanicsModel"] = "none"
        cfg.pop("poroelasticCompaction", None)
    return cfg


def perturb(cfg: dict, parameter: str, fraction: float) -> tuple[float, float]:
    group, key, baseline, _ = PARAMETERS[parameter]
    if group not in cfg:
        raise ValueError(f"{parameter} inactive for configuration")
    value = baseline * (1.0 + fraction)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"invalid perturbed value for {parameter}")
    if parameter == "phi0" and not 0.0 < value < 1.0:
        raise ValueError("phi0 outside physical domain")
    if parameter == "pc" and value <= 1.1e6:
        raise ValueError("pc does not exceed maximum prescribed drop")
    cfg[group][key] = value
    return baseline, value


def case_record(root: pathlib.Path, config_dir: pathlib.Path, case_id: str, cfg: dict,
                stage: str, condition: str, branch: str, parameter: str | None = None,
                fraction: float | None = None) -> dict:
    cfg["scenario_id"] = f"VAL_CASE_001_{case_id}"
    path = config_dir / f"{case_id}.json"
    payload = canonical_bytes(cfg)
    path.write_bytes(payload)
    changed = None
    if parameter is not None:
        _, _, baseline, units = PARAMETERS[parameter]
        changed = {
            "parameter": parameter,
            "baseline_value": baseline,
            "perturbed_value": baseline * (1.0 + float(fraction)),
            "units": units,
            "fraction": fraction,
            "basis": "LOCAL_DERIVATIVE_PROBE_NOT_UNCERTAINTY_INTERVAL",
        }
    return {
        "case_id": case_id,
        "stage": stage,
        "condition": condition,
        "model_form_branch": branch,
        "parent_configuration": "config/reference_R0.json",
        "parent_sha256": PARENT_HASHES["config/reference_R0.json"],
        "change": changed,
        "derived_configuration_sha256": hashlib.sha256(payload).hexdigest(),
        "execute": True,
    }


def generate_stage_a(root: pathlib.Path, run_root: pathlib.Path) -> list[dict]:
    out, records = run_root / "configs", []
    out.mkdir(parents=True, exist_ok=True)
    finite = base_config(root, "finite", "MACHINE_MID")
    records.append(case_record(root, out, "A-BASE", copy.deepcopy(finite), "A", "MACHINE_MID", "finite"))
    records.append(case_record(root, out, "A-REPEAT", copy.deepcopy(finite), "A", "MACHINE_MID", "finite"))
    records.append(case_record(root, out, "A-UNIVERSAL", base_config(root, "universal", "MACHINE_MID"), "A", "MACHINE_MID", "universal"))
    for p in STAGE_A_PARAMETERS:
        step = PRIMARY_FRACTIONS.get(p, PRIMARY)
        for sign, label in ((-1.0, "MINUS"), (1.0, "PLUS")):
            cfg = copy.deepcopy(finite)
            perturb(cfg, p, sign * step)
            records.append(case_record(root, out, f"A-{p}-{label}", cfg, "A", "MACHINE_MID", "finite", p, sign * step))
    return records


def generate_rest(root: pathlib.Path, run_root: pathlib.Path, selected: list[str]) -> list[dict]:
    out, records = run_root / "configs", []
    finite = base_config(root, "finite", "MACHINE_MID")
    for p in selected:
        step = HALF_FRACTIONS.get(p, HALF)
        for sign, label in ((-1.0, "MINUS"), (1.0, "PLUS")):
            cfg = copy.deepcopy(finite)
            perturb(cfg, p, sign * step)
            records.append(case_record(root, out, f"B-{p}-{label}", cfg, "B", "MACHINE_MID", "finite", p, sign * step))
    for condition in CONDITIONS:
        finite_c = base_config(root, "finite", condition)
        records.append(case_record(root, out, f"C-{condition}-FINITE", copy.deepcopy(finite_c), "C", condition, "finite"))
        records.append(case_record(root, out, f"C-{condition}-UNIVERSAL", base_config(root, "universal", condition), "C", condition, "universal"))
        for p in STAGE_C_PARAMETERS:
            step = PRIMARY_FRACTIONS.get(p, PRIMARY)
            for sign, label in ((-1.0, "MINUS"), (1.0, "PLUS")):
                cfg = copy.deepcopy(finite_c)
                perturb(cfg, p, sign * step)
                records.append(case_record(root, out, f"C-{condition}-{p}-{label}", cfg, "C", condition, "finite", p, sign * step))
    return records


def trace_path(run_root: pathlib.Path, case_id: str) -> pathlib.Path:
    return run_root / "cases" / case_id / "postProcessing/wholePull/0/traces.csv"


def run_one(root: pathlib.Path, run_root: pathlib.Path, executable: pathlib.Path,
            ranks: int, case_id: str) -> dict:
    case_dir = run_root / "cases" / case_id
    if case_dir.exists():
        raise RuntimeError(f"refusing to overwrite {case_dir}")
    case_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", str(root / "scripts/prepare_case.py"), "--root", str(root),
                    "--config", str(run_root / "configs" / f"{case_id}.json"),
                    "--case-dir", str(case_dir), "--nprocs", str(ranks)], check=True)
    started = time.time()
    commands = [(["blockMesh"], "log.blockMesh"), (["checkMesh"], "log.checkMesh")]
    if ranks > 1:
        commands.append((["decomposePar", "-force"], "log.decomposePar"))
        solver = ["mpirun", "-np", str(ranks), str(executable), "-parallel"]
    else:
        solver = [str(executable)]
    commands.append((solver, "log.solver"))
    env = dict(os.environ, ESPRESSO_CASE_ROOT=str(case_dir))
    for command, logname in commands:
        with (case_dir / logname).open("wb") as log:
            subprocess.run(command, cwd=case_dir, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    trace = trace_path(run_root, case_id)
    if not trace.is_file():
        raise RuntimeError(f"missing trace for {case_id}")
    return {"case_id": case_id, "status": "COMPLETED", "wall_seconds": time.time() - started,
            "trace_sha256": sha256(trace), "trace_bytes": trace.stat().st_size}


def run_cases(root: pathlib.Path, run_root: pathlib.Path, executable: pathlib.Path,
              ranks: int, workers: int, records: list[dict]) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, root, run_root, executable, ranks, r["case_id"]): r["case_id"] for r in records}
        for future in as_completed(futures):
            cid = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"case_id": cid, "status": "FAILED", "error": str(exc)}
            results.append(result)
            print(json.dumps(result, sort_keys=True), flush=True)
    return sorted(results, key=lambda x: x["case_id"])


def read_trace(run_root: pathlib.Path, case_id: str) -> list[dict[str, float | str]]:
    with trace_path(run_root, case_id).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"empty trace: {case_id}")
    return rows


def interp(rows: list[dict], column: str, at: float) -> float:
    times = [float(r["time_s"]) for r in rows]
    values = [float(r[column]) for r in rows]
    endpoint_tolerance = 1.0e-9
    if at > times[-1] and at - times[-1] <= endpoint_tolerance:
        at = float(times[-1])
    if at < times[0] and times[0] - at <= endpoint_tolerance:
        at = float(times[0])
    if at < times[0] or at > times[-1]:
        raise ValueError(f"time {at} outside trace")
    for left in range(len(times) - 1):
        if times[left] <= at <= times[left + 1]:
            span = times[left + 1] - times[left]
            if span == 0.0:
                return values[left]
            fraction = (at - times[left]) / span
            return values[left] + fraction * (values[left + 1] - values[left])
    return values[-1]


def feature_vector(rows: list[dict], upto: str = "SET_D") -> tuple[list[str], list[float], list[float]]:
    order = ("SET_A", "SET_B", "SET_C", "SET_D")
    names, values, scales = [], [], []
    for set_id in order:
        for column, scale in FEATURES[set_id]:
            if column == "first_drip_s":
                value = float(rows[-1][column])
                names.append(f"{set_id}:{column}")
                values.append(value)
                scales.append(scale)
            else:
                for t in COMMON_TIMES:
                    raw = interp(rows, "predictedBedHeightRatio", t) if column == "deformation" else interp(rows, column, t)
                    value = 1.0 - raw if column == "deformation" else raw
                    names.append(f"{set_id}:{column}@{t:g}s")
                    values.append(value)
                    scales.append(scale)
        if set_id == upto:
            break
    return names, values, scales


def derivative(run_root: pathlib.Path, prefix: str, parameter: str, fraction: float) -> dict:
    minus = feature_vector(read_trace(run_root, f"{prefix}-{parameter}-MINUS"))
    plus = feature_vector(read_trace(run_root, f"{prefix}-{parameter}-PLUS"))
    names, ym, scales = minus
    yp = plus[1]
    baseline = PARAMETERS[parameter][2]
    physical = finite_difference(ym, yp, baseline * (1.0 - fraction), baseline * (1.0 + fraction))
    normalized = normalized_sensitivity(physical, baseline, scales)
    return {"names": names, "physical": physical, "normalized": normalized, "minus": ym, "plus": yp}


def select_top3(run_root: pathlib.Path) -> tuple[list[str], dict]:
    ranking = []
    detail = {}
    for p in STAGE_A_PARAMETERS:
        d = derivative(run_root, "A", p, PRIMARY_FRACTIONS.get(p, PRIMARY))
        score = max(abs(value) for value in d["normalized"])
        detail[p] = score
        ranking.append((-score, p))
    selected = [p for _, p in sorted(ranking)[:3]]
    return selected, detail


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)]


def _jacobi_eigenvalues_symmetric(matrix: list[list[float]]) -> list[float]:
    """Deterministic Jacobi eigenvalues for the small J^T J matrices here."""
    a = [row[:] for row in matrix]
    n = len(a)
    for _ in range(100 * max(1, n * n)):
        p, q, largest = 0, 0, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(a[i][j]) > largest:
                    p, q, largest = i, j, abs(a[i][j])
        if largest <= 1.0e-15:
            break
        angle = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
        cosine, sine = math.cos(angle), math.sin(angle)
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq
        a[q][q] = sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            if k in (p, q):
                continue
            akp, akq = a[k][p], a[k][q]
            a[k][p] = a[p][k] = cosine * akp - sine * akq
            a[k][q] = a[q][k] = sine * akp + cosine * akq
    return sorted((max(0.0, a[i][i]) for i in range(n)), reverse=True)


def svd_summary(jac: list[list[float]]) -> dict:
    if not jac or not jac[0] or any(not math.isfinite(x) for row in jac for x in row):
        raise ValueError("nonfinite or empty Jacobian")
    columns = _transpose(jac)
    gram = [[sum(x * y for x, y in zip(left, right)) for right in columns] for left in columns]
    singular = [math.sqrt(value) for value in _jacobi_eigenvalues_symmetric(gram)]
    lead = singular[0] if len(singular) else 0.0
    tolerances = (1e-2, 1e-3, 1e-4, 1e-6)
    ranks = {f"{tol:.0e}": sum(value > tol * lead for value in singular) if lead > 0 else 0 for tol in tolerances}
    condition = None
    if singular and singular[-1] > 0 and math.isfinite(singular[-1]):
        condition = float(singular[0] / singular[-1])
    return {"dimensions": [len(jac), len(jac[0])], "singular_values": singular,
            "condition_number": condition, "effective_rank_by_relative_tolerance": ranks,
            "effective_rank_range": [min(ranks.values()), max(ranks.values())]}


def correlation(jac: list[list[float]], parameters: tuple[str, ...]) -> dict:
    columns = _transpose(jac)
    norms = [math.sqrt(sum(value * value for value in column)) for column in columns]
    matrix = [[1.0 if i == j else 0.0 for j in range(len(parameters))] for i in range(len(parameters))]
    for i in range(len(parameters)):
        for j in range(i + 1, len(parameters)):
            value = sum(a * b for a, b in zip(columns[i], columns[j])) / (norms[i] * norms[j]) if norms[i] and norms[j] else 0.0
            matrix[i][j] = matrix[j][i] = value
    pairs = [{"parameters": [parameters[i], parameters[j]], "cosine": matrix[i][j]}
             for i in range(len(parameters)) for j in range(i + 1, len(parameters)) if abs(matrix[i][j]) >= 0.95]
    return {"parameters": list(parameters), "cosine_matrix": matrix, "near_collinear_pairs": pairs}


def analyze(root: pathlib.Path, run_root: pathlib.Path, executable: pathlib.Path) -> dict:
    selected, influence = select_top3(run_root)
    names, _, _ = feature_vector(read_trace(run_root, "A-BASE"))
    derivatives = {p: derivative(run_root, "A", p, PRIMARY_FRACTIONS.get(p, PRIMARY)) for p in STAGE_A_PARAMETERS}
    full_jac = [list(row) for row in zip(*(derivatives[p]["normalized"] for p in STAGE_A_PARAMETERS))]
    set_ends = {}
    for set_id in FEATURES:
        idx = max(i for i, n in enumerate(names) if n.startswith(set_id + ":")) + 1
        set_ends[set_id] = idx
    set_results = {}
    for set_id, end in set_ends.items():
        jac = full_jac[:end]
        set_results[set_id] = {"svd": svd_summary(jac), "correlation": correlation(jac, STAGE_A_PARAMETERS)}
    stability = {}
    for p in selected:
        primary = derivatives[p]["physical"]
        half = derivative(run_root, "B", p, HALF_FRACTIONS.get(p, HALF))["physical"]
        valid = [i for i, value in enumerate(primary) if abs(value) > 0.0]
        ratios = [half[i] / primary[i] for i in valid]
        ordered = sorted(abs(value) for value in ratios if math.isfinite(value))
        median = ((ordered[(len(ordered) - 1) // 2] + ordered[len(ordered) // 2]) / 2.0) if ordered else None
        stability[p] = {
            "sign_agreement_fraction": sum((primary[i] > 0) == (half[i] > 0) for i in valid) / len(valid) if valid else None,
            "median_magnitude_ratio": median,
            "maximum_absolute_ratio_minus_one": max((abs(value - 1.0) for value in ratios if math.isfinite(value)), default=None),
        }
    base = feature_vector(read_trace(run_root, "A-BASE"))[1]
    repeat = feature_vector(read_trace(run_root, "A-REPEAT"))[1]
    scales = feature_vector(read_trace(run_root, "A-BASE"))[2]
    differences = [b - a for a, b in zip(base, repeat)]
    repeatability = {"maximum_absolute_feature_difference": max(abs(value) for value in differences),
                     "maximum_scale_normalized_difference": max(abs(value) / scale for value, scale in zip(differences, scales)),
                     "exact_feature_vector_match": base == repeat}
    branch = {}
    for condition, finite_id, universal_id in [
        ("MACHINE_MID", "A-BASE", "A-UNIVERSAL"),
        *[(c, f"C-{c}-FINITE", f"C-{c}-UNIVERSAL") for c in CONDITIONS],
    ]:
        f = feature_vector(read_trace(run_root, finite_id))
        u = feature_vector(read_trace(run_root, universal_id))
        delta = [finite - universal for finite, universal in zip(f[1], u[1])]
        scaled = [abs(value) / scale for value, scale in zip(delta, f[2])]
        maximum_index = max(range(len(scaled)), key=scaled.__getitem__)
        branch[condition] = {"maximum_absolute_separation": max(abs(value) for value in delta),
                             "maximum_scale_normalized_separation": scaled[maximum_index],
                             "feature_of_maximum_scaled_separation": f[0][maximum_index],
                             "separation_vector": dict(zip(f[0], delta))}
    stage_c = {}
    for condition in CONDITIONS:
        cols = [derivative(run_root, f"C-{condition}", p, PRIMARY_FRACTIONS.get(p, PRIMARY))["normalized"] for p in STAGE_C_PARAMETERS]
        jac = [list(row) for row in zip(*cols)]
        stage_c[condition] = {"svd": svd_summary(jac), "correlation": correlation(jac, STAGE_C_PARAMETERS)}
    case_results = []
    for trace in sorted((run_root / "cases").glob("*/postProcessing/wholePull/0/traces.csv")):
        cid = trace.parents[3].name
        rows = read_trace(run_root, cid)
        last = rows[-1]
        case_results.append({"case_id": cid, "trace_sha256": sha256(trace), "rows": len(rows),
                             "final_time_s": float(last["time_s"]), "first_drip_s": float(last["first_drip_s"]),
                             "final_cup_mass_kg": float(last["cup_beverage_mass_kg"]),
                             "final_basket_pressure_pa": float(last["basketPressurePa"]),
                             "final_bed_height_ratio": float(last["predictedBedHeightRatio"])})
    result = {
        "schema_version": "espresso.validation.val_case_001.results.v1",
        "case_id": "VAL-CASE-001",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "planned_openfoam_case_executions": 47,
        "actual_openfoam_case_executions": len(case_results),
        "selected_derivative_stability_parameters": selected,
        "sensitivity_ranking": [{"parameter": p, "maximum_absolute_normalized_sensitivity": influence[p]} for p in sorted(influence, key=lambda p: (-influence[p], p))],
        "numerical_repeatability": repeatability,
        "derivative_stability": stability,
        "observable_sets": set_results,
        "stage_c_information": stage_c,
        "model_form_separation": branch,
        "physical_derivatives": {p: dict(zip(derivatives[p]["names"], derivatives[p]["physical"])) for p in STAGE_A_PARAMETERS},
        "normalized_sensitivities": {p: dict(zip(derivatives[p]["names"], derivatives[p]["normalized"])) for p in STAGE_A_PARAMETERS},
        "case_summaries": case_results,
        "practical_identifiability": "SCREENING_ONLY_WITHOUT_MEASUREMENT_UNCERTAINTY",
        "structural_identifiability": "NOT_ASSESSED",
        "experimental_variant_discrimination": "NOT_ASSESSED",
        "independent_dataset_disposition": "NO_ADDITIONAL_ADMISSIBLE_INDEPENDENT_DATASET_AT_LOCKED_EVIDENCE_STATE",
        "scientific_result_disposition": "VALIDATION_SUPPORT_SENSITIVITY_AND_IDENTIFIABILITY_SCREENING",
        "validation_framework_disposition": "PINNED_FRAMEWORK_USED_UNCHANGED",
        "claim_ceiling": "VALIDATION_SUPPORT_ONLY_PHYSICAL_VALIDATION_NOT_ESTABLISHED",
        "executable_sha256": EXECUTABLE_SHA256,
        "external_artifact_id": ARTIFACT_ID,
    }
    if len(case_results) != 47:
        raise ValueError(f"run count mismatch: {len(case_results)} != 47")
    if executable.exists() and sha256(executable) != EXECUTABLE_SHA256:
        raise ValueError("executable hash mismatch")
    return result


def inventory(run_root: pathlib.Path) -> dict:
    files = [p for p in run_root.rglob("*") if p.is_file()]
    h = hashlib.sha256()
    for path in sorted(files):
        rel = path.relative_to(run_root).as_posix()
        h.update(rel.encode() + b"\0" + sha256(path).encode() + b"\n")
    return {"artifact_id": ARTIFACT_ID, "file_count": len(files),
            "total_bytes": sum(p.stat().st_size for p in files), "aggregate_sha256": h.hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("generate-a", "select", "generate-rest", "run", "analyze", "inventory"))
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--run-root", type=pathlib.Path, required=True)
    parser.add_argument("--executable", type=pathlib.Path)
    parser.add_argument("--ranks", type=int, default=32)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--stage", choices=("a", "rest"))
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    root, run_root = args.root.resolve(), args.run_root.resolve()
    if args.command == "generate-a":
        records = generate_stage_a(root, run_root)
        write_json(run_root / "STAGE_A_INPUT_MANIFEST.json", {"records": records, "count": len(records)})
        print(len(records))
    elif args.command == "select":
        selected, detail = select_top3(run_root)
        value = {"selected": selected, "influence": detail, "selection_rule": "FROZEN_PROTOCOL"}
        write_json(run_root / "STAGE_B_SELECTION.json", value)
        print(json.dumps(value, sort_keys=True))
    elif args.command == "generate-rest":
        selected = load_json(run_root / "STAGE_B_SELECTION.json")["selected"]
        records = generate_rest(root, run_root, selected)
        write_json(run_root / "STAGE_BC_INPUT_MANIFEST.json", {"records": records, "count": len(records)})
        print(len(records))
    elif args.command == "run":
        if not args.executable or not args.stage:
            parser.error("run requires --executable and --stage")
        manifest = "STAGE_A_INPUT_MANIFEST.json" if args.stage == "a" else "STAGE_BC_INPUT_MANIFEST.json"
        records = load_json(run_root / manifest)["records"]
        results = run_cases(root, run_root, args.executable.resolve(), args.ranks, args.workers, records)
        write_json(run_root / f"STAGE_{args.stage.upper()}_EXECUTION.json", {"results": results})
        if any(r["status"] != "COMPLETED" for r in results):
            return 1
    elif args.command == "analyze":
        if not args.executable or not args.output:
            parser.error("analyze requires --executable and --output")
        result = analyze(root, run_root, args.executable.resolve())
        write_json(args.output, result)
        print(json.dumps({"status": "PASS", "runs": result["actual_openfoam_case_executions"]}))
    else:
        value = inventory(run_root)
        if args.output:
            write_json(args.output, value)
        print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
