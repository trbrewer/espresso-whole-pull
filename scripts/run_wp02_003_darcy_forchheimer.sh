#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${WP02_003_RUN_ROOT:=/tmp/wp02-003-darcy-forchheimer}"
: "${WP02_003_NPROCS:=32}"
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
EXE=$(command -v espressoWholePullFoam)
test -x "$EXE"
(
  cd "$ROOT/validation/wp02"
  sha256sum -c WP02_003_DARCY_FORCHHEIMER_RUN_SPEC.sha256
)
mkdir -p "$WP02_003_RUN_ROOT/configs" "$WP02_003_RUN_ROOT/cases" \
  "$WP02_003_RUN_ROOT/timing"

python3 - "$ROOT" "$WP02_003_RUN_ROOT/configs" <<'PY'
import copy, json, pathlib, sys
root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
base = json.loads((root / "config/reference_R0.json").read_text())
spec = json.loads((root / "validation/wp02/WP02_003_DARCY_FORCHHEIMER_RUN_SPEC.json").read_text())
machine_spec = json.loads((root / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text())
wp02 = json.loads((root / "config/reconstruction_WP02A_waszkiewicz_9bar.json").read_text())
controls = spec["nonlinear_controls"]

def make(cid):
    cfg = copy.deepcopy(base)
    cfg["scenario_id"] = "WP02_003_" + cid.replace("-", "_").replace(".", "p")
    item = spec["case_matrix"][cid]
    cfg["pressureBoundaryModel"] = item.get("pressureBoundaryModel", "lumpedMachineCompliance")
    if cfg["pressureBoundaryModel"] == "lumpedMachineCompliance":
        cfg["machineBoundary"] = copy.deepcopy(machine_spec["case_matrix"]["MC-2"]["machineBoundary"])
    cfg["flowResistanceModel"] = item["flowResistanceModel"]
    if cfg["flowResistanceModel"] == "darcyForchheimer":
        cfg["inertialPermeabilityModel"] = item["inertialPermeabilityModel"]
        cfg["constantInertialPermeabilityM"] = item.get("constantInertialPermeabilityM", 1.0)
        cfg["nonlinearControls"] = copy.deepcopy(controls)
    if cid == "DF-6":
        cfg["effective_permeability_evolution"] = copy.deepcopy(
            wp02["effective_permeability_evolution"]
        )
    cfg["governance"] = {
        "task": "WP02-003",
        "change_scope": "GOVERNING_PHYSICS_CHANGE",
        "evidence_role": "NUMERICAL_VERIFICATION_AND_SYNTHETIC_MECHANISM_DIAGNOSTIC",
    }
    cfg["claim_ceiling"] = "Physical validation NOT_ESTABLISHED; synthetic mechanism diagnostic."
    return cfg

for cid in spec["case_matrix"]:
    (out / f"{cid}.json").write_text(json.dumps(make(cid), indent=2) + "\n")

for dt in (0.02, 0.01, 0.005):
    cfg = make("DF-3")
    cfg["scenario_id"] = "WP02_003_DF_3_DT_" + str(dt).replace(".", "p")
    cfg["time"]["delta_t_s"] = dt
    (out / f"DF-3-DT-{dt}.json").write_text(json.dumps(cfg, indent=2) + "\n")

def fixture(name, layered=False, machine=False, ki=1e-10):
    cfg = make("DF-3" if machine else "DF-1")
    cfg["scenario_id"] = "WP02_003_" + name.replace("-", "_")
    cfg["geometry"].update({"axial_cells": 32, "radial_cells": 8})
    dx = cfg["coffee_bed"]["bed_depth_m"] / cfg["geometry"]["axial_cells"]
    for probe in cfg["verification"]["pressure_probes"]:
        probe["half_width_m"] = 0.51 * dx
    cfg["wetting"].update({
        "initial_saturation": 1.0,
        "initial_wet_front_m": cfg["coffee_bed"]["bed_depth_m"],
    })
    cfg["hydraulics"]["pressure_ramp_time_s"] = 0.0
    cfg["time"].update({"end_s": 0.02, "delta_t_s": 0.02, "field_write_interval_s": 0.02})
    cfg["inertialPermeabilityModel"] = "constant"
    cfg["constantInertialPermeabilityM"] = ki
    if layered:
        depth = cfg["coffee_bed"]["bed_depth_m"]
        cfg["hydraulics"]["permeability_profile"] = {
            "type": "axial_two_layer",
            "interface_position_m": 0.5 * depth,
            "upstream_permeability_m2": 1.2e-15,
            "downstream_permeability_m2": 3.4e-15,
            "upstream_inertial_permeability_m": 4e-11,
            "downstream_inertial_permeability_m": 1.3e-10,
        }
    return cfg

(out / "UNIFORM.json").write_text(json.dumps(fixture("UNIFORM"), indent=2) + "\n")
(out / "LAYERED.json").write_text(json.dumps(fixture("LAYERED", layered=True), indent=2) + "\n")
(out / "MACHINE.json").write_text(json.dumps(fixture("MACHINE", machine=True), indent=2) + "\n")
for index, ki in enumerate((1e-8, 1e-5, 1e-2)):
    (out / f"LIMIT-{index}.json").write_text(
        json.dumps(fixture(f"LIMIT_{index}", ki=ki), indent=2) + "\n"
    )
PY

run_case() {
  local cid=$1
  local ranks=$2
  local case_dir="$WP02_003_RUN_ROOT/cases/$cid"
  if [[ -e "$case_dir" ]]; then
    echo "Refusing to overwrite existing governed run: $case_dir" >&2
    return 2
  fi
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP02_003_RUN_ROOT/configs/$cid.json" \
    --case-dir "$case_dir" --nprocs "$ranks"
  (
    cd "$case_dir"
    blockMesh > log.blockMesh
    checkMesh > log.checkMesh
    if (( ranks > 1 )); then
      decomposePar -force > log.decomposePar
      /usr/bin/time -v -o "$WP02_003_RUN_ROOT/timing/$cid.time" \
        env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$ranks" \
        "$EXE" -parallel > log.solver 2>&1
    else
      /usr/bin/time -v -o "$WP02_003_RUN_ROOT/timing/$cid.time" \
        env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" > log.solver 2>&1
    fi
  )
}

for cid in UNIFORM LAYERED MACHINE LIMIT-0 LIMIT-1 LIMIT-2; do
  run_case "$cid" 1
done

if [[ "${WP02_003_FIXTURES_ONLY:-0}" == 1 ]]; then
  exit 0
fi

for cid in DF-0 DF-1 DF-2 DF-3 DF-4 DF-5 DF-6; do
  run_case "$cid" "$WP02_003_NPROCS"
done
for dt in 0.02 0.01 0.005; do
  run_case "DF-3-DT-$dt" "$WP02_003_NPROCS"
done

"$ROOT/scripts/run_wp02_003_zero_inertia_fixture.sh" \
  "$WP02_003_RUN_ROOT/WP02_003_ZERO_INERTIA_FIXTURE.json"
WP02_003_REGRESSION_ROOT="$WP02_003_RUN_ROOT/predecessor-regressions" \
  "$ROOT/scripts/run_wp02_003_predecessor_regressions.sh"

python3 "$ROOT/scripts/analyze_wp02_003_darcy_forchheimer.py" \
  --root "$ROOT" --run-root "$WP02_003_RUN_ROOT" \
  --zero-inertia-result \
    "$WP02_003_RUN_ROOT/WP02_003_ZERO_INERTIA_FIXTURE.json" \
  --regression-root "$WP02_003_RUN_ROOT/predecessor-regressions" \
  --coupling-disabled-result \
    "$WP02_003_RUN_ROOT/predecessor-regressions/WP02_COUPLING_DISABLED_REGRESSION.json" \
  --output "$WP02_003_RUN_ROOT/WP02_003_DARCY_FORCHHEIMER_RESULTS.json" \
  --trace-output "$WP02_003_RUN_ROOT/WP02_003_DARCY_FORCHHEIMER_TRACE.csv"
