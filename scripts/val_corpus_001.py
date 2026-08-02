#!/usr/bin/env python3
"""Frozen VAL-CORPUS-001 case generator, executor, and reducer."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

TASK = "VAL-CORPUS-001"
SNAPSHOT_COMMIT = "9c52c94edb27b461b6e7a4d471d29f3cef9d053e"
SNAPSHOT_TREE = "44d6539096648777f78c4db83f0985d5bd16e352"


def load(path: Path):
    return json.loads(path.read_text())


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(line for line in stream if not line.startswith("#")))


def source_terminal(snapshot: Path, nominal_bar: float):
    rows = read_csv(snapshot / "puckworks/data/waszkiewicz2025/traces_time_dependent.csv")
    group = [r for r in rows if abs(float(r["reference_pressure_round__bar"]) - nominal_bar) < 1e-9]
    if not group:
        raise RuntimeError(f"missing Waszkiewicz {nominal_bar:g}-bar group")
    return max(group, key=lambda r: float(r["time__s"]))


def governance(mode: str):
    return {
        "task": TASK,
        "change_scope": "NO_GOVERNING_PHYSICS_CHANGE",
        "evidence_role": mode,
    }


def saturated(cfg, pressure_pa, permeability):
    cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = pressure_pa
    cfg["hydraulics"]["pressure_ramp_time_s"] = 0.0
    cfg["hydraulics"]["saturated_permeability_m2"] = permeability
    cfg["wetting"].update({"initial_saturation": 1.0, "initial_wet_front_m": cfg["coffee_bed"]["bed_depth_m"]})
    cfg["time"].update({"end_s": 0.02, "delta_t_s": 0.02, "field_write_interval_s": 0.02})
    cfg["geometry"].update({"axial_cells": 64, "radial_cells": 16})


def prepare(root: Path, snapshot: Path, run_root: Path) -> None:
    protocol = load(root / "validation/cases/val_corpus_001/VAL_CORPUS_001_PROTOCOL.json")
    if subprocess.check_output(["git", "-C", str(snapshot), "rev-parse", "HEAD"], text=True).strip() != SNAPSHOT_COMMIT:
        raise RuntimeError("evidence snapshot commit mismatch")
    if subprocess.check_output(["git", "-C", str(snapshot), "rev-parse", "HEAD^{tree}"], text=True).strip() != SNAPSHOT_TREE:
        raise RuntimeError("evidence snapshot tree mismatch")
    configs = run_root / "configs"
    configs.mkdir(parents=True, exist_ok=False)
    base = load(root / "config/reconstruction_WP02A_waszkiewicz_9bar.json")
    ref = load(root / "config/reference_R0.json")
    wp03 = load(root / "validation/wp03/WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.json")
    machine = load(root / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json")["case_matrix"]["MC-2"]["machineBoundary"]
    anchor = source_terminal(snapshot, 9.0)
    p_anchor = float(anchor["basket_pressure__bar"]) * 1e5
    q_anchor = float(anchor["mass_flow_rate__g_per_s"]) / 997.0 / 1e3
    area = math.pi * float(base["geometry"]["basket_radius_m"]) ** 2
    depth = float(base["coffee_bed"]["bed_depth_m"])
    mu = float(base["liquid"]["dynamic_viscosity_Pa_s"])
    anchor_k = min(1e-12, max(1e-16, q_anchor * mu * depth / (area * p_anchor)))
    comp_ref = wp03["reference"]
    configs_written = []
    for item in protocol["run_matrix"]:
        cid = item["id"]
        family = item["family"]
        cfg = copy.deepcopy(base if family == "waszkiewicz2025" else ref)
        cfg["scenario_id"] = "VAL_CORPUS_001_" + cid.replace("-", "_")
        cfg["governance"] = governance(item["mode"])
        cfg["claim_ceiling"] = "Physical validation NOT_ESTABLISHED; existing-public-evidence reconstruction/component comparison."
        if family == "waszkiewicz2025":
            pressure = float(item["pressure_bar"]) * 1e5
            cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = pressure
            cfg["hydraulics"]["saturated_permeability_m2"] = anchor_k
            cfg["time"].update({"end_s": 30.0, "delta_t_s": 0.02, "field_write_interval_s": 1.0})
            cfg["geometry"].update({"axial_cells": 128, "radial_cells": 64})
            if item["branch"] == "darcy_forchheimer_static":
                cfg["flowResistanceModel"] = "darcyForchheimer"
                cfg["inertialPermeabilityModel"] = "wadsworth2026CeramicsFit"
                cfg["nonlinearControls"] = {"relativeTolerance":1e-9,"absoluteTolerance":1e-13,"maximumIterations":80,"underRelaxation":0.8,"machineFluxRelativeTolerance":1e-8}
            elif item["branch"] == "finite_porosity_compaction":
                cfg.pop("effective_permeability_evolution", None)
                cfg["bedMechanicsModel"] = "waszkiewiczQuasiStaticCompaction"
                cfg["poroelasticCompaction"] = {
                    "model":"waszkiewicz2025FinitePhi",
                    "stressFreePorosity":comp_ref["stress_free_porosity"],
                    "criticalCompactionPressurePa":comp_ref["critical_compaction_pressure_pa"],
                    "stressFreePermeabilityM2":anchor_k,
                    "nonlinearRelativeTolerance":1e-9,"nonlinearAbsoluteTolerance":1e-13,
                    "nonlinearMaximumIterations":100,"nonlinearUnderRelaxation":0.7,
                    "machineFluxRelativeTolerance":1e-8}
        elif family == "foster2025_2":
            cfg["geometry"].update({"basket_radius_m":0.0295,"basket_diameter_m":0.059,"axial_cells":128,"radial_cells":64})
            cfg["coffee_bed"].update({"dry_dose_kg":0.010,"bed_depth_m":0.009975,"porosity":0.322})
            cfg["hydraulics"].update({"saturated_permeability_m2":2.97e-15,"target_inlet_pressure_gauge_Pa":9e5})
            cfg["liquid"].update({"density_kg_m3":965.0,"dynamic_viscosity_Pa_s":0.315e-3})
            cfg["time"].update({"end_s":8.0,"delta_t_s":0.01,"field_write_interval_s":0.5})
        elif family in {"wadsworth2026", "romancorrochano2017", "mo2023"}:
            if family == "wadsworth2026":
                k, grad = 2.39e-11, 100 * 1e5
            elif family == "romancorrochano2017":
                k, grad = 4.9e-14, 100 * 1e5
            else:
                grad = (50 if cid.endswith("LOW") else 400) * 1e5
                k = (5.18 if cid.endswith("LOW") else 2.5) * 1e-13
            saturated(cfg, grad * float(cfg["coffee_bed"]["bed_depth_m"]), k)
            if family == "mo2023":
                cfg["flowResistanceModel"] = "darcyForchheimer"
                cfg["inertialPermeabilityModel"] = "constant"
                cfg["constantInertialPermeabilityM"] = 2.17e-13
                cfg["nonlinearControls"] = {"relativeTolerance":1e-9,"absoluteTolerance":1e-13,"maximumIterations":80,"underRelaxation":0.8,"machineFluxRelativeTolerance":1e-8}
        elif family == "de1_fixtureA":
            cfg["coffee_bed"]["dry_dose_kg"] = 0.018
            cfg["coffee_bed"]["bed_depth_m"] = 0.0075 if cid.endswith("LOW") else 0.0105
            cfg["pressureBoundaryModel"] = "lumpedMachineCompliance"
            cfg["machineBoundary"] = copy.deepcopy(machine)
            cfg["time"].update({"end_s":25.0,"delta_t_s":0.02,"field_write_interval_s":1.0})
            cfg["geometry"].update({"axial_cells":128,"radial_cells":64})
        path = configs / f"{cid}.json"
        dump(path, cfg)
        configs_written.append({"id": cid, "path": str(path.relative_to(run_root)), "sha256": sha256(path)})
    dump(run_root / "PREPARATION_RECORD.json", {
        "task": TASK, "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha256(root / "validation/cases/val_corpus_001/VAL_CORPUS_001_PROTOCOL.json"),
        "evidence_snapshot": {"commit": SNAPSHOT_COMMIT, "tree": SNAPSHOT_TREE},
        "anchor": {"source_row": anchor, "fitted_uniform_permeability_m2": anchor_k},
        "configs": configs_written})


def run(root: Path, run_root: Path, executable: Path, ranks: int) -> None:
    attempts = []
    for config in sorted((run_root / "configs").glob("*.json")):
        cid = config.stem
        case = run_root / "cases" / cid
        started = datetime.now(timezone.utc).isoformat()
        t0 = time.monotonic()
        status, reason = "FAILED", ""
        try:
            subprocess.run(["python3", str(root/"scripts/prepare_case.py"), "--root", str(root), "--config", str(config), "--case-dir", str(case), "--nprocs", str(ranks)], check=True)
            with (case/"log.blockMesh").open("w") as log:
                subprocess.run(["blockMesh"], cwd=case, stdout=log, stderr=subprocess.STDOUT, check=True)
            with (case/"log.checkMesh").open("w") as log:
                subprocess.run(["checkMesh"], cwd=case, stdout=log, stderr=subprocess.STDOUT, check=True)
            env = dict(os.environ, ESPRESSO_CASE_ROOT=str(case))
            with (case/"log.solver").open("w") as log:
                if ranks > 1:
                    with (case/"log.decomposePar").open("w") as dec:
                        subprocess.run(["decomposePar", "-force"], cwd=case, stdout=dec, stderr=subprocess.STDOUT, check=True)
                    command = ["mpirun", "-np", str(ranks), str(executable), "-parallel"]
                else:
                    command = [str(executable)]
                subprocess.run(command, cwd=case, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            solver_text = (case / "log.solver").read_text(errors="replace")
            if "FOAM FATAL ERROR" in solver_text or "End\n" not in solver_text:
                status = "FAILED"
                reason = "solver log contains FOAM FATAL ERROR or lacks terminal End marker"
            else:
                status = "COMPLETED"
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
        attempts.append({"id":cid,"status":status,"failure_reason":reason,"started_utc":started,
                         "duration_s":round(time.monotonic()-t0,6),"config_sha256":sha256(config),
                         "trace_present":(case/"postProcessing/wholePull/0/traces.csv").is_file()})
        dump(run_root / "EXECUTION_RECORD.json", {"task":TASK,"executable_sha256":sha256(executable),"ranks":ranks,"attempts":attempts})


def nearest(rows, key, value):
    return min(rows, key=lambda row: abs(float(row[key])-value))


def rmse(pairs):
    return math.sqrt(sum((a-b)**2 for a,b in pairs)/len(pairs)) if pairs else None


def analyze(root: Path, snapshot: Path, run_root: Path, output: Path) -> None:
    protocol = load(root / "validation/cases/val_corpus_001/VAL_CORPUS_001_PROTOCOL.json")
    evidence_w = read_csv(snapshot / "puckworks/data/waszkiewicz2025/traces_time_dependent.csv")
    foster = read_csv(snapshot / "puckworks/data/foster2025_2/fig6_front_position.csv")
    de1 = load(snapshot / "puckworks/data/de1_fixtureA.json")
    execution = load(run_root / "EXECUTION_RECORD.json")
    rows_out, overlays = [], {}
    by_id = {x["id"]: x for x in execution["attempts"]}
    for spec in protocol["run_matrix"]:
        cid, family = spec["id"], spec["family"]
        attempt = by_id.get(cid, {})
        trace_path = run_root / "cases" / cid / "postProcessing/wholePull/0/traces.csv"
        row = {"source":family,"condition":cid,"branch":spec["branch"],"evidence_class":protocol["evidence_class"],
               "comparison_mode":spec["mode"],"calibration_inputs":["9_bar_terminal_flow"] if cid=="WASZ-9-DARCY" else [],
               "comparison_outputs":[],"assumptions":spec.get("assumption","BASE"),"direction_result":"UNASSESSED",
               "scale_result":"UNASSESSED","shape_result":"UNASSESSED","timing_result":"UNASSESSED",
               "residual_signature":"UNASSESSED","claim_label":"NOT_COMPARABLE","failure_reason":attempt.get("failure_reason","")}
        if attempt.get("status") != "COMPLETED" or not trace_path.is_file():
            row["claim_label"] = "INVALIDATED_EXECUTION"
            rows_out.append(row); continue
        trace = read_csv(trace_path)
        if family == "waszkiewicz2025":
            nominal = float(spec["pressure_bar"])
            obs = [r for r in evidence_w if abs(float(r["reference_pressure_round__bar"])-nominal)<1e-9]
            pairs_flow=[]; pairs_mass=[]; overlay=[]
            rho=997.0
            for measured in obs:
                model=nearest(trace,"time_s",float(measured["time__s"]))
                model_flow=float(model["outlet_flow_m3_s"])*rho*1e3
                model_mass=float(model["cup_beverage_mass_kg"])*1e3
                pairs_flow.append((model_flow,float(measured["mass_flow_rate__g_per_s"])))
                pairs_mass.append((model_mass,float(measured["mass__g"])))
                overlay.append([float(measured["time__s"]),float(measured["basket_pressure__bar"]),float(model["inlet_pressure_Pa"])/1e5,float(measured["mass_flow_rate__g_per_s"]),model_flow,float(measured["mass__g"]),model_mass])
            flow_rmse, mass_rmse=rmse(pairs_flow),rmse(pairs_mass)
            row.update({"comparison_outputs":["pressure","flow","delivered_mass"],"direction_result":"PASS" if pairs_flow[-1][0]>0 else "FAIL",
                        "scale_result":"PASS" if flow_rmse <= max(0.5,abs(pairs_flow[-1][1])) else "FAIL",
                        "shape_result":"PASS" if flow_rmse <= 2*max(0.5,abs(pairs_flow[-1][1])) else "FAIL",
                        "timing_result":"PARTIAL_WETTING_ORIGIN_DIFFERS","residual_signature":f"flow_rmse_g_s={flow_rmse:.6g};mass_rmse_g={mass_rmse:.6g}",
                        "claim_label":"WORKING" if flow_rmse <= max(0.5,abs(pairs_flow[-1][1])) else "PARTIAL"})
            overlays[cid]=overlay
        elif family == "foster2025_2":
            pairs=[]; overlay=[]
            for measured in foster:
                model=nearest(trace,"time_s",float(measured["t_s"]))
                pairs.append((float(model["wet_front_m"])*1e3,float(measured["s_mm"])))
                overlay.append([float(measured["t_s"]),float(measured["s_mm"]),float(model["wet_front_m"])*1e3])
            value=rmse(pairs); first=float(trace[-1]["first_drip_s"])
            row.update({"comparison_outputs":["wetting_front","first_drip"],"direction_result":"PASS","scale_result":"PASS" if value<3 else "FAIL",
                        "shape_result":"PASS" if value<3 else "FAIL","timing_result":f"first_drip_s={first:.6g}","residual_signature":f"front_rmse_mm={value:.6g}",
                        "claim_label":"WORKING" if value<3 else "PARTIAL"})
            overlays[cid]=overlay
        elif family == "de1_fixtureA":
            pairs_p=[]; pairs_m=[]; overlay=[]
            masses=de1.get("weight_g",de1.get("weight",[]))
            for i,t in enumerate(de1["elapsed_s"]):
                model=nearest(trace,"time_s",float(t))
                pairs_p.append((float(model["basketPressurePa"])/1e5,float(de1["pressure_bar"][i])))
                if i < len(masses): pairs_m.append((float(model["cup_beverage_mass_kg"])*1e3,float(masses[i])))
                overlay.append([float(t),float(de1["pressure_bar"][i]),pairs_p[-1][0]])
            p_rmse=rmse(pairs_p); m_rmse=rmse(pairs_m)
            row.update({"comparison_outputs":["pressure","scale_mass"],"direction_result":"PASS","scale_result":"PASS" if p_rmse<2 else "FAIL",
                        "shape_result":"PASS" if p_rmse<2 else "FAIL","timing_result":"DIRECT_RECORDED_TIME",
                        "residual_signature":f"pressure_rmse_bar={p_rmse:.6g};mass_rmse_g={m_rmse if m_rmse is not None else 'UNAVAILABLE'}",
                        "claim_label":"WORKING" if p_rmse<2 else "PARTIAL"})
            overlays[cid]=overlay
        else:
            last=trace[-1]
            row.update({"comparison_outputs":["permeability_gradient_response"],"direction_result":"PASS" if float(last["outlet_flow_m3_s"])>=0 else "FAIL",
                        "scale_result":"SOURCE_RECONSTRUCTION","shape_result":"SINGLE_POINT_NOT_ASSESSED","timing_result":"SATURATED_STEADY_FIXTURE",
                        "residual_signature":f"outlet_flow_m3_s={float(last['outlet_flow_m3_s']):.9g};inertial_fraction={float(last['integratedInertialPressureFraction']):.9g}",
                        "claim_label":"PARTIAL"})
        rows_out.append(row)
    dump(output, {"schema_version":"espresso.validation.val_corpus_001.results.v1","task":TASK,
                  "protocol_sha256":sha256(root/"validation/cases/val_corpus_001/VAL_CORPUS_001_PROTOCOL.json"),
                  "execution_summary":{"attempted":len(execution["attempts"]),"completed":sum(x["status"]=="COMPLETED" for x in execution["attempts"]),"failed":sum(x["status"]!="COMPLETED" for x in execution["attempts"])},
                  "rows":rows_out,"overlays":overlays,
                  "claim_ceiling":protocol["claim_ceiling"]})


def correction_protocol(root: Path):
    return load(root / "validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json")


def prepare_r1(root: Path, snapshot: Path, run_root: Path) -> None:
    protocol = correction_protocol(root)
    if subprocess.check_output(["git", "-C", str(snapshot), "rev-parse", "HEAD"], text=True).strip() != SNAPSHOT_COMMIT:
        raise RuntimeError("evidence snapshot commit mismatch")
    if subprocess.check_output(["git", "-C", str(snapshot), "rev-parse", "HEAD^{tree}"], text=True).strip() != SNAPSHOT_TREE:
        raise RuntimeError("evidence snapshot tree mismatch")
    configs = run_root / "configs"
    configs.mkdir(parents=True, exist_ok=False)
    base = load(root / "config/reconstruction_WP02A_waszkiewicz_9bar.json")
    reference = load(root / "config/reference_R0.json")
    machine = load(root / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json")["case_matrix"]["MC-2"]["machineBoundary"]
    anchor_k = float(protocol["anchor"]["resulting_permeability_m2"])
    terminal = {bar: source_terminal(snapshot, float(bar)) for bar in (5, 9, 11)}
    records = []
    for item in protocol["correction_matrix"]:
        cid = item["id"]
        if cid.startswith("R1-WASZ"):
            cfg = copy.deepcopy(base)
            bar = int(item["source_group_bar"])
            cfg["scenario_id"] = cid.replace("-", "_")
            cfg["liquid"]["density_kg_m3"] = 965.0
            cfg["hydraulics"]["saturated_permeability_m2"] = anchor_k
            cfg["hydraulics"]["wetting_permeability_m2"] = anchor_k
            profile = cfg["hydraulics"].get("permeability_profile", {})
            profile["upstream_permeability_m2"] = anchor_k
            profile["downstream_permeability_m2"] = anchor_k
            cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = (
                float(terminal[bar]["basket_pressure__bar"]) * 1e5
                if item["pressure"] == "MEASURED_TERMINAL_BASKET" else bar * 1e5
            )
            cfg["time"].update({"end_s":103.0,"delta_t_s":0.02,"field_write_interval_s":1.0})
            cfg["geometry"].update({"axial_cells":128,"radial_cells":64})
            if "DISSOLUTION_INDEXED" in item["branch"]:
                closure = cfg.get("effective_permeability_evolution")
                if not isinstance(closure, dict) or closure.get("enabled") is not True:
                    raise RuntimeError(f"{cid}: dissolution-indexed closure absent or disabled")
            else:
                cfg.pop("effective_permeability_evolution", None)
                if "effective_permeability_evolution" in cfg:
                    raise RuntimeError(f"{cid}: static branch inherited dissolution closure")
            if item["branch"] == "DARCY_FORCHHEIMER_STATIC":
                cfg["flowResistanceModel"] = "darcyForchheimer"
                cfg["inertialPermeabilityModel"] = "wadsworth2026CeramicsFit"
                cfg["nonlinearControls"] = {"relativeTolerance":1e-9,"absoluteTolerance":1e-13,"maximumIterations":80,"underRelaxation":0.8,"machineFluxRelativeTolerance":1e-8}
            else:
                cfg["flowResistanceModel"] = "darcy"
                cfg.pop("inertialPermeabilityModel", None)
                cfg.pop("constantInertialPermeabilityM", None)
                cfg.pop("nonlinearControls", None)
            cfg["governance"] = governance("SOURCE_ANCHORED_RECONSTRUCTION")
            cfg["claim_ceiling"] = "Review-corrected source-anchored reconstruction; physical validation NOT_ESTABLISHED."
        else:
            cfg = copy.deepcopy(reference)
            cfg["scenario_id"] = cid.replace("-", "_")
            cfg["coffee_bed"].update({"dry_dose_kg":0.018,"bed_depth_m":0.009})
            cfg["pressureBoundaryModel"] = "lumpedMachineCompliance"
            cfg["machineBoundary"] = copy.deepcopy(machine)
            cfg["time"].update({"end_s":25.0,"delta_t_s":0.02,"field_write_interval_s":1.0})
            cfg["geometry"].update({"axial_cells":128,"radial_cells":64})
            cfg["governance"] = governance("GENERIC_MACHINE_FIXTURE_OVERLAY_AGAINST_DE1_TRACE")
            cfg["claim_ceiling"] = "Descriptive generic-machine overlay; physical validation NOT_ESTABLISHED."
        path = configs / f"{cid}.json"
        dump(path, cfg)
        records.append({"id":cid,"sha256":sha256(path),"branch":item["branch"],"closure_present":"effective_permeability_evolution" in cfg})
    dump(run_root / "R1_PREPARATION_RECORD.json", {
        "schema_version":"espresso.validation.val_corpus_001.r1_preparation.v1",
        "protocol_sha256":sha256(root / "validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json"),
        "source_snapshot":{"commit":SNAPSHOT_COMMIT,"tree":SNAPSHOT_TREE},
        "anchor":protocol["anchor"],"configs":records})


def run_r1(root: Path, run_root: Path, executable: Path, ranks: int) -> None:
    attempts = []
    for config in sorted((run_root / "configs").glob("*.json")):
        cid, case = config.stem, run_root / "cases" / config.stem
        started = datetime.now(timezone.utc).isoformat(); t0 = time.monotonic()
        status, reason, classification, launched = "FAILED", "", "PRE_LAUNCH_FAILURE", False
        try:
            subprocess.run(["python3",str(root/"scripts/prepare_case.py"),"--root",str(root),"--config",str(config),"--case-dir",str(case),"--nprocs",str(ranks)],check=True)
            with (case/"log.blockMesh").open("w") as log: subprocess.run(["blockMesh"],cwd=case,stdout=log,stderr=subprocess.STDOUT,check=True)
            with (case/"log.checkMesh").open("w") as log: subprocess.run(["checkMesh"],cwd=case,stdout=log,stderr=subprocess.STDOUT,check=True)
            env = dict(os.environ, ESPRESSO_CASE_ROOT=str(case)); launched = True
            with (case/"log.decomposePar").open("w") as log: subprocess.run(["decomposePar","-force"],cwd=case,stdout=log,stderr=subprocess.STDOUT,check=True)
            with (case/"log.solver").open("w") as log: subprocess.run(["mpirun","-np",str(ranks),str(executable),"-parallel"],cwd=case,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            solver_text=(case/"log.solver").read_text(errors="replace")
            if "FOAM FATAL ERROR" in solver_text or "\nEnd\n" not in solver_text:
                reason="solver log contains FOAM FATAL ERROR or lacks terminal End marker"; classification="SOLVER_FAILURE"
            else: status, classification = "COMPLETED", "COMPLETED"
        except Exception as exc:
            reason=f"{type(exc).__name__}: {exc}"; classification="SOLVER_FAILURE" if launched else "PRE_LAUNCH_FAILURE"
        trace=case/"postProcessing/wholePull/0/traces.csv"
        attempts.append({"id":cid,"status":status,"failure_reason":reason,"failure_classification":classification,
            "openfoam_launched":launched,"started_utc":started,"duration_s":round(time.monotonic()-t0,6),
            "config_path":f"configs/{config.name}","config_sha256":sha256(config),
            "trace_path":f"cases/{cid}/postProcessing/wholePull/0/traces.csv","trace_present":trace.is_file(),
            "trace_size":trace.stat().st_size if trace.is_file() else 0,"trace_sha256":sha256(trace) if trace.is_file() else None})
        dump(run_root/"R1_EXECUTION_RECORD.json", {"schema_version":"espresso.validation.val_corpus_001.r1_execution.v1","task":TASK,
            "executable_sha256":sha256(executable),"ranks":ranks,"attempts":attempts})


def linear_value(rows, time_key: str, value_key: str, target: float):
    points=[(float(r[time_key]),float(r[value_key])) for r in rows if r.get(time_key) not in (None,"") and r.get(value_key) not in (None,"")]
    if not points or target < points[0][0]-1e-12 or target > points[-1][0]+1e-12: return None
    if target <= points[0][0]+1e-12: return points[0][1]
    for (t0,v0),(t1,v1) in zip(points,points[1:]):
        if t0-1e-12 <= target <= t1+1e-12:
            if abs(t1-t0)<1e-15: return v1
            f=(target-t0)/(t1-t0); return v0+f*(v1-v0)
    return points[-1][1] if abs(target-points[-1][0])<1e-9 else None


def metric(observed, modeled, sigma=None):
    pairs=[(float(o),float(m)) for o,m in zip(observed,modeled) if o is not None and m is not None]
    residual=[m-o for o,m in pairs]; n=len(pairs)
    result={"sample_count":n,"rmse":math.sqrt(sum(x*x for x in residual)/n),"mae":sum(abs(x) for x in residual)/n,
            "signed_bias":sum(residual)/n,"relative_endpoint_error":residual[-1]/pairs[-1][0] if pairs[-1][0] else None,
            "median_absolute_log_ratio":sorted(abs(math.log(max(abs(m),1e-30)/max(abs(o),1e-30))) for o,m in pairs)[n//2]}
    if sigma is not None:
        valid=[(abs(m-o),float(s)) for (o,m),s in zip(pairs,sigma) if s is not None and float(s)>0]
        result["source_uncertainty_coverage"] = sum(e<=s for e,s in valid)/len(valid) if valid else None
    else: result["source_uncertainty_coverage"] = None
    return result


def spearman3(source, model):
    def ranks(values):
        order=sorted(range(len(values)),key=lambda i:values[i]); out=[0]*len(values)
        for rank,i in enumerate(order,1): out[i]=rank
        return out
    a,b=ranks(source),ranks(model); n=len(a)
    return 1-6*sum((x-y)**2 for x,y in zip(a,b))/(n*(n*n-1))


def windows_metrics(source_rows, model_rows, density, solver_end=103.0):
    selected=[r for r in source_rows if 0 <= float(r["time__s"]) <= min(100.0,solver_end-3.0)]
    modeled={"pressure":[],"flow":[],"mass":[]}; observed={"pressure":[],"flow":[],"mass":[]}; sigma={"pressure":[],"flow":[],"mass":[]}
    overlay=[]
    for row in selected:
        ts=float(row["time__s"]); tm=ts+3.0
        values={"pressure":linear_value(model_rows,"time_s","inlet_pressure_Pa",tm),
                "flow":linear_value(model_rows,"time_s","outlet_flow_m3_s",tm),
                "mass":linear_value(model_rows,"time_s","cup_beverage_mass_kg",tm)}
        if any(v is None for v in values.values()): continue
        modp=values["pressure"]/1e5; modf=values["flow"]*density*1000; modm=values["mass"]*1000
        obs=[float(row["basket_pressure__bar"]),float(row["mass_flow_rate__g_per_s"]),float(row["mass__g"])]
        for key,m,o,skey in (("pressure",modp,obs[0],"basket_pressure_std__bar"),("flow",modf,obs[1],"mass_flow_rate_std__g_per_s"),("mass",modm,obs[2],"mass_std__g")):
            modeled[key].append(m); observed[key].append(o); sigma[key].append(float(row[skey]))
        overlay.append([ts,tm,obs[0],modp,obs[1],modf,obs[2],modm])
    result={}
    bounds={"early":(0,100/3),"middle":(100/3,200/3),"late":(200/3,100.0000001)}
    times=[x[0] for x in overlay]
    for key in ("pressure","flow","mass"):
        result[key]={"full":metric(observed[key],modeled[key],sigma[key])}
        for label,(lo,hi) in bounds.items():
            idx=[i for i,t in enumerate(times) if lo<=t<hi]
            result[key][label]=metric([observed[key][i] for i in idx],[modeled[key][i] for i in idx],[sigma[key][i] for i in idx]) if idx else None
    result["source_window_s"]=[times[0],times[-1]]; result["model_window_s"]=[times[0]+3,times[-1]+3]
    result["alignment_rule"]="solver_time=source_time+3.0s"; result["interpolation_rule"]="linear within domain; no extrapolation"
    return result,overlay


def analyze_r1(root: Path, snapshot: Path, original_root: Path, run_root: Path, output: Path, overlays_output: Path) -> None:
    protocol=correction_protocol(root); evidence=read_csv(snapshot/"puckworks/data/waszkiewicz2025/traces_time_dependent.csv")
    execution=load(run_root/"R1_EXECUTION_RECORD.json"); attempts={x["id"]:x for x in execution["attempts"]}
    rows=[]; overlays={}; groups={bar:[r for r in evidence if float(r["reference_pressure_round__bar"])==bar] for bar in (5,9,11)}
    wasz={}
    for item in protocol["correction_matrix"]:
        cid=item["id"]; attempt=attempts[cid]
        if not cid.startswith("R1-WASZ"): continue
        trace=run_root/attempt["trace_path"]
        if attempt["status"]!="COMPLETED" or not trace.is_file():
            rows.append({"id":cid,"label":"INVALIDATED_EXECUTION","failure":attempt["failure_reason"]}); continue
        metrics,overlay=windows_metrics(groups[int(item["source_group_bar"])],read_csv(trace),965.0)
        wasz[cid]=metrics; overlays[cid]=overlay
    families={}
    for branch in ("DARCY_STATIC","DARCY_FORCHHEIMER_STATIC","DARCY_DISSOLUTION_INDEXED"):
        ids=[x["id"] for x in protocol["correction_matrix"] if x.get("branch")==branch and x.get("pressure")=="MEASURED_TERMINAL_BASKET"]
        src_flow=[float(source_terminal(snapshot,b)["mass_flow_rate__g_per_s"]) for b in (5,9,11)]
        src_mass=[float(source_terminal(snapshot,b)["mass__g"]) for b in (5,9,11)]
        mod_flow=[overlays[i][-1][5] for i in ids]; mod_mass=[overlays[i][-1][7] for i in ids]
        families[branch]={"ids":ids,"flow_spearman":spearman3(src_flow,mod_flow),"mass_spearman":spearman3(src_mass,mod_mass),
            "source_flow_order":[ids[i] for i in sorted(range(3),key=lambda j:src_flow[j],reverse=True)],
            "model_flow_order":[ids[i] for i in sorted(range(3),key=lambda j:mod_flow[j],reverse=True)],
            "source_mass_order":[ids[i] for i in sorted(range(3),key=lambda j:src_mass[j],reverse=True)],
            "model_mass_order":[ids[i] for i in sorted(range(3),key=lambda j:mod_mass[j],reverse=True)]}
    for cid,metrics in wasz.items():
        branch=next(x["branch"] for x in protocol["correction_matrix"] if x["id"]==cid)
        order=families.get(branch); cover=[metrics[k]["full"]["source_uncertainty_coverage"] for k in ("pressure","flow","mass")]
        correct=order is not None and order["flow_spearman"]==1 and order["mass_spearman"]==1
        wrong_order = order is not None and (order["flow_spearman"] != 1 or order["mass_spearman"] != 1)
        if wrong_order:
            label = "FAILING"
        elif correct and all(x is not None and x >= .68 for x in cover):
            label = "WORKING"
        elif correct or any(x is not None and x > 0 for x in cover):
            label = "PARTIAL"
        else:
            label = "FAILING"
        rows.append({"id":cid,"source":"waszkiewicz2025","branch":branch,"comparison_mode":"SOURCE_ANCHORED_RECONSTRUCTION",
            "metrics":metrics,"ordering":order,"label":label,"density_kg_m3":965.0})
    # Historical 30 s traces: valid aligned overlap only, source 0..27 s.
    historical=[]
    old_cases=original_root/"consolidated/cases"
    for bar in (5,9,11):
        for suffix,branch in (("DARCY","DISSOLUTION_INDEXED_DARCY_30S"),("DF","DISSOLUTION_INDEXED_DARCY_FORCHHEIMER_30S")):
            cid=f"WASZ-{bar}-{suffix}"; trace=old_cases/cid/"postProcessing/wholePull/0/traces.csv"
            m,o=windows_metrics(groups[bar],read_csv(trace),965.0,30.0); overlays[f"HISTORICAL-{cid}"]=o
            historical.append({"id":cid,"branch":branch,"valid_overlap_source_s":[0,27],"metrics":m,"label":"DESCRIPTIVE_ONLY"})
    # Foster frozen shift sensitivity using retained trace.
    foster_source=read_csv(snapshot/"puckworks/data/foster2025_2/fig6_front_position.csv")
    foster_model=read_csv(old_cases/"FOSTER-WETTING/postProcessing/wholePull/0/traces.csv")
    foster=[]
    for shift in (0.0,.796,1.0):
        obs=[]; mod=[]; sig=[]; overlay=[]
        for r in foster_source:
            t=float(r["t_s"]); v=linear_value(foster_model,"time_s","wet_front_m",t+shift)
            if v is None: continue
            obs.append(float(r["s_mm"])); mod.append(v*1000); sig.append(float(r["s_err_mm"])); overlay.append([t,t+shift,obs[-1],mod[-1]])
        mm=metric(obs,mod,sig); mm["early_middle_late"]={}
        for label,lo,hi in (("early",0,8/3),("middle",8/3,16/3),("late",16/3,8.0001)):
            ii=[i for i,x in enumerate(overlay) if lo<=x[0]<hi]; mm["early_middle_late"][label]=metric([obs[i] for i in ii],[mod[i] for i in ii],[sig[i] for i in ii]) if ii else None
        key=f"FOSTER-SHIFT-{shift}"; overlays[key]=overlay; foster.append({"shift_s":shift,"metrics":mm,"model_first_drip_s":float(foster_model[-1]["first_drip_s"]),"first_drip_error":"NOT_SCORED_NO_ADMISSIBLE_OBSERVED_EVENT","label":"PARTIAL"})
    # DE1 low/base/high descriptive overlays.
    de1=load(snapshot/"puckworks/data/de1_fixtureA.json"); de1_results=[]
    de1_paths={"LOW":old_cases/"DE1-MACHINE-LOW/postProcessing/wholePull/0/traces.csv","BASE":run_root/attempts["R1-DE1-MACHINE-BASE-9MM"]["trace_path"],"HIGH":old_cases/"DE1-MACHINE-HIGH/postProcessing/wholePull/0/traces.csv"}
    for level,path in de1_paths.items():
        model=read_csv(path); op=[];mp=[];om=[];mm=[];overlay=[]
        for i,t in enumerate(de1["elapsed_s"]):
            pv=linear_value(model,"time_s","basketPressurePa",float(t)); mv=linear_value(model,"time_s","cup_beverage_mass_kg",float(t))
            if pv is None or mv is None: continue
            op.append(float(de1["pressure_bar"][i]));mp.append(pv/1e5);om.append(float(de1["weight_g"][i]));mm.append(mv*1000);overlay.append([float(t),op[-1],mp[-1],om[-1],mm[-1]])
        overlays[f"DE1-{level}"]=overlay; de1_results.append({"assumption":level,"bed_depth_m":{"LOW":.0075,"BASE":.009,"HIGH":.0105}[level],"pressure":metric(op,mp),"mass":metric(om,mm),"label":"DESCRIPTIVE_ONLY"})
    overlay_bytes=(json.dumps(overlays,indent=2,sort_keys=True)+"\n").encode(); overlays_output.parent.mkdir(parents=True,exist_ok=True); overlays_output.write_bytes(overlay_bytes)
    result={"schema_version":"espresso.validation.val_corpus_001.results.v2","task":"VAL-CORPUS-001-EXACT-HEAD-REVIEW-CORRECTION",
        "protocol_sha256":sha256(root/"validation/cases/val_corpus_001/VAL_CORPUS_001_REVIEW_CORRECTION_PROTOCOL.json"),
        "superseded_result_sha256":protocol["superseded"]["result_bundle_sha256"],
        "execution":{"attempted":len(execution["attempts"]),"launched":sum(x["openfoam_launched"] for x in execution["attempts"]),"completed":sum(x["status"]=="COMPLETED" for x in execution["attempts"]),"failed":sum(x["status"]!="COMPLETED" for x in execution["attempts"])},
        "waszkiewicz_rows":rows,"waszkiewicz_family_ordering":families,"historical_overlap_only":historical,"foster_shift_sensitivity":foster,"de1_assumption_sensitivity":de1_results,
        "retained_dispositions":{"compaction":"INVALIDATED_NUMERICAL_EXECUTION_POROELASTIC_NONLINEAR_FAILURE; separate numerical-robustness finding, not physical-model verdict","wadsworth_roman":"COMPONENT_EQUATION_RECONSTRUCTION","mo":"DESCRIPTIVE_ONLY_QUALITATIVE_MECHANISM_DIAGNOSTIC_UNRESOLVED_COEFFICIENT_UNITS"},
        "mass_conversion_sensitivity_kg_m3":[965.0,997.0,1000.0],"overlays":{"path":overlays_output.name,"sha256":hashlib.sha256(overlay_bytes).hexdigest(),"bytes":len(overlay_bytes)},
        "claim_ceiling":protocol["claim_ceiling"]}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=["prepare","run","analyze","prepare-r1","run-r1","analyze-r1"])
    parser.add_argument("--root",type=Path,required=True); parser.add_argument("--snapshot",type=Path)
    parser.add_argument("--run-root",type=Path,required=True); parser.add_argument("--executable",type=Path)
    parser.add_argument("--ranks",type=int,default=16); parser.add_argument("--output",type=Path)
    parser.add_argument("--original-root",type=Path); parser.add_argument("--overlays-output",type=Path)
    args=parser.parse_args(); root=args.root.resolve(); run_root=args.run_root.resolve()
    if args.command=="prepare": prepare(root,args.snapshot.resolve(),run_root)
    elif args.command=="run": run(root,run_root,args.executable.resolve(),args.ranks)
    elif args.command=="analyze": analyze(root,args.snapshot.resolve(),run_root,args.output.resolve())
    elif args.command=="prepare-r1": prepare_r1(root,args.snapshot.resolve(),run_root)
    elif args.command=="run-r1": run_r1(root,run_root,args.executable.resolve(),args.ranks)
    else: analyze_r1(root,args.snapshot.resolve(),args.original_root.resolve(),run_root,args.output.resolve(),args.overlays_output.resolve())


if __name__ == "__main__": main()
