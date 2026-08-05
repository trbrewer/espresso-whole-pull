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
    geometry = next(item for item in manifest["geometries"] if item["mask_id"] == row["mask_id"])
    evidence = Path(args.evidence_root).resolve()
    mask_path = evidence / "geometry/repeat_a" / f"{row['mask_id']}.uint8"
    if sha256_file(mask_path) != geometry["payload_sha256"]:
        raise RuntimeError("frozen mask mismatch")
    solid = np.frombuffer(mask_path.read_bytes(), dtype=np.uint8).reshape(geometry["shape"]).astype(bool)
    permutation = tuple(int(v) for v in row["permutation"].split(";"))
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
        result = module.solve(solid, g=float(row["g_lu"]), tau_plus=1.2, max_steps=50000, check=200, rtol=1e-6, min_steps=1500, verbose=True)
    (output / "solver.log").write_text("STDOUT\n" + stdout.getvalue() + "\nSTDERR\n" + stderr.getvalue(), encoding="utf-8")
    ux = np.asarray(result["ux"], dtype=np.float64)
    np.save(output / "ux.npy", ux, allow_pickle=False)
    phi = float(result["phi"]); q = float(result["q"]); nu = float(result["nu"]); g = float(row["g_lu"])
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
    record = {"schema_version": "espresso.whole_pull.xsv_taichi_002.lbm_run.v1", "task": "XSV-TAICHI-002", "run_id": args.run_id, "run_order": int(row["run_order"]), "mask_id": row["mask_id"], "physical_direction": row["direction"], "permutation": list(permutation), "force_level": row["force_level"], "g_lu": g, "tau_plus": 1.2, "nu_lu": nu, "check_interval": 200, "relative_convergence_tolerance": 1e-6, "minimum_steps": 1500, "maximum_steps": 50000, "completed_steps": int(result["steps"]), "converged": converged, "actual_architecture": architecture, "precision": "float64", "q_box_lu": q, "phi_gross": phi, "phi_directionally_connected": geometry[f"phi_connected_{direction}"], "u_void_lu": u_void, "k_puckworks_returned": float(result["k"]), "K_gross_lu": k_gross, "K_void_lu": k_void, "gross_area_identity_residual": abs(phi * float(result["k"]) - k_gross) / max(abs(k_gross), 1e-300), "u_max_lu": u_max, "Mach": mach, "Re_L": reynolds, "mask_payload_sha256": geometry["payload_sha256"], "puckworks_commit": PUCKWORKS_COMMIT, "puckworks_tree": PUCKWORKS_TREE, "puckworks_source_hashes": PUCKWORKS_FILES, "output_field_sha256": sha256_file(output / "ux.npy"), "log_sha256": sha256_file(output / "solver.log"), "wall_clock_seconds": float(result["seconds"]), "python": platform.python_version(), "numpy": np.__version__, "typed_disposition": disposition}
    (output / "run.json").write_bytes(canonical_json(record))
    print(json.dumps(record, sort_keys=True))


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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
