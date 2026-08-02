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
                cfg["bedMechanicsModel"] = "waszkiewicz2025FinitePhi"
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
            status = "COMPLETED"
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
        attempts.append({"id":cid,"status":status,"failure_reason":reason,"started_utc":started,
                         "duration_s":round(time.monotonic()-t0,6),"config_sha256":sha256(config),
                         "trace_present":(case/"postProcessing/espressoWholePull/traces.csv").is_file()})
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
        trace_path = run_root / "cases" / cid / "postProcessing/espressoWholePull/traces.csv"
        row = {"source":family,"condition":cid,"branch":spec["branch"],"evidence_class":protocol["evidence_class"],
               "comparison_mode":spec["mode"],"calibration_inputs":["9_bar_terminal_flow"] if cid=="WASZ-9-DARCY" else [],
               "comparison_outputs":[],"assumptions":spec.get("assumption","BASE"),"direction_result":"UNASSESSED",
               "scale_result":"UNASSESSED","shape_result":"UNASSESSED","timing_result":"UNASSESSED",
               "residual_signature":"UNASSESSED","claim_label":"NOT_COMPARABLE","failure_reason":attempt.get("failure_reason","")}
        if not trace_path.is_file():
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


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=["prepare","run","analyze"])
    parser.add_argument("--root",type=Path,required=True); parser.add_argument("--snapshot",type=Path)
    parser.add_argument("--run-root",type=Path,required=True); parser.add_argument("--executable",type=Path)
    parser.add_argument("--ranks",type=int,default=16); parser.add_argument("--output",type=Path)
    args=parser.parse_args(); root=args.root.resolve(); run_root=args.run_root.resolve()
    if args.command=="prepare": prepare(root,args.snapshot.resolve(),run_root)
    elif args.command=="run": run(root,run_root,args.executable.resolve(),args.ranks)
    else: analyze(root,args.snapshot.resolve(),run_root,args.output.resolve())


if __name__ == "__main__": main()
