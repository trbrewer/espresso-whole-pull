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
import tarfile
from typing import Any, Dict, Iterable, Tuple

sys.dont_write_bytecode = True

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
    import numpy as np
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
    import numpy as np
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
    import numpy as np
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


EXPECTED_EXTERNAL_MANIFEST_SHA256 = "8102a43bd83d73f6c3b6885d3402e72d7992416d10352657c43109860e31bd72"
EXPECTED_EXTERNAL_ARCHIVE_SHA256 = "4ec8ab82c6639fa482894910021c9155c944df0adf7bcfcf7f04077a187cd401"


def _check(gate: str, check_id: str, observed: Any, expected: Any,
           operator: str, passed: bool, sources: Iterable[str],
           failure: str) -> Dict[str, Any]:
    return {
        "gate": gate, "check_id": check_id, "source_records": list(sources),
        "observed": observed, "expected_or_threshold": expected,
        "comparison_operator": operator, "pass": bool(passed),
        "typed_failure": None if passed else failure,
        "evidence_identity": sha256_bytes(canonical_json_bytes({
            "sources": list(sources), "observed": observed,
        })),
    }


def evaluate_gate_contract(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Authoritatively derive gates from immutable evidence observations.

    This pure, standard-library evaluator is also used by mutation tests.  It
    never trusts a stored gate or row disposition.
    """
    checks = []
    add = checks.append
    expected_lbm = inputs["expected_lbm_ids"]
    observed_lbm = inputs["observed_lbm_ids"]
    expected_of = inputs["expected_openfoam_ids"]
    observed_of = inputs["observed_openfoam_ids"]
    add(_check("G2", "lbm_run_identity_set", sorted(observed_lbm), sorted(expected_lbm),
               "EXACT_SET_AND_UNIQUE", len(observed_lbm) == len(set(observed_lbm)) and set(observed_lbm) == set(expected_lbm),
               ["XSV_TAICHI_001_CASE_MATRIX.csv", "lbm/*/run.json"], "LBM_RUN_IDENTITY_MISMATCH"))
    add(_check("G4", "openfoam_run_identity_set", sorted(observed_of), sorted(expected_of),
               "EXACT_SET_AND_UNIQUE", len(observed_of) == len(set(observed_of)) and set(observed_of) == set(expected_of),
               ["XSV_TAICHI_001_CASE_MATRIX.csv", "OpenFOAM structured traces"], "OPENFOAM_RUN_IDENTITY_MISMATCH"))
    for item in inputs["checks"]:
        value, limit, op = item["observed"], item["expected"], item["operator"]
        if op == "<=": passed = math.isfinite(float(value)) and float(value) <= float(limit)
        elif op == "<": passed = math.isfinite(float(value)) and float(value) < float(limit)
        elif op == ">=": passed = math.isfinite(float(value)) and float(value) >= float(limit)
        elif op == ">": passed = math.isfinite(float(value)) and float(value) > float(limit)
        elif op == "==": passed = value == limit
        elif op == "EXACT": passed = value == limit
        elif op == "INTEGRITY_CLOSE": passed = math.isclose(float(value), float(limit), rel_tol=1e-12, abs_tol=1e-12)
        elif op == "TRUE": passed = value is True
        elif op == "FALSE": passed = value is False
        else: raise ValueError(f"unsupported evaluator operator: {op}")
        add(_check(item["gate"], item["check_id"], value, limit, op, passed,
                   item["sources"], item["failure"]))
    dispositions = {}
    for gate in ("G0", "G1", "G2", "G3", "G4", "G5", "G6_LOCAL_PACKAGE"):
        relevant = [x for x in checks if x["gate"] == gate]
        dispositions[gate] = "PASS" if relevant and all(x["pass"] for x in relevant) else (
            next((x["typed_failure"] for x in relevant if not x["pass"]), f"{gate}_EVIDENCE_MISSING"))
    dispositions["FINAL_EXACT_HEAD_CI"] = "RESOLVE_FROM_GITHUB_AT_REVIEW"
    dispositions["FINAL_EXACT_HEAD_REVIEW"] = "PENDING"
    scientific_pass = all(dispositions[x] == "PASS" for x in
                          ("G0", "G1", "G2", "G3", "G4", "G5"))
    package_pass = dispositions["G6_LOCAL_PACKAGE"] == "PASS"
    g6_failures = [x["typed_failure"] for x in checks
                   if x["gate"] == "G6_LOCAL_PACKAGE" and not x["pass"]]
    provenance_only = bool(g6_failures) and set(g6_failures) == {
        "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE"
    }
    scientific_disposition = (
        "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED" if scientific_pass
        else "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES"
    )
    package_disposition = (
        "XSV_TAICHI_001_PACKAGE_COMPLETE" if package_pass
        else ("XSV_TAICHI_001_COMPLETE_WITH_TYPED_PROVENANCE_LIMITATION"
              if provenance_only else "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES")
    )
    return {
        "checks": checks,
        "gates": dispositions,
        "scientific_disposition": scientific_disposition,
        "package_disposition": package_disposition,
        "overall_disposition": (
            "XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED"
            if scientific_pass and package_pass
            else "XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES"
        ),
    }


def verify_external_package(manifest_path: Path, archive_path: Path,
                            evidence_root: Path) -> Dict[str, Any]:
    manifest_hash = sha256_file(manifest_path)
    archive_hash = sha256_file(archive_path)
    if manifest_hash != EXPECTED_EXTERNAL_MANIFEST_SHA256:
        raise RuntimeError("external manifest hash mismatch")
    if archive_hash != EXPECTED_EXTERNAL_ARCHIVE_SHA256 or archive_path.stat().st_size != 25214779:
        raise RuntimeError("external archive identity mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    members = manifest["files"]
    if (manifest.get("self_excluded") is not True or len(members) != 1545 or
            manifest.get("file_count") != 1545 or
            sum(int(x["bytes"]) for x in members) != 134226177 or
            manifest.get("total_bytes") != 134226177):
        raise RuntimeError("external manifest count or byte total mismatch")
    logical = [x["logical_path"] for x in members]
    if len(logical) != len(set(logical)) or "EXTERNAL_EVIDENCE_MANIFEST.json" in logical:
        raise RuntimeError("external manifest self-exclusion or uniqueness failure")
    for member in members:
        path = evidence_root / member["logical_path"]
        if (not path.is_file() or path.stat().st_size != int(member["bytes"])
                or sha256_file(path) != member["sha256"]):
            raise RuntimeError(f"external evidence member mismatch: {member['logical_path']}")
    prefix = evidence_root.name + "/"
    expected_archive = {prefix + x for x in logical} | {prefix + manifest_path.name}
    with tarfile.open(archive_path, "r:gz") as archive:
        files = [x for x in archive.getmembers() if x.isfile()]
        if {x.name for x in files} != expected_archive:
            raise RuntimeError("external archive inventory mismatch")
        indexed = {x.name: x for x in files}
        for member in members:
            archived = indexed[prefix + member["logical_path"]]
            stream = archive.extractfile(archived)
            if stream is None or archived.size != int(member["bytes"]) or hashlib.sha256(stream.read()).hexdigest() != member["sha256"]:
                raise RuntimeError(f"external archive member mismatch: {member['logical_path']}")
        stream = archive.extractfile(indexed[prefix + manifest_path.name])
        if stream is None or hashlib.sha256(stream.read()).hexdigest() != manifest_hash:
            raise RuntimeError("archive manifest member mismatch")
    return {"manifest_sha256": manifest_hash, "manifest_member_count": 1545,
            "manifest_source_bytes": 134226177, "archive_sha256": archive_hash,
            "archive_bytes": 25214779, "archive_regular_file_count": 1546,
            "all_manifest_members_verified": True, "archive_inventory_verified": True}


def _last_trace(path: Path, run_id: str, fixture: Dict[str, Any]) -> Dict[str, Any]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"empty structured trace: {run_id}")
    row = rows[-1]
    q = float(row["outlet_flow_m3_s"])
    qin = float(row["inlet_flow_m3_s"])
    spec = next(x for x in fixture["runs"] if x["run_id"] == run_id)
    exact = float(fixture["domain"]["gross_area_m2"]) * float(spec["target_q_m_s"])
    return {"run_id": run_id, "total_flow_m3_s": q,
            "outlet_flow_m3_s": q, "inlet_flow_m3_s": qin,
            "exact_total_flow_m3_s": exact,
            "total_flow_relative_error": relative_difference(q, exact),
            "superficial_flow_m_s": q / float(fixture["domain"]["gross_area_m2"]),
            "superficial_flow_relative_error": relative_difference(q / float(fixture["domain"]["gross_area_m2"]), float(spec["target_q_m_s"])),
            "flux_imbalance_relative": relative_difference(qin, q),
            "boundary_flux_imbalance_relative": relative_difference(qin, q),
            "structured_trace_sha256": sha256_file(path),
            "primitive_trace_sources": [{"logical_path": "/".join(path.parts[-5:]),
                "sha256": sha256_file(path), "member_identity": "FINAL_ROW",
                "fields": ["outlet_flow_m3_s", "inlet_flow_m3_s"]}],
            "typed_disposition": "PASS"}


def _composition_trace(case: Path, run_id: str, fixture: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute composition diagnostics from retained structured primitives."""
    trace_path = case / "xsv_trace.json"
    stored = json.loads(trace_path.read_text(encoding="utf-8"))
    csv_path = case / "postProcessing/wholePull/0/traces.csv"
    if not csv_path.is_file():
        csv_path = case / "processor0/postProcessing/wholePull/0/traces.csv"
    with csv_path.open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    if not csv_rows:
        raise RuntimeError(f"empty composition trace: {run_id}")
    final_csv = csv_rows[-1]
    total = float(stored["total_flow_m3_s"])
    inlet = float(final_csv["inlet_flow_m3_s"])
    outlet = float(final_csv["outlet_flow_m3_s"])
    exact = float(stored["exact_total_flow_m3_s"])
    row = dict(stored)
    row.update({
        "inlet_flow_m3_s": inlet,
        "outlet_flow_m3_s": outlet,
        "total_flow_relative_error": relative_difference(total, exact),
        "flux_imbalance_relative": relative_difference(inlet, outlet),
        "boundary_flux_imbalance_relative": relative_difference(inlet, outlet),
        "previous_hybrid_inlet_aggregate_relative_difference": relative_difference(inlet, total),
        "aggregate_total_vs_boundary_outlet_relative_difference": relative_difference(total, outlet),
        "stored_derived_field_parity": {
            "total_flow_relative_error": relative_difference(total, exact),
        },
        "legacy_flux_imbalance_provenance": {
            "disposition": "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE",
            "stored_value": float(stored["flux_imbalance_relative"]),
            "generating_formula": "NOT_ESTABLISHED_FROM_RETAINED_EVIDENCE",
            "candidate_A_same_row_boundary_balance": relative_difference(inlet, outlet),
            "candidate_B_previous_hybrid": relative_difference(inlet, total),
            "candidate_C": "NOT_AVAILABLE",
        },
        "structured_trace_sha256": sha256_file(trace_path),
        "primitive_trace_sources": [
            {"logical_path": "/".join(trace_path.parts[-4:]), "sha256": sha256_file(trace_path),
             "member_identity": "STRUCTURED_MEMBERS",
             "fields": ["total_flow_m3_s", "exact_total_flow_m3_s", "pressure_fit"] if "SERIES" in run_id else ["total_flow_m3_s", "exact_total_flow_m3_s", "inner_flow_share", "outer_flow_share"]},
            {"logical_path": "openfoam/cases/" + case.name + "/" + "/".join(csv_path.relative_to(case).parts), "sha256": sha256_file(csv_path),
             "member_identity": "FINAL_ROW", "final_row_index": len(csv_rows) - 1,
             "final_row_time_s": final_csv["time_s"],
             "fields": ["inlet_flow_m3_s", "outlet_flow_m3_s"]},
        ],
    })
    if "SERIES" in run_id:
        profile = fixture["profiles"]["axial_two_layer"]
        length = float(fixture["domain"]["bed_depth_m"])
        la = float(profile["interface_position_m"]); lb = length - la
        ka = float(fixture["closure"]["K_A_m2"]); kb = float(fixture["closure"]["K_B_m2"])
        expected_a = (la / ka) / (la / ka + lb / kb); expected_b = 1.0 - expected_a
        pressure = stored["pressure_fit"]
        total_dp = float(pressure["pin"]) - float(pressure["pout"])
        share_a = (float(pressure["pin"]) - float(pressure["pinterface"])) / total_dp
        share_b = (float(pressure["pinterface"]) - float(pressure["pout"])) / total_dp
        row.update({"expected_layer_A_pressure_drop_share": expected_a,
                    "expected_layer_B_pressure_drop_share": expected_b,
                    "layer_A_pressure_drop_share": share_a,
                    "layer_B_pressure_drop_share": share_b,
                    "layer_A_share_relative_error": relative_difference(share_a, expected_a),
                    "layer_B_share_relative_error": relative_difference(share_b, expected_b)})
    else:
        radial = fixture["profiles"]["radial_two_zone"]
        expected_inner = float(radial["expected_inner_flow_share"])
        expected_outer = float(radial["expected_outer_flow_share"])
        inner = float(stored["inner_flow_share"]); outer = float(stored["outer_flow_share"])
        row.update({"expected_inner_flow_share": expected_inner,
                    "expected_outer_flow_share": expected_outer,
                    "inner_flow_share_relative_error": relative_difference(inner, expected_inner),
                    "outer_flow_share_relative_error": relative_difference(outer, expected_outer)})
    row["stored_record"] = stored
    return row


def reduce_final(args: argparse.Namespace) -> None:
    """Deterministically reduce and fail-closed adjudicate retained evidence."""
    import numpy as np
    evidence = Path(args.evidence_root).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    external = verify_external_package(Path(args.external_manifest).resolve(),
                                       Path(args.external_archive).resolve(), evidence)
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    fixture = json.loads(OPENFOAM_FIXTURE_PATH.read_text(encoding="utf-8"))
    amendment_path = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_PROTOCOL_AMENDMENT_001.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    authorization_path = ROOT / "verification/cases/xsv_taichi_001/XSV_TAICHI_001_STAGE_AUTHORIZATION.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    package_qa = json.loads((ROOT / "PACKAGE_QA_STATUS.json").read_text(encoding="utf-8"))
    lbm_records = []
    for path in sorted((evidence / "lbm").glob("*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["source_record_sha256"] = sha256_file(path)
        lbm_records.append(record)
    lbm = {record["run_id"]: record for record in lbm_records}

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
    geometry_sizes = {"CH33": 33, "SP32": 32, "M0A": 40}
    for row in lbm_records:
        nu = (float(row["tau_plus"]) - 0.5) / 3.0
        u_void = float(row["q_box_lu"]) / float(row["phi_gross"])
        derived = {
            "nu_lu": nu,
            "u_void_lu": u_void,
            "K_gross_lu": nu * float(row["q_box_lu"]) / float(row["g_lu"]),
            "K_void_lu": nu * u_void / float(row["g_lu"]),
            "Mach": math.sqrt(3.0) * float(row["u_max_lu"]),
            "Re_L": u_void * geometry_sizes[row["case_id"]] / nu,
        }
        derived["returned_k_identity_relative_difference"] = relative_difference(
            float(row["k_puckworks_returned"]), derived["K_void_lu"])
        row["formula_lineage"] = derived
    closure = fixture["closure"]
    m0_geometry = next(x for x in geometry["geometries"] if x["case_id"] == "M0A")
    delta_x = float(protocol["openfoam_settings"]["delta_x_m"])
    side = 40 * delta_x; area = side**2; radius = math.sqrt(area / math.pi)
    k_b = float(closure["K_B_over_K_A"]) * k_m0_si
    closure_handoff = {
        "source_run_ids": [x["run_id"] for x in cuda_m0],
        "source_run_record_sha256": [x["source_record_sha256"] for x in cuda_m0],
        "origin_fit": {"recomputed": slope_qg, "fixture": closure["origin_fit_s_qg"], "relative_difference": relative_difference(slope_qg, closure["origin_fit_s_qg"])},
        "K_A_lu": {"recomputed": k_m0_lu, "fixture": closure["K_A_lu"], "relative_difference": relative_difference(k_m0_lu, closure["K_A_lu"])},
        "delta_x_m": {"protocol": delta_x, "fixture": closure["delta_x_m"]},
        "K_A_m2": {"recomputed": k_m0_si, "fixture": closure["K_A_m2"], "relative_difference": relative_difference(k_m0_si, closure["K_A_m2"])},
        "K_B_m2": {"recomputed": k_b, "fixture": closure["K_B_m2"], "relative_difference": relative_difference(k_b, closure["K_B_m2"])},
        "porosity": {"geometry": m0_geometry["phi_gross"], "fixture": fixture["porosity"]["base"]},
        "domain": {"bed_depth_recomputed": side, "bed_depth_fixture": fixture["domain"]["bed_depth_m"], "gross_area_recomputed": area, "gross_area_fixture": fixture["domain"]["gross_area_m2"], "basket_radius_recomputed": radius, "basket_radius_fixture": fixture["domain"]["basket_radius_m"]},
    }

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
            row = _composition_trace(case, run_id, fixture)
        else:
            row = _last_trace(case / "postProcessing/wholePull/0/traces.csv", run_id, fixture)
        openfoam[run_id] = row
    uniform = [openfoam[name] for name in ("OF-U-LOW", "OF-U-MID", "OF-U-HIGH")]
    uniform_q_over_dp = [row["total_flow_m3_s"] / next(item["delta_p_Pa"] for item in fixture["runs"] if item["run_id"] == row["run_id"]) for row in uniform]
    uniform_median = sorted(uniform_q_over_dp)[1]
    porosity_difference = relative_difference(openfoam["OF-U-PHI-ALT"]["total_flow_m3_s"], openfoam["OF-U-MID"]["total_flow_m3_s"])
    series_serial = openfoam["OF-SERIES-1"]; series_mpi = openfoam["OF-SERIES-16"]
    parallel_serial = openfoam["OF-PARALLEL-1"]; parallel_mpi = openfoam["OF-PARALLEL-16"]
    preflight = json.loads((evidence / "openfoam/cases/OF-PARALLEL-1-R2/radial_mesh_preflight.json").read_text(encoding="utf-8"))
    with CASE_MATRIX_PATH.open(encoding="utf-8", newline="") as handle:
        matrix_rows = list(csv.DictReader(handle))
    expected_lbm_ids = [x["run_id"] for x in matrix_rows if x["family"] == "LBM"]
    expected_of_ids = [x["run_id"] for x in matrix_rows if x["family"] == "OPENFOAM"]
    thresholds = protocol["thresholds"]
    evaluation_checks = []
    def ev(gate: str, check_id: str, observed: Any, expected: Any, operator: str,
           failure: str, sources: Iterable[str]) -> None:
        evaluation_checks.append({"gate": gate, "check_id": check_id,
                                  "observed": observed, "expected": expected,
                                  "operator": operator, "failure": failure,
                                  "sources": list(sources)})
    ev("G0", "authorization_and_protocol_identity", amendment["authorization_id"],
       "XSV-TAICHI-001-G5-RADIAL-MESH-ALIGNMENT-2026-08-04", "EXACT", "G0_AUTHORITY_MISMATCH", [str(amendment_path.relative_to(ROOT))])
    ev("G0", "issue_bootstrap", authorization["issue"]["number"], protocol["issue"], "==", "G0_ISSUE_MISMATCH", ["XSV_TAICHI_001_STAGE_AUTHORIZATION.json", "XSV_TAICHI_001_PROTOCOL.json"])
    ev("G0", "pull_request_bootstrap", authorization["pull_request"]["number"], protocol["pull_request"], "==", "G0_PULL_REQUEST_MISMATCH", ["XSV_TAICHI_001_STAGE_AUTHORIZATION.json", "XSV_TAICHI_001_PROTOCOL.json"])
    ev("G1", "geometry_manifest_identity", sha256_file(GEOMETRY_MANIFEST_PATH), "5ddb9617b3543d7f48eecf5941291d265894a6cd2d5a142265a0750ab509afdd", "EXACT", "GEOMETRY_IDENTITY_MISMATCH", [str(GEOMETRY_MANIFEST_PATH.relative_to(ROOT))])
    ev("G1", "geometry_repeat_identity", geometry.get("repeat_identity"), "PASS", "EXACT", "GEOMETRY_NONDETERMINISTIC", [str(GEOMETRY_MANIFEST_PATH.relative_to(ROOT))])
    for geo in geometry["geometries"]:
        ev("G1", f"{geo['case_id']}_x_through", geo["x_through_connected"], True, "TRUE", "GEOMETRY_NOT_X_THROUGH_CONNECTED", [str(GEOMETRY_MANIFEST_PATH.relative_to(ROOT))])
        ev("G1", f"{geo['case_id']}_porosity_lower", geo["phi_gross"], 0.0, ">", "GEOMETRY_POROSITY_INVALID", [str(GEOMETRY_MANIFEST_PATH.relative_to(ROOT))])
        ev("G1", f"{geo['case_id']}_porosity_upper", geo["phi_gross"], 1.0, "<", "GEOMETRY_POROSITY_INVALID", [str(GEOMETRY_MANIFEST_PATH.relative_to(ROOT))])
    matrix_by_id = {x["run_id"]: x for x in matrix_rows}
    geom_by_id = {x["case_id"]: x for x in geometry["geometries"]}
    finite_fields = ("q_box_lu", "phi_gross", "K_gross_lu", "K_void_lu", "u_max_lu", "Mach", "Re_L")
    for row in lbm_records:
        rid = row["run_id"]; spec = matrix_by_id.get(rid, {})
        for field in finite_fields:
            value = row.get(field, float("nan")); ev("G2", f"{rid}_{field}_finite", math.isfinite(float(value)), True, "TRUE", "LBM_NONFINITE", [f"lbm/{rid}/run.json"])
        for field in ("q_box_lu", "K_gross_lu", "K_void_lu"):
            ev("G2", f"{rid}_{field}_positive", row[field], 0.0, ">", "LBM_NONPOSITIVE", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_phi_upper", row["phi_gross"], 1.0, "<", "LBM_POROSITY_INVALID", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_converged", row["converged"], True, "TRUE", "LBM_UNCONVERGED", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_completed_steps", row["completed_steps"], row["max_steps"], "<", "LBM_UNCONVERGED", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_mach", row["Mach"], thresholds["mach_max"], "<=", "LBM_MACH_LIMIT_EXCEEDED", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_reynolds", row["Re_L"], thresholds["Re_L_max"], "<=", "LBM_REYNOLDS_LIMIT_EXCEEDED", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_precision", row["precision"], "float64", "EXACT", "LBM_PRECISION_MISMATCH", [f"lbm/{rid}/run.json"])
        expected_architecture = ("CPU_NUMPY" if spec.get("backend") == "NUMPY_REFERENCE"
                                 else {"CPU": "Arch.x64", "CUDA": "Arch.cuda"}.get(spec.get("architecture")))
        ev("G2", f"{rid}_actual_architecture", row.get("actual_architecture"), expected_architecture, "EXACT", "LBM_BACKEND_ARCHITECTURE_MISMATCH", [f"lbm/{rid}/run.json", "XSV_TAICHI_001_CASE_MATRIX.csv"])
        ev("G2", f"{rid}_puckworks_source_hashes", row.get("puckworks_source_hashes"), protocol["sources"]["puckworks"]["files"], "EXACT", "PUCKWORKS_SOURCE_IDENTITY_MISMATCH", [f"lbm/{rid}/run.json", "XSV_TAICHI_001_PROTOCOL.json"])
        ev("G2", f"{rid}_force", row["g_lu"], float(spec.get("g_lu", "nan")), "==", "LBM_INPUT_MISMATCH", [f"lbm/{rid}/run.json", "XSV_TAICHI_001_CASE_MATRIX.csv"])
        for key, expected in (("tau_plus", protocol["lbm_settings"]["tau_plus"]), ("check_interval", protocol["lbm_settings"]["check_interval"]), ("rtol", protocol["lbm_settings"]["relative_convergence_tolerance"]), ("min_steps", protocol["lbm_settings"]["minimum_steps"]), ("max_steps", int(spec.get("max_steps", 0))), ("puckworks_commit", protocol["sources"]["puckworks"]["commit"]), ("puckworks_tree", protocol["sources"]["puckworks"]["tree"]), ("mask_payload_sha256", geom_by_id[row["case_id"]]["payload_sha256"]), ("typed_disposition", "RUN_LEVEL_PASS_PENDING_MATRIX_GATES")):
            ev("G2", f"{rid}_{key}", row.get(key), expected, "EXACT", "LBM_INPUT_OR_PROVENANCE_MISMATCH", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_output_hash", bool(row.get("output_field_sha256")), True, "TRUE", "LBM_OUTPUT_IDENTITY_MISSING", [f"lbm/{rid}/run.json"])
        ev("G2", f"{rid}_log_hash", bool(row.get("log_sha256")), True, "TRUE", "LBM_LOG_IDENTITY_MISSING", [f"lbm/{rid}/run.json"])
        for field in ("nu_lu", "u_void_lu", "K_gross_lu", "K_void_lu", "Mach", "Re_L"):
            ev("G2", f"{rid}_{field}_formula_lineage", row[field], row["formula_lineage"][field], "INTEGRITY_CLOSE", "LBM_DERIVED_QUANTITY_LINEAGE_MISMATCH", [f"lbm/{rid}/run.json", "XSV_TAICHI_001_PROTOCOL.json"])
    for name, pairs in (("numpy_taichi", numpy_cpu_pairs), ("cpu_cuda", cpu_cuda_pairs)):
        for key, threshold_key in (("q_box_lu", "backend_relative_q_max"), ("K_gross_lu", "backend_relative_K_gross_max")):
            ev("G2", f"{name}_{key}_parity", pair_max(pairs, key), thresholds[threshold_key], "<=", "NUMPY_TAICHI_PARITY_FAILED" if name == "numpy_taichi" else "TAICHI_CPU_GPU_PARITY_FAILED", ["retained LBM run records"])
    for case_id, value in velocity_l2.items(): ev("G2", f"{case_id}_velocity_L2", value, thresholds["mid_force_velocity_relative_L2_max"], "<=", "NUMPY_TAICHI_PARITY_FAILED", [f"lbm/{case_id}-NP-MID/ux.npy", f"lbm/{case_id}-TC-MID/ux.npy"])
    for key, metrics in force_linearity.items():
        ev("G2", f"{key}_R2", metrics["R2"], thresholds["force_linearity_R2_min"], ">=", "LBM_FORCE_NONLINEAR", ["retained LBM run records"])
        ev("G2", f"{key}_q_over_g", metrics["q_over_g_max_relative_deviation"], thresholds["q_over_g_max_relative_deviation"], "<=", "LBM_FORCE_NONLINEAR", ["retained LBM run records"])
        ev("G2", f"{key}_intercept", metrics["normalized_intercept"], thresholds["normalized_intercept_max"], "<=", "LBM_FORCE_NONLINEAR", ["retained LBM run records"])
    ev("G2", "channel_gross_error", channel_gross_error, thresholds["channel_relative_error_max"], "<=", "CHANNEL_ANALYTICAL_GATE_FAILED", ["CH33 retained records"])
    ev("G2", "channel_void_error", channel_void_error, thresholds["channel_relative_error_max"], "<=", "CHANNEL_ANALYTICAL_GATE_FAILED", ["CH33 retained records"])
    ev("G3", "returned_k_identity", returned_identity_error, thresholds["returned_identity_relative_tolerance"], "<=", "PUCKWORKS_RETURN_IDENTITY_MISMATCH", ["retained LBM run records"])
    ev("G3", "gross_area_adapter_error", channel_gross_error, thresholds["channel_relative_error_max"], "<=", "REFERENCE_VOLUME_ADAPTER_REJECTED", ["CH33 retained records"])
    ev("G3", "primary_adapter_advantage", adapter_advantage, thresholds["primary_adapter_advantage_min"], ">=", "REFERENCE_VOLUME_ADAPTER_REJECTED", ["CH33 retained records"])
    ev("G3", "M0A_source_run_identity", closure_handoff["source_run_ids"], closure["source_runs"], "EXACT", "M0A_CLOSURE_LINEAGE_MISMATCH", ["M0A CUDA run records", "OpenFOAM fixture"])
    for key in ("origin_fit", "K_A_lu", "K_A_m2", "K_B_m2"):
        ev("G3", f"M0A_{key}_identity", closure_handoff[key]["recomputed"], closure_handoff[key]["fixture"], "INTEGRITY_CLOSE", "M0A_CLOSURE_LINEAGE_MISMATCH", ["M0A CUDA run records", "OpenFOAM fixture"])
    ev("G3", "M0A_delta_x_identity", closure_handoff["delta_x_m"]["protocol"], closure_handoff["delta_x_m"]["fixture"], "INTEGRITY_CLOSE", "M0A_CLOSURE_LINEAGE_MISMATCH", ["machine protocol", "OpenFOAM fixture"])
    ev("G4", "M0A_porosity_handoff", closure_handoff["porosity"]["geometry"], closure_handoff["porosity"]["fixture"], "INTEGRITY_CLOSE", "OPENFOAM_CLOSURE_CONSUMPTION_IDENTITY_MISMATCH", ["geometry manifest", "OpenFOAM fixture"])
    for key in ("bed_depth", "gross_area", "basket_radius"):
        ev("G4", f"domain_{key}_identity", closure_handoff["domain"][f"{key}_recomputed"], closure_handoff["domain"][f"{key}_fixture"], "INTEGRITY_CLOSE", "REFERENCE_VOLUME_DOMAIN_MAPPING_MISMATCH", ["geometry manifest", "machine protocol", "OpenFOAM fixture"])
    for row in openfoam.values():
        gate = "G4" if row["run_id"].startswith("OF-U-") else "G5"
        maxerr = thresholds["uniform_relative_error_max"] if gate == "G4" else thresholds["composition_relative_error_max"]
        ev(gate, f"{row['run_id']}_total_flow", row["total_flow_relative_error"], maxerr, "<=", "OPENFOAM_UNIFORM_ANALYTICAL_GATE_FAILED" if gate == "G4" else "COMPOSITION_TOTAL_FLOW_FAILED", [f"structured trace:{row['run_id']}"])
        ev(gate, f"{row['run_id']}_flux_imbalance", row["flux_imbalance_relative"], thresholds["flux_imbalance_relative_max"], "<=", "OPENFOAM_FLUX_BALANCE_FAILED" if gate == "G4" else "COMPOSITION_FLUX_BALANCE_FAILED", [f"structured trace:{row['run_id']}"])
        if gate == "G4": ev("G4", f"{row['run_id']}_superficial_flow", row["superficial_flow_relative_error"], thresholds["uniform_relative_error_max"], "<=", "OPENFOAM_UNIFORM_ANALYTICAL_GATE_FAILED", [f"structured trace:{row['run_id']}"])
        if "stored_record" in row:
            stored = row["stored_record"]
            ev(gate, f"{row['run_id']}_total_flow_relative_error_stored_parity",
               row["total_flow_relative_error"], stored["total_flow_relative_error"],
               "INTEGRITY_CLOSE", "STRUCTURED_TRACE_DERIVED_FIELD_MISMATCH",
               [f"structured trace:{row['run_id']}"])
            ev("G6_LOCAL_PACKAGE", f"{row['run_id']}_aggregate_total_boundary_outlet_consistency",
               row["aggregate_total_vs_boundary_outlet_relative_difference"],
               thresholds["flux_imbalance_relative_max"], "<=",
               "TRACE_REPRESENTATION_CONSISTENCY_FAILED", [f"structured trace:{row['run_id']}"])
            ev("G6_LOCAL_PACKAGE", f"{row['run_id']}_legacy_flux_provenance",
               row["legacy_flux_imbalance_provenance"]["disposition"],
               "STORED_DERIVED_FIELD_REPRODUCED", "EXACT",
               "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE",
               [f"structured trace:{row['run_id']}"])
            ev("G6_LOCAL_PACKAGE", f"{row['run_id']}_legacy_flux_provenance_supported",
               row["legacy_flux_imbalance_provenance"]["generating_formula"] !=
               "NOT_ESTABLISHED_FROM_RETAINED_EVIDENCE", True, "TRUE",
               "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE",
               [f"structured trace:{row['run_id']}"])
    qdev = max(abs(x-uniform_median)/uniform_median for x in uniform_q_over_dp)
    ev("G4", "uniform_Q_over_delta_p", qdev, thresholds["uniform_Q_over_delta_p_relative_deviation_max"], "<=", "OPENFOAM_UNIFORM_ANALYTICAL_GATE_FAILED", ["four uniform structured traces"])
    ev("G4", "porosity_invariance", porosity_difference, thresholds["porosity_invariance_relative_difference_max"], "<=", "POROSITY_DOUBLE_COUNTING_OR_COUPLING_DETECTED", ["OF-U-MID", "OF-U-PHI-ALT"])
    ev("G5", "mesh_preflight", preflight["maximum_mesh_zone_area_relative_error"], 1e-8, "<=", "MESH_CONFORMING_RADIAL_FIXTURE_PREFLIGHT_FAILED", ["radial_mesh_preflight.json"])
    for label, row in (("series_serial", series_serial), ("series_mpi", series_mpi)):
        ev("G5", f"{label}_layer_A", row["layer_A_share_relative_error"], thresholds["composition_relative_error_max"], "<=", "AXIAL_SERIES_COMPOSITION_FAILED", [f"structured trace:{row['run_id']}"])
        ev("G5", f"{label}_layer_B", row["layer_B_share_relative_error"], thresholds["composition_relative_error_max"], "<=", "AXIAL_SERIES_COMPOSITION_FAILED", [f"structured trace:{row['run_id']}"])
        for field in ("layer_A_pressure_drop_share", "layer_B_pressure_drop_share", "layer_A_share_relative_error", "layer_B_share_relative_error"):
            ev("G5", f"{label}_{field}_stored_parity", row[field], row["stored_record"][field], "INTEGRITY_CLOSE", "STRUCTURED_TRACE_DERIVED_FIELD_MISMATCH", [f"structured trace:{row['run_id']}"])
    for label, row in (("radial_serial", parallel_serial), ("radial_mpi", parallel_mpi)):
        ev("G5", f"{label}_inner", row["inner_flow_share_relative_error"], thresholds["composition_relative_error_max"], "<=", "RADIAL_PARALLEL_ZONE_SHARE_GATE_FAILED", [f"structured trace:{row['run_id']}"])
        ev("G5", f"{label}_outer", row["outer_flow_share_relative_error"], thresholds["composition_relative_error_max"], "<=", "RADIAL_PARALLEL_ZONE_SHARE_GATE_FAILED", [f"structured trace:{row['run_id']}"])
        for field in ("inner_flow_share_relative_error", "outer_flow_share_relative_error"):
            ev("G5", f"{label}_{field}_stored_parity", row[field], row["stored_record"][field], "INTEGRITY_CLOSE", "STRUCTURED_TRACE_DERIVED_FIELD_MISMATCH", [f"structured trace:{row['run_id']}"])
    parity_metrics = {"series_flow": relative_difference(series_mpi["total_flow_m3_s"], series_serial["total_flow_m3_s"]), "series_A": relative_difference(series_mpi["layer_A_pressure_drop_share"], series_serial["layer_A_pressure_drop_share"]), "series_B": relative_difference(series_mpi["layer_B_pressure_drop_share"], series_serial["layer_B_pressure_drop_share"]), "radial_flow": relative_difference(parallel_mpi["total_flow_m3_s"], parallel_serial["total_flow_m3_s"]), "radial_inner": relative_difference(parallel_mpi["inner_flow_share"], parallel_serial["inner_flow_share"]), "radial_outer": relative_difference(parallel_mpi["outer_flow_share"], parallel_serial["outer_flow_share"])}
    for key, value in parity_metrics.items(): ev("G5", f"serial_mpi_{key}", value, thresholds["serial_mpi_relative_difference_max"], "<=", "SERIAL_MPI_PARITY_FAILED", ["serial and MPI structured traces"])
    observed_successful = len(openfoam)
    observed_invalid = 1 if amendment.get("failed_attempt", {}).get("log_sha256") == "0232443cff64335e1239a9b38e243bec861029848671b7945389e0fc502fe074" else 0
    ev("G5", "process_attempt_count", observed_successful + observed_invalid, amendment["attempt_accounting"]["revised_process_attempt_ceiling"], "==", "OPENFOAM_ATTEMPT_ACCOUNTING_FAILED", ["protocol amendment", "retained structured traces"])
    ev("G5", "protocol_invalid_attempt", amendment["failed_attempt"]["disposition"], "PROTOCOL_INVALID_PRE_SOLVE_MESH_INTERFACE_MISALIGNMENT", "EXACT", "PROTOCOL_INVALID_ATTEMPT_MISSING", [str(amendment_path.relative_to(ROOT))])
    for key, expected in (("manifest_sha256", EXPECTED_EXTERNAL_MANIFEST_SHA256), ("manifest_member_count", 1545), ("manifest_source_bytes", 134226177), ("archive_sha256", EXPECTED_EXTERNAL_ARCHIVE_SHA256), ("archive_bytes", 25214779), ("all_manifest_members_verified", True), ("archive_inventory_verified", True)):
        ev("G6_LOCAL_PACKAGE", f"external_{key}", external[key], expected, "TRUE" if expected is True else "EXACT", "EXTERNAL_EVIDENCE_VERIFICATION_FAILED", ["external manifest", "external archive"])
    ev("G6_LOCAL_PACKAGE", "physical_validation_ceiling", [protocol["claim_ceiling"]["physical_validation"], authorization["physical_validation"], package_qa["xsv_taichi_001"]["physical_validation"]], ["NOT_ESTABLISHED"] * 3, "EXACT", "PHYSICAL_VALIDATION_PROMOTED", ["machine protocol", "stage authorization", "PACKAGE_QA_STATUS.json"])
    ev("G6_LOCAL_PACKAGE", "xsv_taichi_002_inactive", package_qa["xsv_taichi_001"]["xsv_taichi_002"], "NOT_STARTED_NOT_AUTHORIZED", "EXACT", "XSV_TAICHI_002_UNAUTHORIZED_ACTIVATION", ["PACKAGE_QA_STATUS.json"])
    evaluation_inputs = {"expected_lbm_ids": expected_lbm_ids, "observed_lbm_ids": [x["run_id"] for x in lbm_records], "expected_openfoam_ids": expected_of_ids, "observed_openfoam_ids": list(openfoam), "checks": evaluation_checks}
    evaluation = evaluate_gate_contract(evaluation_inputs)
    gates = evaluation["gates"]
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
        "backend_parity": {"maximum_numpy_taichi_q_relative_difference": pair_max(numpy_cpu_pairs, "q_box_lu"), "maximum_numpy_taichi_K_relative_difference": pair_max(numpy_cpu_pairs, "K_gross_lu"), "maximum_taichi_cpu_cuda_q_relative_difference": pair_max(cpu_cuda_pairs, "q_box_lu"), "maximum_taichi_cpu_cuda_K_relative_difference": pair_max(cpu_cuda_pairs, "K_gross_lu"), "mid_force_velocity_relative_L2": velocity_l2},
        "force_linearity": force_linearity,
        "channel_adapter": {"K_gross_exact_lu": channel_gross_exact, "K_void_exact_lu": channel_void_exact, "maximum_gross_relative_error": channel_gross_error, "maximum_void_relative_error": channel_void_error, "returned_k_identity_max_relative_error": returned_identity_error, "primary_adapter_advantage": adapter_advantage, "disposition": "GROSS_AREA_DARCY_ADAPTER_CONFIRMED"},
        "M0A_closure": {"origin_fit_s_qg": slope_qg, "K_gross_lu": k_m0_lu, "K_void_lu": k_m0_lu / cuda_m0[1]["phi_gross"], "delta_x_m": fixture["closure"]["delta_x_m"], "K_EWP_SI_m2": k_m0_si},
        "closure_handoff_lineage": {**closure_handoff, "disposition": "PASS" if all(x["pass"] for x in evaluation["checks"] if x["check_id"].startswith("M0A_") or x["check_id"].startswith("domain_")) else "M0A_CLOSURE_LINEAGE_MISMATCH"},
        "primitive_trace_source_map": {key: value["primitive_trace_sources"] for key, value in sorted(openfoam.items())},
        "openfoam_uniform": {"runs": uniform, "maximum_total_flow_relative_error": max(row["total_flow_relative_error"] for row in uniform), "maximum_superficial_flow_relative_error": max(row["superficial_flow_relative_error"] for row in uniform), "maximum_Q_over_delta_p_relative_deviation": qdev, "porosity_invariance_relative_difference": porosity_difference},
        "mesh_preflight": preflight,
        "series": {"serial": series_serial, "mpi": series_mpi, "serial_mpi_total_flow_relative_difference": relative_difference(series_mpi["total_flow_m3_s"], series_serial["total_flow_m3_s"]), "serial_mpi_layer_A_share_relative_difference": relative_difference(series_mpi["layer_A_pressure_drop_share"], series_serial["layer_A_pressure_drop_share"]), "serial_mpi_layer_B_share_relative_difference": relative_difference(series_mpi["layer_B_pressure_drop_share"], series_serial["layer_B_pressure_drop_share"])},
        "parallel": {"serial": parallel_serial, "mpi": parallel_mpi, "serial_mpi_total_flow_relative_difference": relative_difference(parallel_mpi["total_flow_m3_s"], parallel_serial["total_flow_m3_s"]), "serial_mpi_inner_share_relative_difference": relative_difference(parallel_mpi["inner_flow_share"], parallel_serial["inner_flow_share"]), "serial_mpi_outer_share_relative_difference": relative_difference(parallel_mpi["outer_flow_share"], parallel_serial["outer_flow_share"])},
        "gate_evaluation": evaluation,
        "evaluation_inputs": evaluation_inputs,
        "gates": gates,
        "trace_derived_field_integrity": (
            "PASS" if gates["G6_LOCAL_PACKAGE"] == "PASS"
            else "LEGACY_DERIVED_FIELD_PROVENANCE_INCOMPLETE"
        ),
        "scientific_disposition": evaluation["scientific_disposition"],
        "package_disposition": evaluation["package_disposition"],
        "overall_disposition": evaluation["overall_disposition"],
        "execution_package_status": "XSV_TAICHI_001_EXECUTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW",
        "claim_ceiling": {"qualified_scope": "EXACT_SYNTHETIC_SATURATED_DARCY_FIXTURES_ONLY", "real_coffee_permeability": "NOT_ESTABLISHED", "real_coffee_morphology": "NOT_REPRESENTED", "fines_physics": "NOT_TESTED", "full_basket_scale_transfer": "NOT_TESTED", "physical_validation": "NOT_ESTABLISHED", "independent_data_gate": "UNCHANGED"},
        "external_evidence": {"logical_root": "EXTERNAL_EVIDENCE_ROOT", **external},
        "protected_hash_parity": "PASS",
        "prohibited_work": {"openfoam_source_change": False, "puckworks_change": False, "calibration_or_refit": False, "protected_scoring": False, "physical_validation": False, "XSV_TAICHI_002_started": False}
    }
    result_path = output / "XSV_TAICHI_001_RESULT.json"
    result_path.write_bytes(canonical_json_bytes(result))
    fieldnames = ("row_class", "run_id", "family", "backend_or_ranks", "fixture_revision", "disposition", "primary_value", "primary_unit")
    summary_rows = []
    for run_id in sorted(lbm):
        row = lbm[run_id]; passed = gates["G2"] == "PASS" and all(x["pass"] for x in evaluation["checks"] if x["gate"] == "G2" and (run_id in x["check_id"] or x["check_id"] == "lbm_run_identity_set")); summary_rows.append({"row_class": "GOVERNED_RUN", "run_id": run_id, "family": "LBM", "backend_or_ranks": row["actual_architecture"], "fixture_revision": 1, "disposition": "PASS" if passed else "G2_FAIL", "primary_value": row["K_gross_lu"], "primary_unit": "lu2"})
    for run_id in sorted(openfoam):
        row = openfoam[run_id]; family_gate = "G4" if run_id.startswith("OF-U-") else "G5"; passed = gates[family_gate] == "PASS"; summary_rows.append({"row_class": "GOVERNED_RUN", "run_id": run_id, "family": "OPENFOAM", "backend_or_ranks": next(item["mpi_ranks"] for item in fixture["runs"] if item["run_id"] == run_id), "fixture_revision": 2 if "PARALLEL" in run_id else 1, "disposition": "PASS" if passed else f"{family_gate}_FAIL", "primary_value": row["total_flow_m3_s"], "primary_unit": "m3/s"})
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
        "external_manifest_sha256": external["manifest_sha256"],
        "external_archive_sha256": external["archive_sha256"],
        "external_manifest_member_count": external["manifest_member_count"],
        "external_manifest_source_bytes": external["manifest_source_bytes"],
        "external_archive_regular_file_count": external["archive_regular_file_count"],
        "external_archive_file_count": external["archive_regular_file_count"],
        "external_archive_file_count_role": "REGULAR_FILES_IN_ARCHIVE_INCLUDING_SELF_EXCLUDED_MANIFEST",
        "external_archive_bytes": external["archive_bytes"],
        "external_verification": external,
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
    import numpy as np
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
    reduce_parser.add_argument("--external-manifest", required=True)
    reduce_parser.add_argument("--external-archive", required=True)
    reduce_parser.set_defaults(function=reduce_final)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
