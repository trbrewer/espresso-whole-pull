#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${WP03_001_RUN_ROOT:=/tmp/wp03-001-poroelastic-compaction}"
: "${WP03_001_NPROCS:=32}"
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
EXE=$(command -v espressoWholePullFoam)
test -x "$EXE"
(cd "$ROOT/validation/wp03" &&
  sha256sum -c WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.sha256)
mkdir -p "$WP03_001_RUN_ROOT/configs" "$WP03_001_RUN_ROOT/cases" \
  "$WP03_001_RUN_ROOT/timing"

python3 - "$ROOT" "$WP03_001_RUN_ROOT/configs" <<'PY'
import copy, csv, json, pathlib, statistics, sys
root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
base = json.loads((root/"config/reference_R0.json").read_text())
spec = json.loads((root/"validation/wp03/WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.json").read_text())
machine = json.loads((root/"validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text())["case_matrix"]["MC-2"]["machineBoundary"]
ref, controls = spec["reference"], spec["nonlinear_controls"]

def mechanics(k0, pc):
    return {
      "model": "waszkiewicz2025FinitePhi",
      "stressFreePorosity": ref["stress_free_porosity"],
      "criticalCompactionPressurePa": pc,
      "stressFreePermeabilityM2": k0,
      "nonlinearRelativeTolerance": controls["nonlinear_relative_tolerance"],
      "nonlinearAbsoluteTolerance": controls["nonlinear_absolute_tolerance"],
      "nonlinearMaximumIterations": controls["nonlinear_maximum_iterations"],
      "nonlinearUnderRelaxation": controls["nonlinear_under_relaxation"],
      "machineFluxRelativeTolerance": controls["machine_flux_relative_tolerance"]}

def make(cid):
    item, cfg = spec["case_matrix"][cid], copy.deepcopy(base)
    cfg["scenario_id"] = "WP03_001_"+cid.replace("-","_")
    cfg["pressureBoundaryModel"] = item["pressure"]
    if item["pressure"] == "lumpedMachineCompliance":
        cfg["machineBoundary"] = copy.deepcopy(machine)
    else:
        cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"] = item["target_pressure_pa"]
    cfg["bedMechanicsModel"] = item["mechanics"]
    if item["mechanics"] != "none":
        cfg["poroelasticCompaction"] = mechanics(
            item["stress_free_permeability_m2"], item["critical_pressure_pa"])
        cfg["poroelasticCompaction"]["nonlinearUnderRelaxation"] = \
            item.get("nonlinear_under_relaxation",
                     controls["nonlinear_under_relaxation"])
    cfg["governance"] = {"task":"WP03-001",
      "change_scope":"GOVERNING_PHYSICS_CHANGE",
      "evidence_role":"NUMERICAL_VERIFICATION_AND_SOURCE_LINKED_QUASISTATIC_COMPACTION_DIAGNOSTIC"}
    cfg["claim_ceiling"] = "Physical validation NOT_ESTABLISHED; source-linked and synthetic numerical diagnostic."
    return cfg

for cid in spec["case_matrix"]:
    (out/f"{cid}.json").write_text(json.dumps(make(cid),indent=2)+"\n")
for dt in (0.02,0.01,0.005):
    cfg=make("PE-7"); cfg["scenario_id"]+=f"_DT_{dt}"
    cfg["time"]["delta_t_s"]=dt
    (out/f"PE-7-DT-{dt}.json").write_text(json.dumps(cfg,indent=2)+"\n")
for nx in (128,256,512):
    cfg=make("PE-7"); cfg["scenario_id"]+=f"_NX_{nx}"
    cfg["geometry"]["axial_cells"]=nx
    (out/f"PE-7-NX-{nx}.json").write_text(json.dumps(cfg,indent=2)+"\n")

def saturated_fixture(cid, pressure, source=False):
    cfg=make("PE-3")
    cfg["scenario_id"]="WP03_001_"+cid
    cfg["hydraulics"]["target_inlet_pressure_gauge_Pa"]=pressure
    cfg["hydraulics"]["pressure_ramp_time_s"]=0
    cfg["wetting"]["initial_saturation"]=1
    cfg["wetting"]["initial_wet_front_m"]=cfg["coffee_bed"]["bed_depth_m"]
    cfg["geometry"].update({"axial_cells":8192,"radial_cells":32})
    cfg["time"].update({"end_s":0.02,"delta_t_s":0.02,"field_write_interval_s":0.02})
    if pressure > 1.0e6:
        cfg["poroelasticCompaction"]["nonlinearUnderRelaxation"] = 0.7
    if source:
        s=ref["source"]
        cfg["geometry"]["basket_radius_m"]=s["basket_radius_m"]
        cfg["geometry"]["basket_diameter_m"]=2*s["basket_radius_m"]
        cfg["coffee_bed"]["bed_depth_m"]=s["bed_depth_m"]
        cfg["liquid"]["density_kg_m3"]=s["density_kg_m3"]
        cfg["liquid"]["dynamic_viscosity_Pa_s"]=s["dynamic_viscosity_pa_s"]
        cfg["poroelasticCompaction"]["stressFreePorosity"]=s["stress_free_porosity"]
        cfg["poroelasticCompaction"]["criticalCompactionPressurePa"]=s["critical_compaction_pressure_pa"]
        cfg["poroelasticCompaction"]["stressFreePermeabilityM2"]=s["stress_free_permeability_m2"]
        cfg["wetting"]["initial_wet_front_m"]=s["bed_depth_m"]
    return cfg
for bar in (5,9,11):
    cfg=saturated_fixture(f"PROFILE-{bar}BAR",bar*1e5)
    (out/f"PROFILE-{bar}BAR.json").write_text(json.dumps(cfg,indent=2)+"\n")

source_dir=root.parent/"puckworks-pinned/puckworks/data/waszkiewicz2025"
rows=list(csv.DictReader((source_dir/"traces_time_dependent.csv").open()))
groups={}
for row in rows:
    groups.setdefault(row["reference_pressure_round__bar"],[]).append(row)
points=[]
pc=ref["source"]["critical_compaction_pressure_pa"]
for nominal, group in sorted(groups.items(),key=lambda kv:float(kv[0])):
    last=max(group,key=lambda r:float(r["time__s"]))
    p=float(last["basket_pressure__bar"])
    q=float(last["mass_flow_rate__g_per_s"])
    point={"nominal_pressure_bar":float(nominal),"basket_pressure_bar":p,
           "measured_mass_flow_g_s":q,
           "domain_status":"IN_DOMAIN" if p*1e5 < pc else "OUTSIDE_LOCAL_CONSTITUTIVE_DOMAIN"}
    points.append(point)
    if point["domain_status"]=="IN_DOMAIN":
        cid=f"SRC-{len(points)-1:02d}"
        cfg=saturated_fixture(cid,p*1e5,True)
        (out/f"{cid}.json").write_text(json.dumps(cfg,indent=2)+"\n")
(out/"SOURCE_POINTS.json").write_text(json.dumps(points,indent=2)+"\n")
PY

run_case() {
  local cid=$1 ranks=$2
  local case_dir="$WP03_001_RUN_ROOT/cases/$cid"
  test ! -e "$case_dir" || { echo "Refusing to overwrite $case_dir" >&2; return 2; }
  python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
    --config "$WP03_001_RUN_ROOT/configs/$cid.json" --case-dir "$case_dir" --nprocs "$ranks"
  (
    cd "$case_dir"
    blockMesh >log.blockMesh
    checkMesh >log.checkMesh
    if ((ranks>1)); then
      decomposePar -force >log.decomposePar
      /usr/bin/time -v -o "$WP03_001_RUN_ROOT/timing/$cid.time" \
        env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$ranks" "$EXE" -parallel >log.solver 2>&1
    else
      /usr/bin/time -v -o "$WP03_001_RUN_ROOT/timing/$cid.time" \
        env ESPRESSO_CASE_ROOT="$case_dir" "$EXE" >log.solver 2>&1
    fi
  )
}

for cid in PROFILE-{5,9,11}BAR; do run_case "$cid" 1; done
while IFS= read -r cfg; do
  cid=$(basename "$cfg" .json)
  run_case "$cid" 1
done < <(find "$WP03_001_RUN_ROOT/configs" -maxdepth 1 -name 'SRC-*.json' | sort)
scripts/run_wp03_001_production_fixture.sh \
  "$WP03_001_RUN_ROOT/WP03_001_PRODUCTION_FIXTURE.json"
if [[ ${WP03_001_FIXTURES_ONLY:-0} == 1 ]]; then exit 0; fi
for cid in PE-{0..7}; do run_case "$cid" "$WP03_001_NPROCS"; done
for dt in 0.02 0.01 0.005; do run_case "PE-7-DT-$dt" "$WP03_001_NPROCS"; done
for nx in 128 256 512; do run_case "PE-7-NX-$nx" "$WP03_001_NPROCS"; done
WP02_004_RUN_ROOT="$WP03_001_RUN_ROOT/predecessor-wp02-004" \
  WP02_004_FIXTURES_ONLY=1 \
  "$ROOT/scripts/run_wp02_004_radial_heterogeneity.sh"
python3 "$ROOT/scripts/verify_wp02_regression.py" --root "$ROOT" \
  --results "$ROOT/validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json" \
  >"$WP03_001_RUN_ROOT/WP02_COUPLING_DISABLED_REGRESSION.json"
python3 "$ROOT/scripts/analyze_wp03_001_poroelastic_compaction.py" \
  --root "$ROOT" --run-root "$WP03_001_RUN_ROOT" --executable "$EXE" \
  --output "$WP03_001_RUN_ROOT/WP03_001_POROELASTIC_COMPACTION_RESULTS.json" \
  --trace-output "$WP03_001_RUN_ROOT/WP03_001_POROELASTIC_COMPACTION_TRACE.csv" \
  --source-output "$WP03_001_RUN_ROOT/WP03_001_SOURCE_PRESSURE_SWEEP.csv"
