#!/usr/bin/env python3
"""Bounded runner and reducer for XSV-TAICHI-001.

Scientific inputs live in the frozen protocol. Full masks and run products are
written only to an explicitly supplied external evidence directory.
"""

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
import sys
from typing import Any, Dict, Iterable, Tuple

sys.dont_write_bytecode = True

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_PROTOCOL.json"
EXPECTED_PUCKWORKS_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
CASE_MATRIX_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_CASE_MATRIX.csv"
GEOMETRY_MANIFEST_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_GEOMETRY_MANIFEST.json"

for required_root_member in (
    ROOT / "SOURCE_PACKAGE_MANIFEST.json",
    PROTOCOL_PATH,
    ROOT / "scripts/xsv_taichi_001.py",
):
    if not required_root_member.is_file():
        raise RuntimeError(
            f"invalid repository root for governed XSV-TAICHI-001 runtime: {ROOT}"
        )


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import locked source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def geometry_config(protocol: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    return {
        "schema_version": "espresso.whole_pull.xsv_taichi_001.geometry_config.v1",
        "task": protocol["task"],
        "case_id": case_id,
        "definition": protocol["geometry_definitions"][case_id],
        "mask_convention": protocol["quantities"]["mask"],
        "puckworks_commit": protocol["sources"]["puckworks"]["commit"],
    }


def generate_mask(case_id: str, protocol: Dict[str, Any], puckworks: Path) -> np.ndarray:
    definition = protocol["geometry_definitions"][case_id]
    if case_id == "CH33":
        solid = np.zeros(tuple(definition["shape"]), dtype=np.bool_)
        solid[:, :, definition["solid_z"][0]] = True
        solid[:, :, definition["solid_z"][1]] = True
        return solid
    if case_id == "SP32":
        # Exact mask construction from locked lb_reference.sphere_case. Calling
        # sphere_case itself would also execute a flow solve before G1 freeze.
        L = int(definition["L"])
        c_nom = float(definition["c_nom"])
        radius = L * (3.0 * c_nom / (4.0 * np.pi)) ** (1.0 / 3.0)
        x, y, z = np.meshgrid(*(np.arange(L),) * 3, indexing="ij")
        center = (L - 1) / 2.0
        return (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2 <= radius**2
    if case_id == "M0A":
        module = load_module(
            puckworks / "puckworks/models/brewer2026/pack_generator.py",
            "xsv_taichi_001_pack_generator",
        )
        solid, _metadata = module.make_pack(
            L=int(definition["L"]),
            voxel_um=float(definition["voxel_um"]),
            gs=float(definition["gs"]),
            phis_target=float(definition["phis_target"]),
            hetero_amp=float(definition["hetero_amp"]),
            hetero_len=float(definition["hetero_len"]),
            seed=int(definition["seed"]),
            verbose=False,
        )
        return np.asarray(solid, dtype=np.bool_)
    raise ValueError(f"unapproved geometry: {case_id}")


def connected_descriptor(solid: np.ndarray, periodic_axes: Iterable[int]) -> Tuple[int, bool]:
    """Return nodes in x-through components and whether such a component exists."""
    fluid = ~solid
    shape = solid.shape
    periodic = set(periodic_axes)
    seen = np.zeros(shape, dtype=np.bool_)
    through_count = 0
    through = False
    for start_y, start_z in np.argwhere(fluid[0]):
        start = (0, int(start_y), int(start_z))
        if seen[start]:
            continue
        queue = deque([start])
        seen[start] = True
        component = []
        touches_outlet = False
        while queue:
            node = queue.popleft()
            component.append(node)
            if node[0] == shape[0] - 1:
                touches_outlet = True
            for axis in range(3):
                for direction in (-1, 1):
                    candidate = list(node)
                    candidate[axis] += direction
                    if candidate[axis] < 0 or candidate[axis] >= shape[axis]:
                        if axis not in periodic:
                            continue
                        candidate[axis] %= shape[axis]
                    nxt = tuple(candidate)
                    if fluid[nxt] and not seen[nxt]:
                        seen[nxt] = True
                        queue.append(nxt)
        if touches_outlet:
            through = True
            through_count += len(component)
    return through_count, through


def generate_geometry(args: argparse.Namespace) -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol["sources"]["puckworks"]["commit"] != EXPECTED_PUCKWORKS_COMMIT:
        raise RuntimeError("protocol Puckworks lock differs")
    puckworks = Path(args.puckworks).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    solid = generate_mask(args.case_id, protocol, puckworks)
    payload = np.ascontiguousarray(solid, dtype=np.uint8).tobytes(order="C")
    config = geometry_config(protocol, args.case_id)
    config_payload = canonical_json_bytes(config)
    periodic_names = protocol["geometry_definitions"][args.case_id].get(
        "periodic", ["x", "y", "z"]
    )
    # x is deliberately nonperiodic for the inlet-to-outlet diagnostic.
    periodic_axes = [{"x": 0, "y": 1, "z": 2}[name] for name in periodic_names if name != "x"]
    connected_count, is_through = connected_descriptor(solid, periodic_axes)
    n_total = int(solid.size)
    n_solid = int(solid.sum())
    n_fluid = n_total - n_solid
    descriptor = {
        "schema_version": "espresso.whole_pull.xsv_taichi_001.geometry_descriptor.v1",
        "case_id": args.case_id,
        "shape": list(solid.shape),
        "dtype": "uint8",
        "n_total": n_total,
        "n_solid": n_solid,
        "n_fluid": n_fluid,
        "phi_gross": n_fluid / n_total,
        "n_x_connected_fluid": connected_count,
        "phi_x_connected": connected_count / n_total,
        "x_through_connected": is_through,
        "payload_sha256": sha256_bytes(payload),
        "geometry_config_sha256": sha256_bytes(config_payload),
    }
    (output / f"{args.case_id}.uint8").write_bytes(payload)
    (output / f"{args.case_id}.config.json").write_bytes(config_payload)
    (output / f"{args.case_id}.descriptor.json").write_bytes(canonical_json_bytes(descriptor))
    print(json.dumps(descriptor, sort_keys=True))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_lbm_case(run_id: str) -> Dict[str, str]:
    with CASE_MATRIX_PATH.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["run_id"] == run_id]
    if len(rows) != 1 or rows[0]["family"] != "LBM":
        raise RuntimeError(f"run ID is not one exact governed LBM case: {run_id}")
    return rows[0]


def run_lbm(args: argparse.Namespace) -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    geometry_manifest = json.loads(GEOMETRY_MANIFEST_PATH.read_text(encoding="utf-8"))
    case = load_lbm_case(args.run_id)
    geometry = next(
        row for row in geometry_manifest["geometries"] if row["case_id"] == case["geometry"]
    )
    evidence_root = Path(args.evidence_root).resolve()
    mask_path = evidence_root / "geometry/repeat_a" / f"{case['geometry']}.uint8"
    if not mask_path.is_file() or sha256_file(mask_path) != geometry["payload_sha256"]:
        raise RuntimeError(f"frozen mask identity mismatch: {mask_path}")
    shape = tuple(geometry["shape"])
    solid = np.frombuffer(mask_path.read_bytes(), dtype=np.uint8).reshape(shape).astype(bool)
    output_dir = evidence_root / "lbm" / args.run_id
    if output_dir.exists():
        raise RuntimeError(f"refusing to overwrite retained run: {output_dir}")
    output_dir.mkdir(parents=True)
    puckworks = Path(args.puckworks).resolve()
    g_lu = float(case["g_lu"])
    tau_plus = float(protocol["lbm_settings"]["tau_plus"])
    kwargs = {
        "g": g_lu,
        "tau_plus": tau_plus,
        "max_steps": int(case["max_steps"]),
        "check": int(protocol["lbm_settings"]["check_interval"]),
        "rtol": float(protocol["lbm_settings"]["relative_convergence_tolerance"]),
        "min_steps": int(protocol["lbm_settings"]["minimum_steps"]),
        "verbose": True,
    }
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
        if case["backend"] == "NUMPY_REFERENCE":
            module = load_module(
                puckworks / "puckworks/models/brewer2026/lb_reference.py",
                f"xsv_lb_reference_{args.run_id.replace('-', '_')}",
            )
            actual_architecture = "CPU_NUMPY"
            result = module.solve(solid, **kwargs)
        elif case["backend"] == "TAICHI":
            module = load_module(
                puckworks / "puckworks/models/brewer2026/lb_taichi.py",
                f"xsv_lb_taichi_{args.run_id.replace('-', '_')}",
            )
            requested = case["architecture"].lower()
            module.init_lb(arch="gpu" if requested == "cuda" else "cpu", dtype="f64")
            actual_architecture = str(module.ti.lang.impl.current_cfg().arch)
            if requested == "cuda" and actual_architecture != "Arch.cuda":
                raise RuntimeError(f"CUDA substitution detected: {actual_architecture}")
            if str(module.ti.lang.impl.current_cfg().default_fp) != "f64":
                raise RuntimeError("Taichi float64 configuration not active")
            result = module.solve(solid, **kwargs)
        else:
            raise RuntimeError(f"unapproved backend: {case['backend']}")
    log_payload = (
        "STDOUT\n" + captured_stdout.getvalue() + "\nSTDERR\n" + captured_stderr.getvalue()
    ).encode("utf-8")
    log_path = output_dir / "solver.log"
    log_path.write_bytes(log_payload)
    ux = np.asarray(result["ux"], dtype=np.float64)
    velocity_path = output_dir / "ux.npy"
    np.save(velocity_path, ux, allow_pickle=False)
    fluid = ~solid
    q_box = float(result["q"])
    phi_gross = float(result["phi"])
    nu_lu = float(result["nu"])
    u_void = q_box / phi_gross
    k_returned = float(result["k"])
    k_gross = nu_lu * q_box / g_lu
    k_void = nu_lu * u_void / g_lu
    u_max = float(np.max(np.abs(ux[fluid])))
    mach = math.sqrt(3.0) * u_max
    reynolds = u_void * shape[0] / nu_lu
    finite = all(
        math.isfinite(value)
        for value in (q_box, phi_gross, u_void, k_returned, k_gross, k_void, u_max, mach, reynolds)
    )
    completed_steps = int(result["steps"])
    converged = completed_steps < int(case["max_steps"])
    if not finite:
        disposition = "LBM_NONFINITE"
    elif not converged:
        disposition = "LBM_UNCONVERGED"
    elif mach > protocol["thresholds"]["mach_max"]:
        disposition = "LBM_MACH_LIMIT_EXCEEDED"
    elif reynolds > protocol["thresholds"]["Re_L_max"]:
        disposition = "LBM_REYNOLDS_LIMIT_EXCEEDED"
    else:
        disposition = "RUN_LEVEL_PASS_PENDING_MATRIX_GATES"
    record = {
        "schema_version": "espresso.whole_pull.xsv_taichi_001.lbm_run.v1",
        "task": "XSV-TAICHI-001",
        "run_id": args.run_id,
        "case_id": case["geometry"],
        "backend": case["backend"],
        "actual_architecture": actual_architecture,
        "precision": "float64",
        "puckworks_commit": protocol["sources"]["puckworks"]["commit"],
        "puckworks_tree": protocol["sources"]["puckworks"]["tree"],
        "puckworks_source_hashes": protocol["sources"]["puckworks"]["files"],
        "mask_payload_sha256": geometry["payload_sha256"],
        "g_lu": g_lu,
        "tau_plus": tau_plus,
        "nu_lu": nu_lu,
        "check_interval": kwargs["check"],
        "rtol": kwargs["rtol"],
        "min_steps": kwargs["min_steps"],
        "max_steps": kwargs["max_steps"],
        "completed_steps": completed_steps,
        "converged": converged,
        "q_box_lu": q_box,
        "phi_gross": phi_gross,
        "phi_x_connected": geometry["phi_x_connected"],
        "u_void_lu": u_void,
        "k_puckworks_returned": k_returned,
        "K_gross_lu": k_gross,
        "K_void_lu": k_void,
        "u_max_lu": u_max,
        "Mach": mach,
        "Re_L": reynolds,
        "wall_clock_seconds": float(result["seconds"]),
        "output_field_sha256": sha256_file(velocity_path),
        "log_sha256": sha256_file(log_path),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "typed_disposition": disposition,
    }
    record_path = output_dir / "run.json"
    record_path.write_bytes(canonical_json_bytes(record))
    print(json.dumps(record, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    geometry = subparsers.add_parser("generate-geometry")
    geometry.add_argument("--case-id", choices=("CH33", "SP32", "M0A"), required=True)
    geometry.add_argument("--puckworks", required=True)
    geometry.add_argument("--output", required=True)
    geometry.set_defaults(function=generate_geometry)
    lbm = subparsers.add_parser("run-lbm")
    lbm.add_argument("--run-id", required=True)
    lbm.add_argument("--puckworks", required=True)
    lbm.add_argument("--evidence-root", required=True)
    lbm.set_defaults(function=run_lbm)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
