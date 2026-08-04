#!/usr/bin/env python3
"""Bounded runner and reducer for XSV-TAICHI-001.

Scientific inputs live in the frozen protocol. Full masks and run products are
written only to an explicitly supplied external evidence directory.
"""

from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_PROTOCOL.json"
EXPECTED_PUCKWORKS_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    geometry = subparsers.add_parser("generate-geometry")
    geometry.add_argument("--case-id", choices=("CH33", "SP32", "M0A"), required=True)
    geometry.add_argument("--puckworks", required=True)
    geometry.add_argument("--output", required=True)
    geometry.set_defaults(function=generate_geometry)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
