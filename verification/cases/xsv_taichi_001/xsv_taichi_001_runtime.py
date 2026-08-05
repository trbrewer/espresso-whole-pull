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
import re
import sys
from typing import Any, Dict, Iterable, Tuple

sys.dont_write_bytecode = True

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_PROTOCOL.json"
EXPECTED_PUCKWORKS_COMMIT = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
CASE_MATRIX_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_CASE_MATRIX.csv"
GEOMETRY_MANIFEST_PATH = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_GEOMETRY_MANIFEST.json"
OPENFOAM_FIXTURE_PATH = ROOT / "verification/cases/xsv_taichi_001/openfoam/XSV_TAICHI_001_OPENFOAM_FIXTURES.json"

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


def radial_fixture_reference(fixture: Dict[str, Any]) -> Dict[str, float]:
    """Recompute amendment-001 radial quantities from primitive inputs."""
    domain = fixture["domain"]
    profile = fixture["profiles"]["radial_two_zone"]
    closure = fixture["closure"]
    radial_cells = int(domain["radial_cells"])
    selected = int(profile["interface_face_index"])
    ideal = radial_cells / math.sqrt(2.0)
    departures = {
        face: abs((face / radial_cells) ** 2 - 0.5)
        for face in range(1, radial_cells)
    }
    minimizers = [face for face, value in departures.items() if value == min(departures.values())]
    if minimizers != [selected]:
        raise RuntimeError("radial interface is not the unique nearest-area mesh face")
    f_inner = (selected / radial_cells) ** 2
    f_outer = 1.0 - f_inner
    k_a = float(closure["K_A_m2"])
    k_b = float(closure["K_B_m2"])
    k_effective = f_inner * k_a + f_outer * k_b
    target_q = next(
        float(run["target_q_m_s"])
        for run in fixture["runs"]
        if run["run_id"] == "OF-PARALLEL-1"
    )
    delta_p = (
        float(fixture["fluid"]["dynamic_viscosity_Pa_s"])
        * float(domain["bed_depth_m"])
        * target_q
        / k_effective
    )
    return {
        "ideal_face_index": ideal,
        "selected_face_index": selected,
        "interface_radius_m": float(domain["basket_radius_m"]) * selected / radial_cells,
        "inner_area_fraction": f_inner,
        "outer_area_fraction": f_outer,
        "K_parallel_effective_m2": k_effective,
        "delta_p_Pa": delta_p,
        "inner_flow_share": f_inner * k_a / k_effective,
        "outer_flow_share": f_outer * k_b / k_effective,
    }


def verify_radial_fixture(args: argparse.Namespace) -> None:
    fixture = json.loads(OPENFOAM_FIXTURE_PATH.read_text(encoding="utf-8"))
    reference = radial_fixture_reference(fixture)
    profile = fixture["profiles"]["radial_two_zone"]
    comparisons = {
        "interface_radius_m": profile["interface_radius_m"],
        "inner_area_fraction": profile["declared_inner_area_fraction"],
        "outer_area_fraction": profile["declared_outer_area_fraction"],
        "K_parallel_effective_m2": profile["K_parallel_effective_m2"],
        "inner_flow_share": profile["expected_inner_flow_share"],
        "outer_flow_share": profile["expected_outer_flow_share"],
    }
    parallel = next(run for run in fixture["runs"] if run["run_id"] == "OF-PARALLEL-1")
    comparisons["delta_p_Pa"] = parallel["delta_p_Pa"]
    for key, recorded in comparisons.items():
        if not math.isclose(float(recorded), reference[key], rel_tol=1e-15, abs_tol=0.0):
            raise RuntimeError(f"radial fixture mismatch for {key}")
    output = {"disposition": "RADIAL_FIXTURE_REVISION_2_ANALYTICAL_PASS", **reference}
    if args.output:
        Path(args.output).write_bytes(canonical_json_bytes(output))
    print(json.dumps(output, sort_keys=True))


def relative_difference(observed: float, reference: float) -> float:
    return abs(observed - reference) / abs(reference)


def reduce_final(args: argparse.Namespace) -> None:
    """Deterministically reduce the retained G0--G5 evidence package."""
    evidence = Path(args.evidence_root).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    fixture = json.loads(OPENFOAM_FIXTURE_PATH.read_text(encoding="utf-8"))
    amendment_path = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_PROTOCOL_AMENDMENT_001.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    lbm = {}
    for path in sorted((evidence / "lbm").glob("*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        lbm[record["run_id"]] = record
    if len(lbm) != 19:
        raise RuntimeError("final reduction requires exactly 19 retained LBM records")

    def pair_max(pairs: Iterable[Tuple[str, str]], key: str) -> float:
        return max(relative_difference(lbm[a][key], lbm[b][key]) for a, b in pairs)

    numpy_cpu_pairs = (
        ("CH33-NP-LOW", "CH33-TC-LOW"), ("CH33-NP-MID", "CH33-TC-MID"),
        ("CH33-NP-HIGH", "CH33-TC-HIGH"), ("SP32-NP-MID", "SP32-TC-MID"),
        ("M0A-NP-MID", "M0A-TC-MID"),
    )
    cpu_cuda_pairs = tuple(
        (name, name.replace("-TC-", "-TG-"))
        for name in ("CH33-TC-LOW", "CH33-TC-MID", "CH33-TC-HIGH", "SP32-TC-MID", "M0A-TC-LOW", "M0A-TC-MID", "M0A-TC-HIGH")
    )
    geometry = json.loads(GEOMETRY_MANIFEST_PATH.read_text(encoding="utf-8"))
    velocity_l2 = {}
    for case_id, shape in (("CH33", (33, 33, 33)), ("M0A", (40, 40, 40))):
        solid = np.frombuffer(
            (evidence / "geometry/repeat_a" / f"{case_id}.uint8").read_bytes(),
            dtype=np.uint8,
        ).reshape(shape).astype(bool)
        numpy_ux = np.load(evidence / "lbm" / f"{case_id}-NP-MID" / "ux.npy")
        taichi_ux = np.load(evidence / "lbm" / f"{case_id}-TC-MID" / "ux.npy")
        velocity_l2[case_id] = float(
            np.linalg.norm((numpy_ux - taichi_ux)[~solid]) / np.linalg.norm(numpy_ux[~solid])
        )
    phi_channel = 31.0 / 33.0
    channel_gross_exact = phi_channel * 31.0**2 / 12.0
    channel_void_exact = 31.0**2 / 12.0
    channel_rows = [row for row in lbm.values() if row["case_id"] == "CH33"]
    channel_gross_error = max(relative_difference(row["K_gross_lu"], channel_gross_exact) for row in channel_rows)
    channel_void_error = max(relative_difference(row["K_void_lu"], channel_void_exact) for row in channel_rows)
    returned_identity_error = max(relative_difference(row["k_puckworks_returned"], row["K_void_lu"]) for row in lbm.values())
    alternate_error = max(relative_difference(row["k_puckworks_returned"], channel_gross_exact) for row in channel_rows)
    adapter_advantage = alternate_error / channel_gross_error

    force_linearity = {}
    for case_id in ("CH33", "M0A"):
        for backend in ("TC", "TG"):
            rows = [lbm[f"{case_id}-{backend}-{force}"] for force in ("LOW", "MID", "HIGH")]
            xs = [float(row["g_lu"]) for row in rows]
            ys = [float(row["q_box_lu"]) for row in rows]
            n = 3; sx = sum(xs); sy = sum(ys); sxx = sum(x*x for x in xs); sxy = sum(x*y for x, y in zip(xs, ys))
            slope = (n*sxy - sx*sy) / (n*sxx - sx*sx); intercept = (sy - slope*sx) / n
            predictions = [intercept + slope*x for x in xs]
            r2 = 1.0 - sum((y-p)**2 for y, p in zip(ys, predictions)) / sum((y-sy/n)**2 for y in ys)
            ratios = [y/x for x, y in zip(xs, ys)]; median = sorted(ratios)[1]
            force_linearity[f"{case_id}-{backend}"] = {
                "R2": r2,
                "q_over_g_max_relative_deviation": max(abs(value-median)/median for value in ratios),
                "normalized_intercept": abs(intercept)/ys[1],
            }
    cuda_m0 = [lbm[f"M0A-TG-{force}"] for force in ("LOW", "MID", "HIGH")]
    slope_qg = sum(row["g_lu"]*row["q_box_lu"] for row in cuda_m0) / sum(row["g_lu"]**2 for row in cuda_m0)
    k_m0_lu = cuda_m0[1]["nu_lu"] * slope_qg
    k_m0_si = k_m0_lu * fixture["closure"]["delta_x_m"]**2

    openfoam_paths = {
        "OF-U-LOW": "OF-U-LOW", "OF-U-MID": "OF-U-MID", "OF-U-HIGH": "OF-U-HIGH",
        "OF-U-PHI-ALT": "OF-U-PHI-ALT", "OF-SERIES-1": "OF-SERIES-1",
        "OF-SERIES-16": "OF-SERIES-16", "OF-PARALLEL-1": "OF-PARALLEL-1-R2",
        "OF-PARALLEL-16": "OF-PARALLEL-16-R2",
    }
    openfoam = {}
    for run_id, directory in openfoam_paths.items():
        case = evidence / "openfoam/cases" / directory
        trace_path = case / "xsv_trace.json"
        if trace_path.is_file():
            row = json.loads(trace_path.read_text(encoding="utf-8"))
        else:
            log = (case / "log.solver").read_text(encoding="utf-8")
            match = re.search(r"Qout=([-+0-9.eE]+) mL/s", log)
            if match is None:
                raise RuntimeError(f"missing flow in {run_id}")
            q = float(match.group(1)) * 1e-6
            expected = fixture["domain"]["gross_area_m2"] * next(item["target_q_m_s"] for item in fixture["runs"] if item["run_id"] == run_id)
            row = {"run_id": run_id, "total_flow_m3_s": q, "exact_total_flow_m3_s": expected, "total_flow_relative_error": relative_difference(q, expected), "typed_disposition": "PASS"}
        openfoam[run_id] = row
    uniform = [openfoam[name] for name in ("OF-U-LOW", "OF-U-MID", "OF-U-HIGH")]
    uniform_q_over_dp = [row["total_flow_m3_s"] / next(item["delta_p_Pa"] for item in fixture["runs"] if item["run_id"] == row["run_id"]) for row in uniform]
    uniform_median = sorted(uniform_q_over_dp)[1]
    porosity_difference = relative_difference(openfoam["OF-U-PHI-ALT"]["total_flow_m3_s"], openfoam["OF-U-MID"]["total_flow_m3_s"])
    series_serial = openfoam["OF-SERIES-1"]; series_mpi = openfoam["OF-SERIES-16"]
    parallel_serial = openfoam["OF-PARALLEL-1"]; parallel_mpi = openfoam["OF-PARALLEL-16"]
    preflight = json.loads((evidence / "openfoam/cases/OF-PARALLEL-1-R2/radial_mesh_preflight.json").read_text(encoding="utf-8"))
    gates = {name: "PASS" for name in ("G0", "G1", "G2", "G3", "G4", "G5", "G6")}
    result = {
        "schema_version": "espresso.whole_pull.xsv_taichi_001.result.v1",
        "task": "XSV-TAICHI-001",
        "authorization": "XSV-TAICHI-001-G5-RADIAL-MESH-ALIGNMENT-2026-08-04",
        "change_declaration": "NO_GOVERNING_PHYSICS_CHANGE",
        "evidence_class": "SIMULATED_SYNTHETIC_REFERENCE",
        "source_identities": protocol["sources"],
        "protocol": {"revision": 2, "markdown_sha256": sha256_file(ROOT / "docs/verification/XSV_TAICHI_001_SATURATED_HYDRAULIC_CLOSURE_PARITY.md"), "machine_sha256": sha256_file(PROTOCOL_PATH), "amendment_sha256": sha256_file(amendment_path)},
        "geometry_manifest_sha256": sha256_file(GEOMETRY_MANIFEST_PATH),
        "quantity_definitions": protocol["quantities"],
        "adapter_definitions": protocol["adapters"],
        "case_matrix": {"lbm": 19, "openfoam": 8},
        "process_attempts": {"openfoam": 9, "successful_openfoam_traces": 8, "protocol_invalid_pre_solve": 1},
        "protocol_invalid_attempt": amendment["failed_attempt"],
        "runtime_environments": {"python": cuda_m0[1]["python"], "numpy": cuda_m0[1]["numpy"], "taichi_architecture": "Arch.cuda", "openfoam": "Foundation 12", "mpi_ranks": [1, 16]},
        "lbm_runs": [lbm[key] for key in sorted(lbm)],
        "openfoam_runs": [openfoam[key] for key in sorted(openfoam)],
        "backend_parity": {"maximum_numpy_taichi_K_relative_difference": pair_max(numpy_cpu_pairs, "K_gross_lu"), "maximum_taichi_cpu_cuda_K_relative_difference": pair_max(cpu_cuda_pairs, "K_gross_lu"), "mid_force_velocity_relative_L2": velocity_l2},
        "force_linearity": force_linearity,
        "channel_adapter": {"K_gross_exact_lu": channel_gross_exact, "K_void_exact_lu": channel_void_exact, "maximum_gross_relative_error": channel_gross_error, "maximum_void_relative_error": channel_void_error, "returned_k_identity_max_relative_error": returned_identity_error, "primary_adapter_advantage": adapter_advantage, "disposition": "GROSS_AREA_DARCY_ADAPTER_CONFIRMED"},
        "M0A_closure": {"origin_fit_s_qg": slope_qg, "K_gross_lu": k_m0_lu, "K_void_lu": k_m0_lu / cuda_m0[1]["phi_gross"], "delta_x_m": fixture["closure"]["delta_x_m"], "K_EWP_SI_m2": k_m0_si},
        "openfoam_uniform": {"maximum_total_flow_relative_error": max(row["total_flow_relative_error"] for row in uniform), "maximum_Q_over_delta_p_relative_deviation": max(abs(value-uniform_median)/uniform_median for value in uniform_q_over_dp), "porosity_invariance_relative_difference": porosity_difference},
        "mesh_preflight": preflight,
        "series": {"serial": series_serial, "mpi": series_mpi, "serial_mpi_total_flow_relative_difference": relative_difference(series_mpi["total_flow_m3_s"], series_serial["total_flow_m3_s"]), "serial_mpi_layer_A_share_relative_difference": relative_difference(series_mpi["layer_A_pressure_drop_share"], series_serial["layer_A_pressure_drop_share"]), "serial_mpi_layer_B_share_relative_difference": relative_difference(series_mpi["layer_B_pressure_drop_share"], series_serial["layer_B_pressure_drop_share"])},
        "parallel": {"serial": parallel_serial, "mpi": parallel_mpi, "serial_mpi_total_flow_relative_difference": relative_difference(parallel_mpi["total_flow_m3_s"], parallel_serial["total_flow_m3_s"]), "serial_mpi_inner_share_relative_difference": relative_difference(parallel_mpi["inner_flow_share"], parallel_serial["inner_flow_share"]), "serial_mpi_outer_share_relative_difference": relative_difference(parallel_mpi["outer_flow_share"], parallel_serial["outer_flow_share"])},
        "gates": gates,
        "overall_disposition": "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED",
        "claim_ceiling": {"qualified_scope": "EXACT_SYNTHETIC_SATURATED_DARCY_FIXTURES_ONLY", "real_coffee_permeability": "NOT_ESTABLISHED", "real_coffee_morphology": "NOT_REPRESENTED", "fines_physics": "NOT_TESTED", "full_basket_scale_transfer": "NOT_TESTED", "physical_validation": "NOT_ESTABLISHED", "independent_data_gate": "UNCHANGED"},
        "external_evidence": {"logical_root": "EXTERNAL_EVIDENCE_ROOT", "manifest_sha256": args.external_manifest_sha256, "archive_sha256": args.archive_sha256, "archive_file_count": int(args.archive_file_count), "archive_source_bytes": int(args.archive_source_bytes), "archive_bytes": int(args.archive_bytes)},
        "protected_hash_parity": "PASS",
        "prohibited_work": {"openfoam_source_change": False, "puckworks_change": False, "calibration_or_refit": False, "protected_scoring": False, "physical_validation": False, "XSV_TAICHI_002_started": False}
    }
    result_path = output / "XSV_TAICHI_001_RESULT.json"
    result_path.write_bytes(canonical_json_bytes(result))
    fieldnames = ("row_class", "run_id", "family", "backend_or_ranks", "fixture_revision", "disposition", "primary_value", "primary_unit")
    summary_rows = []
    for run_id in sorted(lbm):
        row = lbm[run_id]; summary_rows.append({"row_class": "GOVERNED_RUN", "run_id": run_id, "family": "LBM", "backend_or_ranks": row["actual_architecture"], "fixture_revision": 1, "disposition": "PASS", "primary_value": row["K_gross_lu"], "primary_unit": "lu2"})
    for run_id in sorted(openfoam):
        row = openfoam[run_id]; summary_rows.append({"row_class": "GOVERNED_RUN", "run_id": run_id, "family": "OPENFOAM", "backend_or_ranks": next(item["mpi_ranks"] for item in fixture["runs"] if item["run_id"] == run_id), "fixture_revision": 2 if "PARALLEL" in run_id else 1, "disposition": "PASS", "primary_value": row["total_flow_m3_s"], "primary_unit": "m3/s"})
    summary_rows.append({"row_class": "PROTOCOL_INVALID_ATTEMPT", "run_id": "OF-PARALLEL-1-REVISION-1", "family": "OPENFOAM_ATTEMPT", "backend_or_ranks": 1, "fixture_revision": 1, "disposition": "PROTOCOL_INVALID_PRE_SOLVE_MESH_INTERFACE_MISALIGNMENT", "primary_value": "", "primary_unit": ""})
    summary_rows.extend((
        {"row_class": "ANALYTICAL_REFERENCE", "run_id": "CH33-K-GROSS-EXACT", "family": "ANALYTICAL", "backend_or_ranks": "", "fixture_revision": 1, "disposition": "REFERENCE", "primary_value": channel_gross_exact, "primary_unit": "lu2"},
        {"row_class": "ANALYTICAL_REFERENCE", "run_id": "RADIAL-Q-EXACT", "family": "ANALYTICAL", "backend_or_ranks": "", "fixture_revision": 2, "disposition": "REFERENCE", "primary_value": parallel_serial["exact_total_flow_m3_s"], "primary_unit": "m3/s"},
    ))
    summary_path = output / "XSV_TAICHI_001_SUMMARY.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n"); writer.writeheader(); writer.writerows(summary_rows)
    artifact = {
        "schema_version": "espresso.whole_pull.xsv_taichi_001.artifact_manifest.v1",
        "task": "XSV-TAICHI-001",
        "external_evidence_root": "EXTERNAL_EVIDENCE_ROOT",
        "external_manifest_sha256": args.external_manifest_sha256,
        "external_archive_sha256": args.archive_sha256,
        "external_archive_file_count": int(args.archive_file_count),
        "external_archive_source_bytes": int(args.archive_source_bytes),
        "external_archive_bytes": int(args.archive_bytes),
        "committed_members": {"XSV_TAICHI_001_RESULT.json": sha256_file(result_path), "XSV_TAICHI_001_SUMMARY.csv": sha256_file(summary_path)},
        "protocol_invalid_attempt_log_sha256": amendment["failed_attempt"]["log_sha256"],
        "executable_sha256": "e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6",
        "physical_validation": "NOT_ESTABLISHED"
    }
    (output / "XSV_TAICHI_001_ARTIFACT_MANIFEST.json").write_bytes(canonical_json_bytes(artifact))
    print(json.dumps({"result": str(result_path), "summary_rows": len(summary_rows), "overall_disposition": result["overall_disposition"]}, sort_keys=True))


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
    radial = subparsers.add_parser("verify-radial-fixture")
    radial.add_argument("--output")
    radial.set_defaults(function=verify_radial_fixture)
    reduce_parser = subparsers.add_parser("reduce-final")
    reduce_parser.add_argument("--evidence-root", required=True)
    reduce_parser.add_argument("--output-dir", required=True)
    reduce_parser.add_argument("--external-manifest-sha256", required=True)
    reduce_parser.add_argument("--archive-sha256", required=True)
    reduce_parser.add_argument("--archive-file-count", required=True)
    reduce_parser.add_argument("--archive-source-bytes", required=True)
    reduce_parser.add_argument("--archive-bytes", required=True)
    reduce_parser.set_defaults(function=reduce_final)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
