#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${WP02_002_RUN_ROOT:=/tmp/wp02-002-machine-coupling}"
: "${WP02_002_NPROCS:=32}"
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
EXE=$(command -v espressoWholePullFoam)
test -x "$EXE"
mkdir -p "$WP02_002_RUN_ROOT/configs" "$WP02_002_RUN_ROOT/cases" "$WP02_002_RUN_ROOT/timing"

python3 - "$ROOT" "$WP02_002_RUN_ROOT/configs" <<'PY'
import copy, json, pathlib, sys
root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
base=json.loads((root/"config/reference_R0.json").read_text())
spec=json.loads((root/"validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text())
wp02=json.loads((root/"config/reconstruction_WP02A_waszkiewicz_9bar.json").read_text())
for name, item in spec["case_matrix"].items():
    cfg=copy.deepcopy(base)
    cfg["scenario_id"]="WP02_002_"+name.replace("-","_")
    cfg["pressureBoundaryModel"]=item.get("pressureBoundaryModel","lumpedMachineCompliance")
    if cfg["pressureBoundaryModel"]=="lumpedMachineCompliance":
        machine=copy.deepcopy(spec["case_matrix"]["MC-2"]["machineBoundary"])
        if "machineBoundary" in item: machine=copy.deepcopy(item["machineBoundary"])
        if "upstreamCompliance" in item: machine["upstreamCompliance"]=item["upstreamCompliance"]
        cfg["machineBoundary"]=machine
    if name=="MC-5":
        cfg["effective_permeability_evolution"]=wp02["effective_permeability_evolution"]
    cfg["claim_ceiling"]="SYNTHETIC_ENGINEERING_DEMONSTRATION; physical validation NOT_ESTABLISHED."
    (out/(name+".json")).write_text(json.dumps(cfg,indent=2)+"\n")
PY

for dt in 0.04 0.02 0.01; do
  id="LF-$dt"
  python3 - "$WP02_002_RUN_ROOT/configs/MC-2.json" \
    "$WP02_002_RUN_ROOT/configs/$id.json" "$dt" <<'PY'
import json,sys
cfg=json.load(open(sys.argv[1]))
cfg["scenario_id"]="WP02_002_"+sys.argv[3].replace(".","p")
cfg["geometry"]["axial_cells"]=16
cfg["geometry"]["radial_cells"]=8
cfg["wetting"]["initial_saturation"]=1.0
cfg["wetting"]["initial_wet_front_m"]=cfg["coffee_bed"]["bed_depth_m"]
cfg["time"]["end_s"]=2.0
cfg["time"]["delta_t_s"]=float(sys.argv[3])
cfg["time"]["field_write_interval_s"]=2.0
cfg["machineBoundary"]["upstreamResistance"]=0.0
cfg["machineBoundary"]["supplyRampTime"]=0.0
json.dump(cfg,open(sys.argv[2],"w"),indent=2); open(sys.argv[2],"a").write("\n")
PY
  case_dir="$WP02_002_RUN_ROOT/cases/$id"
  rm -rf "$case_dir"
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP02_002_RUN_ROOT/configs/$id.json" --case-dir "$case_dir" --nprocs 1
  (
    cd "$case_dir"
    blockMesh > log.blockMesh
    checkMesh > log.checkMesh
    /usr/bin/time -v -o "$WP02_002_RUN_ROOT/timing/$id.time" \
      env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" > log.solver 2>&1
  )
done

python3 - "$WP02_002_RUN_ROOT/configs/LF-0.02.json" \
  "$WP02_002_RUN_ROOT/configs/LF-EQ.json" <<'PY'
import json,sys
cfg=json.load(open(sys.argv[1])); cfg["scenario_id"]="WP02_002_LF_EQ"
cfg["time"]["end_s"]=100.0; cfg["time"]["field_write_interval_s"]=100.0
json.dump(cfg,open(sys.argv[2],"w"),indent=2); open(sys.argv[2],"a").write("\n")
PY
case_dir="$WP02_002_RUN_ROOT/cases/LF-EQ"
rm -rf "$case_dir"
python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
  --config "$WP02_002_RUN_ROOT/configs/LF-EQ.json" --case-dir "$case_dir" --nprocs 1
(cd "$case_dir"; blockMesh > log.blockMesh; checkMesh > log.checkMesh;
 env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" > log.solver 2>&1)

python3 - "$WP02_002_RUN_ROOT/configs/LF-0.02.json" \
  "$WP02_002_RUN_ROOT/configs/TL.json" <<'PY'
import json,sys
cfg=json.load(open(sys.argv[1])); cfg["scenario_id"]="WP02_002_TL"
depth=cfg["coffee_bed"]["bed_depth_m"]
cfg["hydraulics"]["permeability_profile"]={
    "type":"axial_two_layer",
    "interface_position_m":depth/2.0,
    "upstream_permeability_m2":1.0e-15,
    "downstream_permeability_m2":3.0e-15,
}
json.dump(cfg,open(sys.argv[2],"w"),indent=2); open(sys.argv[2],"a").write("\n")
PY
case_dir="$WP02_002_RUN_ROOT/cases/TL"
rm -rf "$case_dir"
python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
  --config "$WP02_002_RUN_ROOT/configs/TL.json" --case-dir "$case_dir" --nprocs 1
(cd "$case_dir"; blockMesh > log.blockMesh; checkMesh > log.checkMesh;
 env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" > log.solver 2>&1)

index=0
for pair in "1e-10 1e-5" "1e-11 1e-4" "1e-12 1e-3"; do
  set -- $pair
  id="PL-$index"
  python3 - "$WP02_002_RUN_ROOT/configs/MC-2.json" \
    "$WP02_002_RUN_ROOT/configs/$id.json" "$1" "$2" <<'PY'
import json,sys
cfg=json.load(open(sys.argv[1]))
cfg["scenario_id"]="WP02_002_"+sys.argv[2].split("/")[-1].split(".")[0]
cfg["geometry"]["axial_cells"]=16; cfg["geometry"]["radial_cells"]=8
cfg["wetting"]["initial_saturation"]=1.0
cfg["wetting"]["initial_wet_front_m"]=cfg["coffee_bed"]["bed_depth_m"]
cfg["time"].update({"end_s":2.0,"delta_t_s":.02,"field_write_interval_s":2.0})
cfg["machineBoundary"].update({"upstreamCompliance":float(sys.argv[3]),
 "freeFlowRate":float(sys.argv[4]),"shutoffPressure":900000.0,
 "upstreamResistance":0.0,"supplyRampTime":0.0})
json.dump(cfg,open(sys.argv[2],"w"),indent=2); open(sys.argv[2],"a").write("\n")
PY
  case_dir="$WP02_002_RUN_ROOT/cases/$id"
  rm -rf "$case_dir"
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP02_002_RUN_ROOT/configs/$id.json" --case-dir "$case_dir" --nprocs 1
  (cd "$case_dir"; blockMesh > log.blockMesh; checkMesh > log.checkMesh;
   env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" > log.solver 2>&1)
  index=$((index+1))
done

if [[ "${WP02_002_FIXTURES_ONLY:-0}" == 1 ]]; then
  exit 0
fi

for id in MC-0 MC-1 MC-2 MC-3 MC-4 MC-5; do
  case_dir="$WP02_002_RUN_ROOT/cases/$id"
  rm -rf "$case_dir"
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP02_002_RUN_ROOT/configs/$id.json" --case-dir "$case_dir" \
    --nprocs "$WP02_002_NPROCS"
  (
    cd "$case_dir"
    blockMesh > log.blockMesh
    checkMesh > log.checkMesh
    decomposePar -force > log.decomposePar
    /usr/bin/time -v -o "$WP02_002_RUN_ROOT/timing/$id.time" \
      env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$WP02_002_NPROCS" \
      "$EXE" -parallel > log.solver 2>&1
  )
done

for dt in 0.02 0.01 0.005; do
  id="MC2-DT-$dt"
  python3 - "$WP02_002_RUN_ROOT/configs/MC-2.json" \
    "$WP02_002_RUN_ROOT/configs/$id.json" "$dt" <<'PY'
import json,sys
cfg=json.load(open(sys.argv[1]))
cfg["scenario_id"]="WP02_002_"+sys.argv[2].split("/")[-1].split(".json")[0].replace(".","p")
cfg["time"]["delta_t_s"]=float(sys.argv[3])
json.dump(cfg,open(sys.argv[2],"w"),indent=2); open(sys.argv[2],"a").write("\n")
PY
  case_dir="$WP02_002_RUN_ROOT/cases/$id"
  rm -rf "$case_dir"
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP02_002_RUN_ROOT/configs/$id.json" --case-dir "$case_dir" \
    --nprocs "$WP02_002_NPROCS"
  (
    cd "$case_dir"
    blockMesh > log.blockMesh
    checkMesh > log.checkMesh
    decomposePar -force > log.decomposePar
    /usr/bin/time -v -o "$WP02_002_RUN_ROOT/timing/$id.time" \
      env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$WP02_002_NPROCS" \
      "$EXE" -parallel > log.solver 2>&1
  )
done

cp "$ROOT/config/reconstruction_WP02A_waszkiewicz_9bar.json" \
  "$WP02_002_RUN_ROOT/configs/WP02-disabled.json"
case_dir="$WP02_002_RUN_ROOT/cases/WP02-disabled"
rm -rf "$case_dir"
python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
  --config "$ROOT/config/reconstruction_WP02A_waszkiewicz_9bar.json" --case-dir "$case_dir" \
  --nprocs "$WP02_002_NPROCS"
(
  cd "$case_dir"
  blockMesh > log.blockMesh
  checkMesh > log.checkMesh
  decomposePar -force > log.decomposePar
  /usr/bin/time -v -o "$WP02_002_RUN_ROOT/timing/WP02-disabled.time" \
    env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$WP02_002_NPROCS" \
    "$EXE" -parallel > log.solver 2>&1
)

python3 "$ROOT/scripts/analyze_wp02_002_machine_coupling.py" \
  --root "$ROOT" --run-root "$WP02_002_RUN_ROOT" \
  --output "$WP02_002_RUN_ROOT/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json"
