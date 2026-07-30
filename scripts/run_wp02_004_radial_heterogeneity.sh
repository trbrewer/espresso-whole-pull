#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${WP02_004_RUN_ROOT:=/tmp/wp02-004-radial-heterogeneity}"
: "${WP02_004_NPROCS:=32}"
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
EXE=$(command -v espressoWholePullFoam)
test -x "$EXE"
(cd "$ROOT/validation/wp02" && sha256sum -c WP02_004_RADIAL_HETEROGENEITY_RUN_SPEC.sha256)
mkdir -p "$WP02_004_RUN_ROOT/configs" "$WP02_004_RUN_ROOT/cases" \
  "$WP02_004_RUN_ROOT/timing"

python3 - "$ROOT" "$WP02_004_RUN_ROOT/configs" <<'PY'
import copy, json, pathlib, sys
root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
base = json.loads((root/"config/reference_R0.json").read_text())
spec = json.loads((root/"validation/wp02/WP02_004_RADIAL_HETEROGENEITY_RUN_SPEC.json").read_text())
machine = json.loads((root/"validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text())["case_matrix"]["MC-2"]["machineBoundary"]
k0 = spec["reference"]["reference_permeability_m2"]
radius = spec["reference"]["basket_radius_m"]
profiles = spec["matched_profiles"]

def profile_for(item):
    if item["profile"] == "uniform":
        return {"type": "uniform"}
    if item.get("contrast") == 1:
        ki = ko = k0
    else:
        p = profiles[f"c{item['contrast']}_{'high_inner' if item['high_zone']=='inner' else 'high_outer'}"]
        ki, ko = p["inner_permeability_m2"], p["outer_permeability_m2"]
    return {"type": "radial_two_zone", "interface_radius_m": 0.5*radius,
            "inner_permeability_m2": ki, "outer_permeability_m2": ko}

def make(cid):
    item = spec["case_matrix"][cid]
    cfg = copy.deepcopy(base)
    cfg["scenario_id"] = "WP02_004_" + cid.replace("-", "_")
    cfg["pressureBoundaryModel"] = item["pressure"]
    if item["pressure"] == "lumpedMachineCompliance":
        cfg["machineBoundary"] = copy.deepcopy(machine)
    cfg["flowResistanceModel"] = item["flow"]
    cfg["hydraulics"]["permeability_profile"] = profile_for(item)
    if item["flow"] == "darcyForchheimer":
        cfg["inertialPermeabilityModel"] = item["inertial"]
        cfg["constantInertialPermeabilityM"] = 1.0
        cfg["nonlinearControls"] = {
            "nonlinearRelativeTolerance": 1e-10,
            "nonlinearAbsoluteTolerance": 1e-10,
            "nonlinearMaximumIterations": 100,
            "nonlinearUnderRelaxation": 0.7,
            "machineFluxRelativeTolerance": 1e-6}
    cfg["governance"] = {"task": "WP02-004",
      "change_scope": "GOVERNING_PHYSICS_CHANGE",
      "evidence_role": "NUMERICAL_VERIFICATION_AND_SYNTHETIC_SPATIAL_HETEROGENEITY_DIAGNOSTIC"}
    cfg["claim_ceiling"] = "Physical validation NOT_ESTABLISHED; synthetic static heterogeneity."
    return cfg

for cid in spec["case_matrix"]:
    (out/f"{cid}.json").write_text(json.dumps(make(cid), indent=2)+"\n")
for dt in (0.02, 0.01, 0.005):
    cfg = make("RH-6"); cfg["scenario_id"] += "_DT_"+str(dt).replace(".","p")
    cfg["time"]["delta_t_s"] = dt
    (out/f"RH-6-DT-{dt}.json").write_text(json.dumps(cfg,indent=2)+"\n")
for nr in (256,512,1024):
    cfg = make("RH-6"); cfg["scenario_id"] += f"_NR_{nr}"
    cfg["geometry"]["radial_cells"] = nr
    (out/f"RH-6-NR-{nr}.json").write_text(json.dumps(cfg,indent=2)+"\n")

def fixture(cid, flow="darcy", machine_mode=False):
    cfg = make("RH-6" if machine_mode else "RH-2")
    cfg["scenario_id"] = "WP02_004_"+cid
    cfg["geometry"].update({"axial_cells": 32, "radial_cells": 32})
    cfg["wetting"].update({"initial_saturation": 1.0,
                           "initial_wet_front_m": cfg["coffee_bed"]["bed_depth_m"]})
    cfg["hydraulics"]["pressure_ramp_time_s"] = 0.0
    cfg["time"].update({"end_s": 0.02, "delta_t_s": 0.02,
                        "field_write_interval_s": 0.02})
    if flow == "darcyForchheimer":
        cfg["flowResistanceModel"] = "darcyForchheimer"
        cfg["inertialPermeabilityModel"] = "constant"
        cfg["constantInertialPermeabilityM"] = 1e-10
        cfg["hydraulics"]["permeability_profile"].update({
            "inner_inertial_permeability_m": 2e-11,
            "outer_inertial_permeability_m": 9e-11})
        cfg["nonlinearControls"] = {
            "nonlinearRelativeTolerance": 1e-10,
            "nonlinearAbsoluteTolerance": 1e-10,
            "nonlinearMaximumIterations": 100,
            "nonlinearUnderRelaxation": 0.7,
            "machineFluxRelativeTolerance": 1e-6}
    return cfg
for cid, flow, mach in (("RADIAL-DARCY","darcy",False),
                        ("RADIAL-FORCH","darcyForchheimer",False),
                        ("MACHINE-RADIAL","darcyForchheimer",True)):
    (out/f"{cid}.json").write_text(json.dumps(fixture(cid,flow,mach),indent=2)+"\n")
PY

run_case() {
  local cid=$1 ranks=$2
  local case_dir="$WP02_004_RUN_ROOT/cases/$cid"
  test ! -e "$case_dir" || { echo "Refusing to overwrite $case_dir" >&2; return 2; }
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP02_004_RUN_ROOT/configs/$cid.json" --case-dir "$case_dir" --nprocs "$ranks"
  (
    cd "$case_dir"
    blockMesh >log.blockMesh
    checkMesh >log.checkMesh
    if ((ranks>1)); then
      decomposePar -force >log.decomposePar
      /usr/bin/time -v -o "$WP02_004_RUN_ROOT/timing/$cid.time" \
        env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$ranks" "$EXE" -parallel >log.solver 2>&1
    else
      /usr/bin/time -v -o "$WP02_004_RUN_ROOT/timing/$cid.time" \
        env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" >log.solver 2>&1
    fi
  )
}

for cid in RADIAL-DARCY RADIAL-FORCH MACHINE-RADIAL; do run_case "$cid" 1; done
scripts/run_wp02_004_production_fixture.sh \
  "$WP02_004_RUN_ROOT/WP02_004_PRODUCTION_FIXTURE.json"
if [[ ${WP02_004_FIXTURES_ONLY:-0} == 1 ]]; then exit 0; fi
for cid in RH-{0..8}; do run_case "$cid" "$WP02_004_NPROCS"; done
for dt in 0.02 0.01 0.005; do run_case "RH-6-DT-$dt" "$WP02_004_NPROCS"; done
for nr in 256 512 1024; do run_case "RH-6-NR-$nr" "$WP02_004_NPROCS"; done
WP02_003_RUN_ROOT="$WP02_004_RUN_ROOT/predecessor" \
  WP02_003_FIXTURES_ONLY=1 \
  "$ROOT/scripts/run_wp02_003_darcy_forchheimer.sh"
python3 "$ROOT/scripts/verify_wp02_regression.py" --root "$ROOT" \
  --results "$ROOT/validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json" \
  >"$WP02_004_RUN_ROOT/WP02_COUPLING_DISABLED_REGRESSION.json"
python3 "$ROOT/scripts/analyze_wp02_004_radial_heterogeneity.py" \
  --root "$ROOT" --run-root "$WP02_004_RUN_ROOT" \
  --predecessor-root "$WP02_004_RUN_ROOT/predecessor" \
  --coupling-disabled-result \
    "$WP02_004_RUN_ROOT/WP02_COUPLING_DISABLED_REGRESSION.json" \
  --executable "$EXE" \
  --output "$WP02_004_RUN_ROOT/WP02_004_RADIAL_HETEROGENEITY_RESULTS.json" \
  --trace-output "$WP02_004_RUN_ROOT/WP02_004_RADIAL_HETEROGENEITY_TRACE.csv"
