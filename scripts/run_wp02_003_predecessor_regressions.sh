#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${WP02_003_REGRESSION_ROOT:=/tmp/wp02-003-predecessor-regressions}"
: "${WP02_003_NPROCS:=32}"
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
EXE=$(command -v espressoWholePullFoam)
test -x "$EXE"
mkdir -p "$WP02_003_REGRESSION_ROOT/configs" \
  "$WP02_003_REGRESSION_ROOT/cases" "$WP02_003_REGRESSION_ROOT/timing"

python3 - "$ROOT" "$WP02_003_REGRESSION_ROOT/configs/MC-5-DARCY.json" <<'PY'
import copy, json, pathlib, sys
root, output = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
cfg = json.loads((root / "config/reference_R0.json").read_text())
machine = json.loads(
    (root / "validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json").read_text()
)["case_matrix"]["MC-2"]["machineBoundary"]
wp02 = json.loads(
    (root / "config/reconstruction_WP02A_waszkiewicz_9bar.json").read_text()
)
cfg["scenario_id"] = "WP02_003_REGRESSION_MC_5_DARCY"
cfg["pressureBoundaryModel"] = "lumpedMachineCompliance"
cfg["machineBoundary"] = copy.deepcopy(machine)
cfg["flowResistanceModel"] = "darcy"
cfg["effective_permeability_evolution"] = copy.deepcopy(
    wp02["effective_permeability_evolution"]
)
cfg["governance"] = {
    "task": "WP02-003",
    "change_scope": "GOVERNING_PHYSICS_CHANGE",
    "evidence_role": "PREDECESSOR_REGRESSION_CONTROL",
}
cfg["claim_ceiling"] = (
    "WP02-002 MC-5 Darcy regression control; physical validation NOT_ESTABLISHED."
)
output.write_text(json.dumps(cfg, indent=2) + "\n")
PY

case_dir="$WP02_003_REGRESSION_ROOT/cases/MC-5-DARCY"
if [[ -e "$case_dir" ]]; then
  echo "Refusing to overwrite governed regression run: $case_dir" >&2
  exit 2
fi
python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
  --config "$WP02_003_REGRESSION_ROOT/configs/MC-5-DARCY.json" \
  --case-dir "$case_dir" --nprocs "$WP02_003_NPROCS"
(
  cd "$case_dir"
  blockMesh > log.blockMesh
  checkMesh > log.checkMesh
  decomposePar -force > log.decomposePar
  /usr/bin/time -v -o "$WP02_003_REGRESSION_ROOT/timing/MC-5-DARCY.time" \
    env ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$WP02_003_NPROCS" \
    "$EXE" -parallel > log.solver 2>&1
)

PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/verify_wp02_regression.py" \
  --root "$ROOT" \
  --results "$ROOT/validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json" \
  > "$WP02_003_REGRESSION_ROOT/WP02_COUPLING_DISABLED_REGRESSION.json"
