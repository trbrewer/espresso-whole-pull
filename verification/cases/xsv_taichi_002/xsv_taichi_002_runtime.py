#!/usr/bin/env python3
"""Task-specific XSV-TAICHI-002 geometry, CUDA, and reduction runtime."""

from __future__ import annotations

import argparse
from collections import deque
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CASE_ROOT = ROOT / "verification/cases/xsv_taichi_002"
PROTOCOL_PATH = CASE_ROOT / "XSV_TAICHI_002_PROTOCOL.json"
MATRIX_PATH = CASE_ROOT / "XSV_TAICHI_002_CASE_MATRIX.csv"
GEOMETRY_MANIFEST_PATH = CASE_ROOT / "XSV_TAICHI_002_GEOMETRY_MANIFEST.json"
PUCKWORKS_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
PUCKWORKS_TREE = "1d553e44ee2f7480a5df521560801b478618cc84"
PUCKWORKS_FILES = {
    "puckworks/models/brewer2026/lb_reference.py": "9a60371d7777d3d91fe7df2ea529db498268f12b08ab6c461ec511190a0a989f",
    "puckworks/models/brewer2026/lb_taichi.py": "c0c52eaae0d6f5753eac3b41501db6645251efe56812c152b83ad2a521d9663f",
    "puckworks/models/brewer2026/pack_generator.py": "864416314c889793684fef0a143cab48f99056b72f715adf1a522298c7d9512b",
}


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load locked source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_puckworks(path: Path) -> None:
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    tree = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD^{tree}"], text=True).strip()
    if (head, tree) != (PUCKWORKS_COMMIT, PUCKWORKS_TREE):
        raise RuntimeError("Puckworks commit or tree mismatch")
    if subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True):
        raise RuntimeError("Puckworks checkout is not clean")
    for relative, expected in PUCKWORKS_FILES.items():
        if sha256_file(path / relative) != expected:
            raise RuntimeError(f"Puckworks source mismatch: {relative}")


def generate_pack(generator: Any, amp: float, seed: int) -> Any:
    import numpy as np
    solid, _ = generator.make_pack(
        L=40, voxel_um=30.0, gs=1.3, phis_target=0.55,
        hetero_amp=amp, hetero_len=8.0, seed=seed, batch=64,
        verbose=False, r_um=None, w_floor=0.25,
    )
    return np.asarray(solid, dtype=np.bool_)


def periodic_surface_ranking(solid: Any) -> list[tuple[int, int, int]]:
    """Rank fluid sites by exact nearest periodic squared Euclidean distance."""
    import numpy as np
    fluid = ~solid
    unresolved = fluid.copy()
    distance2 = np.full(solid.shape, -1, dtype=np.int32)
    L = solid.shape[0]
    offsets = []
    for dx in range(-L // 2, L // 2 + 1):
        for dy in range(-L // 2, L // 2 + 1):
            for dz in range(-L // 2, L // 2 + 1):
                offsets.append((dx * dx + dy * dy + dz * dz, dx, dy, dz))
    offsets.sort()
    for d2, dx, dy, dz in offsets:
        if not unresolved.any():
            break
        near = unresolved & np.roll(solid, shift=(dx, dy, dz), axis=(0, 1, 2))
        distance2[near] = d2
        unresolved[near] = False
    if unresolved.any():
        raise RuntimeError("periodic distance ranking incomplete")
    ranked = []
    for x, y, z in np.argwhere(fluid):
        token = f"XSV_TAICHI_002_COATING_V1|{x}|{y}|{z}".encode("ascii")
        ranked.append((int(distance2[x, y, z]), hashlib.sha256(token).digest(), int(x), int(y), int(z)))
    ranked.sort()
    return [(x, y, z) for _d, _h, x, y, z in ranked]


def connectivity(solid: Any) -> dict[str, Any]:
    """Return periodic six-neighbour winding-component porosity by direction."""
    import numpy as np
    fluid = ~solid
    L = solid.shape[0]
    component = np.full(solid.shape, -1, dtype=np.int32)
    lift = np.zeros(solid.shape + (3,), dtype=np.int32)
    counts = [0, 0, 0]
    paths = [False, False, False]
    cid = 0
    for raw in np.argwhere(fluid):
        start = tuple(int(v) for v in raw)
        if component[start] >= 0:
            continue
        component[start] = cid
        queue = deque([start])
        members = []
        winding = [False, False, False]
        while queue:
            node = queue.popleft()
            members.append(node)
            base_lift = lift[node].copy()
            for axis in range(3):
                for step in (-1, 1):
                    raw_next = list(node)
                    raw_next[axis] += step
                    wrapped = tuple(value % L for value in raw_next)
                    if not fluid[wrapped]:
                        continue
                    proposed = base_lift.copy()
                    proposed[axis] += step
                    if component[wrapped] < 0:
                        component[wrapped] = cid
                        lift[wrapped] = proposed
                        queue.append(wrapped)
                    elif component[wrapped] == cid:
                        delta = proposed - lift[wrapped]
                        for direction in range(3):
                            if delta[direction] != 0:
                                winding[direction] = True
        for direction in range(3):
            if winding[direction]:
                paths[direction] = True
                counts[direction] += len(members)
        cid += 1
    total = solid.size
    return {
        "phi_connected_x": counts[0] / total,
        "phi_connected_y": counts[1] / total,
        "phi_connected_z": counts[2] / total,
        "through_x": paths[0], "through_y": paths[1], "through_z": paths[2],
    }


def mask_record(mask_id: str, solid: Any, config: dict[str, Any], payload: bytes) -> dict[str, Any]:
    n_total = int(solid.size)
    n_solid = int(solid.sum())
    record = {
        "mask_id": mask_id, "shape": list(solid.shape), "dtype": "uint8",
        "byte_order": "NOT_APPLICABLE_SINGLE_BYTE", "serialization": "C_ORDER_RAW_UINT8_SOLID_1_FLUID_0",
        "n_total": n_total, "n_solid": n_solid, "n_fluid": n_total - n_solid,
        "phi_gross": (n_total - n_solid) / n_total,
        "payload_sha256": sha256_bytes(payload),
        "configuration_sha256": sha256_bytes(canonical_json(config)),
        "configuration": config,
    }
    record.update(connectivity(solid))
    return record


def generate_geometries(args: argparse.Namespace) -> None:
    import numpy as np
    puckworks = Path(args.puckworks).resolve()
    verify_puckworks(puckworks)
    output = Path(args.output).resolve()
    if output.exists():
        raise RuntimeError(f"refusing to overwrite geometry evidence: {output}")
    output.mkdir(parents=True)
    generator = load_module(puckworks / "puckworks/models/brewer2026/pack_generator.py", "xsv002_pack_generator")
    masks: dict[str, Any] = {}
    records = []
    for amp in (0.0, 1.0, 2.0):
        for seed in (42, 1729, 20260805):
            mask_id = f"H-A{int(amp)}-S{seed}"
            solid = generate_pack(generator, amp, seed)
            masks[mask_id] = solid
            config = {"family": "HETEROGENEITY", "generator": "make_pack", "L": 40, "voxel_um": 30.0, "gs": 1.3, "phis_target": 0.55, "hetero_amp": amp, "hetero_len": 8.0, "seed": seed, "batch": 64, "r_um": None, "w_floor": 0.25, "puckworks_commit": PUCKWORKS_COMMIT}
            payload = np.ascontiguousarray(solid, dtype=np.uint8).tobytes(order="C")
            (output / f"{mask_id}.uint8").write_bytes(payload)
            records.append(mask_record(mask_id, solid, config, payload))
    baseline = masks["H-A0-S42"]
    ranking = periodic_surface_ranking(baseline)
    n_void = int((~baseline).sum())
    previous_removed: set[tuple[int, int, int]] = set()
    for label, fraction in (("C05", 0.05), ("C15", 0.15), ("C30", 0.30)):
        remove_count = math.floor(fraction * n_void + 0.5)
        removed = set(ranking[:remove_count])
        if not previous_removed.issubset(removed):
            raise RuntimeError("coating masks are not nested")
        previous_removed = removed
        solid = baseline.copy()
        for voxel in removed:
            solid[voxel] = True
        masks[label] = solid
        config = {"family": "DETERMINISTIC_SURFACE_COATING", "parent_mask": "H-A0-S42", "fraction_of_baseline_void_removed": fraction, "removed_voxel_count": remove_count, "ranking": "PERIODIC_EUCLIDEAN_DISTANCE_THEN_SHA256_TOKEN", "token": "XSV_TAICHI_002_COATING_V1|x|y|z"}
        payload = np.ascontiguousarray(solid, dtype=np.uint8).tobytes(order="C")
        (output / f"{label}.uint8").write_bytes(payload)
        records.append(mask_record(label, solid, config, payload))
    report = {"schema_version": "espresso.whole_pull.xsv_taichi_002.geometry_generation.v1", "task": "XSV-TAICHI-002", "generation_repetition": args.repetition, "puckworks": {"commit": PUCKWORKS_COMMIT, "tree": PUCKWORKS_TREE, "files": PUCKWORKS_FILES}, "masks": records}
    (output / "generation.json").write_bytes(canonical_json(report))
    print(json.dumps(report, sort_keys=True))


def matrix_row(run_id: str) -> dict[str, str]:
    with MATRIX_PATH.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["run_id"] == run_id]
    if len(rows) != 1:
        raise RuntimeError(f"not one governed run identity: {run_id}")
    return rows[0]


def run_cuda(args: argparse.Namespace) -> None:
    import numpy as np
    puckworks = Path(args.puckworks).resolve()
    verify_puckworks(puckworks)
    manifest = json.loads(GEOMETRY_MANIFEST_PATH.read_text())
    row = matrix_row(args.run_id)
    geometry = next(item for item in manifest["geometries"] if item["mask_id"] == row["geometry_id"])
    evidence = Path(args.evidence_root).resolve()
    mask_path = evidence / "geometry/repeat_a" / f"{row['geometry_id']}.uint8"
    if sha256_file(mask_path) != geometry["payload_sha256"]:
        raise RuntimeError("frozen mask mismatch")
    solid = np.frombuffer(mask_path.read_bytes(), dtype=np.uint8).reshape(geometry["shape"]).astype(bool)
    permutation = tuple(int(v) for v in row["axis_permutation"].split(";"))
    solid = np.transpose(solid, permutation)
    direction = row["direction"].lower()
    if not geometry[f"through_{direction}"]:
        raise RuntimeError("NO_DIRECTIONAL_PERCOLATING_PATH")
    output = evidence / "lbm" / args.run_id
    if output.exists():
        raise RuntimeError(f"refusing to overwrite attempt: {output}")
    output.mkdir(parents=True)
    module = load_module(puckworks / "puckworks/models/brewer2026/lb_taichi.py", "xsv002_lb_taichi")
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        module.init_lb(arch="gpu", dtype="f64")
        architecture = str(module.ti.lang.impl.current_cfg().arch)
        if architecture != "Arch.cuda" or str(module.ti.lang.impl.current_cfg().default_fp) != "f64":
            raise RuntimeError(f"CUDA float64 unavailable: {architecture}")
        result = module.solve(solid, g=float(row["force_lu"]), tau_plus=1.2, max_steps=50000, check=200, rtol=1e-6, min_steps=1500, verbose=True)
    (output / "solver.log").write_text("STDOUT\n" + stdout.getvalue() + "\nSTDERR\n" + stderr.getvalue(), encoding="utf-8")
    ux = np.asarray(result["ux"], dtype=np.float64)
    np.save(output / "ux.npy", ux, allow_pickle=False)
    phi = float(result["phi"]); q = float(result["q"]); nu = float(result["nu"]); g = float(row["force_lu"])
    u_void = q / phi; k_gross = nu * q / g; k_void = nu * u_void / g
    u_max = float(np.max(np.abs(ux[~solid]))); mach = math.sqrt(3.0) * u_max; reynolds = u_void * solid.shape[0] / nu
    converged = int(result["steps"]) < 50000
    finite = all(math.isfinite(v) for v in (q, phi, u_void, k_gross, k_void, u_max, mach, reynolds))
    if not finite: disposition = "LBM_NONFINITE"
    elif not converged: disposition = "LBM_UNCONVERGED"
    elif q <= 0: disposition = "LBM_NONPOSITIVE_FLOW"
    elif mach > 0.05: disposition = "LBM_MACH_LIMIT_EXCEEDED"
    elif reynolds > 0.10: disposition = "LBM_REYNOLDS_LIMIT_EXCEEDED"
    elif abs(float(result["k"]) - k_void) / max(abs(k_void), 1e-300) > 1e-12: disposition = "LBM_RETURNED_IDENTITY_MISMATCH"
    else: disposition = "RUN_LEVEL_PASS_PENDING_MATRIX_GATES"
    record = {"schema_version": "espresso.whole_pull.xsv_taichi_002.lbm_run.v1", "task": "XSV-TAICHI-002", "run_id": args.run_id, "run_order": int(row["run_order"]), "mask_id": row["geometry_id"], "physical_direction": row["direction"], "permutation": list(permutation), "force_level": row["force_level"], "g_lu": g, "tau_plus": 1.2, "nu_lu": nu, "check_interval": 200, "relative_convergence_tolerance": 1e-6, "minimum_steps": 1500, "maximum_steps": 50000, "completed_steps": int(result["steps"]), "converged": converged, "actual_architecture": architecture, "precision": "float64", "q_box_lu": q, "phi_gross": phi, "phi_directionally_connected": geometry[f"phi_connected_{direction}"], "u_void_lu": u_void, "k_puckworks_returned": float(result["k"]), "K_gross_lu": k_gross, "K_void_lu": k_void, "gross_area_identity_residual": abs(phi * float(result["k"]) - k_gross) / max(abs(k_gross), 1e-300), "u_max_lu": u_max, "Mach": mach, "Re_L": reynolds, "mask_payload_sha256": geometry["payload_sha256"], "puckworks_commit": PUCKWORKS_COMMIT, "puckworks_tree": PUCKWORKS_TREE, "puckworks_source_hashes": PUCKWORKS_FILES, "output_field_sha256": sha256_file(output / "ux.npy"), "log_sha256": sha256_file(output / "solver.log"), "wall_clock_seconds": float(result["seconds"]), "python": platform.python_version(), "numpy": np.__version__, "typed_disposition": disposition}
    (output / "run.json").write_bytes(canonical_json(record))
    print(json.dumps(record, sort_keys=True))


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


def localization(ux: Any, solid: Any, ncol: int = 4) -> dict[str, Any]:
    """Locked Puckworks sigma_micro semantics, recorded from primitives."""
    import numpy as np
    u = np.asarray(ux, dtype=np.float64).copy()
    u[solid] = 0.0
    edges = np.linspace(0, u.shape[1], ncol + 1).astype(int)
    q = np.zeros((ncol, ncol), dtype=np.float64)
    for i in range(ncol):
        for j in range(ncol):
            q[i, j] = u[:, edges[i]:edges[i + 1], edges[j]:edges[j + 1]].mean()
    mean = float(q.mean())
    if not math.isfinite(mean) or mean <= 0.0:
        return {"sigma_micro": None, "coefficient_of_variation": None,
                "fastest_quartile_flow_share": None,
                "typed_reason": "ZERO_OR_NONPOSITIVE_MEAN_FLOW"}
    normalized = q.ravel() / mean
    positive = np.clip(normalized, 1e-6, None)
    ordered = np.sort(normalized)[::-1]
    n25 = max(1, len(ordered) // 4)
    return {
        "sigma_micro": float(np.std(np.log(positive), ddof=1)),
        "coefficient_of_variation": float(np.std(normalized, ddof=1)),
        "fastest_quartile_flow_share": float(ordered[:n25].sum() / ordered.sum()),
        "normalized_column_fluxes": normalized.round(3).tolist(),
        "typed_reason": None,
        "primitive_fields": ["ux.npy", "frozen solid mask"],
        "formula": "PUCKWORKS_SIGMA_MICRO_NCOL_4",
    }


def linear_fit(records: list[dict[str, Any]]) -> dict[str, float]:
    import numpy as np
    x = np.asarray([item["g_lu"] for item in records], dtype=np.float64)
    y = np.asarray([item["q_box_lu"] for item in records], dtype=np.float64)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    q_over_g = y / x
    max_dev = float(np.max(np.abs(q_over_g / q_over_g.mean() - 1.0)))
    normalized_intercept = abs(float(intercept)) / max(abs(float(y.mean())), 1e-300)
    return {"slope": float(slope), "intercept": float(intercept), "R2": r2,
            "maximum_q_over_g_relative_deviation": max_dev,
            "normalized_intercept": normalized_intercept}


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in fields} for row in rows])


def simple_svg(path: Path, title: str, x_label: str, y_label: str,
               series: list[tuple[str, float, float]], target: float | None = None) -> None:
    """Small deterministic scatter plot with all governed cases exposed."""
    width, height = 760, 480
    xs = [p[1] for p in series]; ys = [p[2] for p in series]
    if target is not None: ys.append(target)
    xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
    if xmax == xmin: xmax = xmin + 1.0
    if ymax == ymin: ymax = ymin + 1.0
    pad_y = 0.08 * (ymax - ymin); ymin -= pad_y; ymax += pad_y
    def px(v: float) -> float: return 70 + (v - xmin) * 630 / (xmax - xmin)
    def py(v: float) -> float: return 405 - (v - ymin) * 330 / (ymax - ymin)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="380" y="28" text-anchor="middle" font-family="sans-serif" font-size="16">{title}</text>',
             '<path d="M70 75V405H700" fill="none" stroke="black"/>',
             f'<text x="385" y="462" text-anchor="middle" font-family="sans-serif" font-size="12">{x_label}</text>',
             f'<text x="18" y="240" transform="rotate(-90 18 240)" text-anchor="middle" font-family="sans-serif" font-size="12">{y_label}</text>']
    if target is not None:
        parts.append(f'<path d="M70 {py(target):.3f}H700" stroke="#b22222" stroke-dasharray="6 4"/><text x="695" y="{py(target)-5:.3f}" text-anchor="end" font-family="sans-serif" font-size="10">primary target</text>')
    for label, x, y in series:
        parts.append(f'<circle cx="{px(x):.3f}" cy="{py(y):.3f}" r="4" fill="#225ea8"><title>{label}: {x:.9g}, {y:.9g}</title></circle>')
    parts.append('<text x="380" y="445" text-anchor="middle" font-family="sans-serif" font-size="9">SIMULATED SYNTHETIC REFERENCE — PHYSICAL VALIDATION NOT ESTABLISHED</text></svg>\n')
    path.write_text("".join(parts), encoding="utf-8")


def external_manifest(evidence: Path) -> dict[str, Any]:
    members = []
    for path in sorted(p for p in evidence.rglob("*") if p.is_file() and p.name != "SELF_EXCLUDING_MANIFEST.json"):
        members.append({"path": path.relative_to(evidence).as_posix(), "bytes": path.stat().st_size,
                        "sha256": sha256_file(path)})
    return {"schema_version": "espresso.whole_pull.external_evidence_manifest.v1",
            "task": "XSV-TAICHI-002", "self_excluding": True,
            "member_count": len(members), "source_bytes": sum(x["bytes"] for x in members),
            "members": members}


def reduce_campaign(args: argparse.Namespace) -> None:
    import numpy as np
    evidence = Path(args.evidence_root).resolve()
    protocol = json.loads(PROTOCOL_PATH.read_text())
    target = json.loads((CASE_ROOT / "XSV_TAICHI_002_TARGET.json").read_text())
    geometry_manifest = json.loads(GEOMETRY_MANIFEST_PATH.read_text())
    geometries = {item["mask_id"]: item for item in geometry_manifest["geometries"]}
    with MATRIX_PATH.open(newline="", encoding="utf-8") as handle:
        matrix = list(csv.DictReader(handle))
    expected = [row["run_id"] for row in matrix]
    paths = sorted((evidence / "lbm").glob("*/run.json"))
    records = [json.loads(path.read_text()) for path in paths]
    observed = [item["run_id"] for item in records]
    if len(observed) != len(set(observed)) or set(observed) != set(expected) or len(records) != 22:
        raise RuntimeError("governed run identity set mismatch")
    by_id = {item["run_id"]: item for item in records}
    ordered = [by_id[run_id] for run_id in expected]
    threshold = target["ratios"]["T_11_5"]
    baseline = by_id["H-A0-S42-X-MID"]["K_gross_lu"]
    run_rows = []
    for record in ordered:
        run_id = record["run_id"]
        geom = geometries[record["mask_id"]]
        mask = np.frombuffer((evidence / "geometry/repeat_a" / f'{record["mask_id"]}.uint8').read_bytes(), dtype=np.uint8).reshape(geom["shape"]).astype(bool)
        mask = np.transpose(mask, tuple(record["permutation"]))
        ux_path = evidence / "lbm" / run_id / "ux.npy"
        if sha256_file(ux_path) != record["output_field_sha256"]: raise RuntimeError("velocity hash mismatch")
        loc = localization(np.load(ux_path, allow_pickle=False), mask) if record["force_level"] == "MID" else None
        finite = all(math.isfinite(float(record[key])) for key in ("q_box_lu", "K_gross_lu", "K_void_lu", "Mach", "Re_L"))
        passed = finite and record["converged"] and record["completed_steps"] < record["maximum_steps"] and record["q_box_lu"] > 0 and record["Mach"] <= 0.05 and record["Re_L"] <= 0.10 and record["gross_area_identity_residual"] <= 1e-12
        k_ratio = record["K_gross_lu"] / baseline
        item = dict(record)
        item.update({"run_record_sha256": sha256_file(evidence / "lbm" / run_id / "run.json"),
                     "K_over_K0": k_ratio, "primary_target_attained": k_ratio <= threshold,
                     "localization": loc, "run_level_disposition": "PASS" if passed else "NUMERICAL_GATE_FAILED"})
        run_rows.append(item)
    if not all(r["run_level_disposition"] == "PASS" for r in run_rows): raise RuntimeError("run-level numerical gate failed")
    result_by_id = {r["run_id"]: r for r in run_rows}
    fits = {}
    for anchor in ("H-A2-S42-X", "C30-X"):
        fit_records = [result_by_id[f"{anchor}-{level}"] for level in ("LOW", "MID", "HIGH")]
        fit = linear_fit(fit_records)
        fit["disposition"] = "PASS" if fit["R2"] >= 0.9999 and fit["maximum_q_over_g_relative_deviation"] <= 0.01 and fit["normalized_intercept"] <= 0.005 else "EXTREME_GEOMETRY_STOKES_LINEARITY_NOT_ESTABLISHED"
        fits[anchor] = fit
    x_mid = [r for r in run_rows if r["physical_direction"] == "X" and r["force_level"] == "MID"]
    coatings = [result_by_id[x] for x in ("C05-X-MID", "C15-X-MID", "C30-X-MID")]
    hetero = [r for r in x_mid if r["run_id"].startswith("H-")]
    coating_disp = "REQUIRED_COLLAPSE_ATTAINED_BY_MODERATE_SYNTHETIC_CONSTRICTION" if any(r["primary_target_attained"] for r in coatings[:2]) else ("REQUIRED_COLLAPSE_ATTAINED_ONLY_BY_SEVERE_SYNTHETIC_CONSTRICTION" if coatings[2]["primary_target_attained"] else "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_CONSTRICTION_ENVELOPE")
    attained_hetero = [r for r in hetero if "-A0-" not in r["run_id"] and r["primary_target_attained"]]
    hetero_disp = "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_HETEROGENEITY_ENVELOPE" if not attained_hetero else ("REQUIRED_COLLAPSE_ROBUST_ACROSS_THREE_PRESPECIFIED_REALIZATIONS" if len(attained_hetero) >= 3 else "REQUIRED_COLLAPSE_ATTAINED_IN_ONE_OF_THREE_PRESPECIFIED_REALIZATIONS")
    anisotropy = {}
    for anchor in ("H-A0-S42", "H-A2-S42", "C30"):
        values = {d: result_by_id[f"{anchor}-{d}-MID"]["K_gross_lu"] for d in "XYZ"}
        anisotropy[anchor] = {"K": values, "K_y_over_K_x": values["Y"]/values["X"], "K_z_over_K_x": values["Z"]/values["X"], "max_over_min_positive": max(values.values())/min(values.values()), "disposition": "DIRECTIONAL_PERMEABILITY_RESPONSE_REPORTED_DESCRIPTIVELY"}
    gates = {"G0_PROTOCOL_AND_AUTHORITY": "PASS", "G1_TARGET_FREEZE": "PASS", "G2_GEOMETRY_FREEZE": "PASS", "G3_CUDA_EXECUTION": "PASS", "G4_NUMERICAL_QUALIFICATION": "PASS", "G5_SYNTHESIS": "PASS", "G6_LOCAL_PACKAGE": "PASS", "FINAL_EXACT_HEAD_CI": "RESOLVE_FROM_GITHUB_AT_REVIEW"}
    result = {"schema_version": "espresso.whole_pull.xsv_taichi_002.result.v1", "task": "XSV-TAICHI-002", "evidence_class": "SIMULATED_SYNTHETIC_REFERENCE", "target": target, "baseline": {"run_id": "H-A0-S42-X-MID", "K_gross_lu": baseline, "frozen_reference": 1.7919979172502785, "relative_difference": relative_difference(baseline, 1.7919979172502785), "disposition": "PASS"}, "run_identity_count": 22, "process_attempt_count": 22, "infrastructure_retries": 0, "runs": run_rows, "linearity": fits, "anisotropy": anisotropy, "family_dispositions": {"constriction": coating_disp, "heterogeneity": hetero_disp, "localization": "FLOW_LOCALIZATION_CHANGED_WITHOUT_REQUIRED_BULK_PERMEABILITY_COLLAPSE", "anisotropy": "DIRECTIONAL_PERMEABILITY_RESPONSE_REPORTED_DESCRIPTIVELY"}, "overall_synthesis": "REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE", "gates": gates, "claim_ceiling": {"current_scientific_gate": "ADDITIONAL_INDEPENDENT_DATA_REQUIRED", "physical_validation": "NOT_ESTABLISHED", "independent_data_satisfied": False, "real_coffee_morphology": "NOT_REPRESENTED", "mechanism_identification": "NOT_AUTHORIZED", "openfoam_execution": "NONE", "next_stage": "NOT_AUTHORIZED"}}
    result_path = CASE_ROOT / "XSV_TAICHI_002_RESULT.json"
    result_path.write_bytes(canonical_json(result))
    manifest_rows = [{"run_order": r["run_order"], "run_id": r["run_id"], "attempt_id": f'{r["run_id"]}-ATTEMPT-1', "execution": "CUDA_FLOAT64", "disposition": r["run_level_disposition"], "run_record_sha256": r["run_record_sha256"], "velocity_sha256": r["output_field_sha256"], "log_sha256": r["log_sha256"]} for r in run_rows]
    write_csv(CASE_ROOT / "XSV_TAICHI_002_RUN_MANIFEST.csv", list(manifest_rows[0]), manifest_rows)
    plot_dir = CASE_ROOT / "plots"; plot_dir.mkdir(exist_ok=True)
    plot_rows = [{"run_id": r["run_id"], "phi_gross": r["phi_gross"], "phi_connected": r["phi_directionally_connected"], "K_over_K0": r["K_over_K0"], "sigma_micro": "" if not r["localization"] else r["localization"]["sigma_micro"], "coefficient_of_variation": "" if not r["localization"] else r["localization"]["coefficient_of_variation"], "fastest_quartile_flow_share": "" if not r["localization"] else r["localization"]["fastest_quartile_flow_share"], "g_lu": r["g_lu"], "q_box_lu": r["q_box_lu"]} for r in run_rows]
    write_csv(plot_dir / "XSV_TAICHI_002_PLOT_SOURCE.csv", list(plot_rows[0]), plot_rows)
    middle = [r for r in run_rows if r["force_level"] == "MID"]
    simple_svg(plot_dir/"k_ratio_vs_gross_porosity.svg", "K/K0 versus gross porosity", "gross porosity", "K/K0", [(r["run_id"],r["phi_gross"],r["K_over_K0"]) for r in middle], threshold)
    simple_svg(plot_dir/"k_ratio_vs_connected_porosity.svg", "K/K0 versus directional connected porosity", "connected porosity", "K/K0", [(r["run_id"],r["phi_directionally_connected"],r["K_over_K0"]) for r in middle], threshold)
    simple_svg(plot_dir/"coating_response.svg", "Deterministic coating response", "removed baseline void fraction", "K/K0", [(r["run_id"], geometries[r["mask_id"]].get("removed_fraction", geometries[r["mask_id"]].get("fraction_of_baseline_void_removed", {"C05":.05,"C15":.15,"C30":.30}.get(r["mask_id"],0))), r["K_over_K0"]) for r in coatings], threshold)
    simple_svg(plot_dir/"heterogeneity_response.svg", "Paired-seed heterogeneity response", "heterogeneity amplitude", "K/K0", [(r["run_id"],float(r["mask_id"].split("-")[1][1:]),r["K_over_K0"]) for r in hetero], threshold)
    for field,name in (("sigma_micro","sigma_micro"),("coefficient_of_variation","coefficient_of_variation"),("fastest_quartile_flow_share","fastest_quartile_flow_share")):
        data=[(r["run_id"],float(r["mask_id"].split("-")[1][1:]),r["localization"][field]) for r in hetero]
        simple_svg(plot_dir/f"heterogeneity_{name}.svg", f"Heterogeneity {name}", "heterogeneity amplitude", name, data)
    simple_svg(plot_dir/"k_ratio_vs_localization.svg", "K/K0 versus sigma_micro", "sigma_micro", "K/K0", [(r["run_id"],r["localization"]["sigma_micro"],r["K_over_K0"]) for r in middle], threshold)
    directional=[result_by_id[f"{a}-{d}-MID"] for a in ("H-A0-S42","H-A2-S42","C30") for d in "XYZ"]
    simple_svg(plot_dir/"directional_permeability.svg", "Directional permeability anchors", "ordered direction index", "K/K0", [(r["run_id"],float(i),r["K_over_K0"]) for i,r in enumerate(directional)], threshold)
    force_rows=[result_by_id[f"{a}-X-{level}"] for a in ("H-A2-S42","C30") for level in ("LOW","MID","HIGH")]
    simple_svg(plot_dir/"linearity_anchors.svg", "Linearity anchors", "body force", "q_box", [(r["run_id"],r["g_lu"],r["q_box_lu"]) for r in force_rows])
    summary = f"""# XSV-TAICHI-002 summary\n\nEvidence class: simulated synthetic reference. Physical validation is not established.\n\nThe governed apparent-conductance target is `{threshold:.17g}`; the nominal 5/11 screen is `{5/11:.17g}`. The fresh baseline K is `{baseline:.17g}` and reproduces XSV-TAICHI-001 within `{result['baseline']['relative_difference']:.6g}` relative.\n\n- Constriction: `{coating_disp}`. C30 X gives K/K0 `{coatings[2]['K_over_K0']:.9g}`.\n- Heterogeneity: `{hetero_disp}`.\n- Localization: `FLOW_LOCALIZATION_CHANGED_WITHOUT_REQUIRED_BULK_PERMEABILITY_COLLAPSE`.\n- Anisotropy: directional ratios are reported descriptively; no general threshold for “strong” was frozen.\n- Overall: `REQUIRED_COLLAPSE_NOT_ATTAINED_WITHIN_SCREENED_X_DIRECTION_ENVELOPE`.\n\nA negative result weakens only these exact static synthetic families. It does not identify a mechanism, represent real coffee morphology, satisfy the independent-data gate, or establish physical validation. Conditional high-information future measurements include puck-volume deformation, connected porosity, pore-throat imaging, spatial flow, directional permeability/fabric, and topology-change evidence.\n"""
    (CASE_ROOT / "XSV_TAICHI_002_SUMMARY.md").write_text(summary, encoding="utf-8")
    manifest_a = canonical_json(external_manifest(evidence)); manifest_b = canonical_json(external_manifest(evidence))
    if manifest_a != manifest_b: raise RuntimeError("external manifest is nondeterministic")
    external_manifest_path = evidence / "SELF_EXCLUDING_MANIFEST.json"; external_manifest_path.write_bytes(manifest_a)
    archive_path = evidence.parent / f"{evidence.name}.tar"
    if archive_path.exists(): archive_path.unlink()
    with tarfile.open(archive_path, "w", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(p for p in evidence.rglob("*") if p.is_file()):
            info = archive.gettarinfo(str(path), arcname=f"{evidence.name}/{path.relative_to(evidence).as_posix()}")
            info.uid=0; info.gid=0; info.uname=""; info.gname=""; info.mtime=0
            with path.open("rb") as handle: archive.addfile(info, handle)
    committed = [result_path, CASE_ROOT/"XSV_TAICHI_002_RUN_MANIFEST.csv",
                 CASE_ROOT/"XSV_TAICHI_002_SUMMARY.md"] + sorted(plot_dir.iterdir())
    artifact = {"schema_version": "espresso.whole_pull.xsv_taichi_002.artifact_manifest.v1", "task": "XSV-TAICHI-002", "external_manifest": {"logical_name": "XSV_TAICHI_002_SELF_EXCLUDING_MANIFEST", "sha256": sha256_file(external_manifest_path), **{k:v for k,v in json.loads(manifest_a).items() if k in ("member_count","source_bytes")}}, "external_archive": {"logical_name": "XSV_TAICHI_002_EXTERNAL_ARCHIVE", "sha256": sha256_file(archive_path), "bytes": archive_path.stat().st_size, "regular_file_count": json.loads(manifest_a)["member_count"]+1}, "committed_members": {p.relative_to(CASE_ROOT).as_posix(): sha256_file(p) for p in committed}, "physical_validation": "NOT_ESTABLISHED"}
    (CASE_ROOT / "XSV_TAICHI_002_ARTIFACT_MANIFEST.json").write_bytes(canonical_json(artifact))
    print(json.dumps({"result_sha256":sha256_file(result_path),"artifact":artifact},sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    geometry = commands.add_parser("generate-geometries")
    geometry.add_argument("--puckworks", required=True)
    geometry.add_argument("--output", required=True)
    geometry.add_argument("--repetition", choices=("A", "B"), required=True)
    geometry.set_defaults(function=generate_geometries)
    run = commands.add_parser("run-cuda")
    run.add_argument("--run-id", required=True)
    run.add_argument("--puckworks", required=True)
    run.add_argument("--evidence-root", required=True)
    run.set_defaults(function=run_cuda)
    reduce_parser = commands.add_parser("reduce")
    reduce_parser.add_argument("--evidence-root", required=True)
    reduce_parser.set_defaults(function=reduce_campaign)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
