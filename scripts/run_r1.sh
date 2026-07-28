#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${R1_CASE:?set R1_CASE to a fresh external directory}"
: "${PUCKWORKS_CHECKOUT:?set PUCKWORKS_CHECKOUT to a fresh external directory}"
NPROCS="${NPROCS:-32}"
[[ "$NPROCS" == 32 ]] || { echo "WP01R-005 requires 32 ranks" >&2; exit 2; }
python3 "$ROOT/scripts/r1_contract_bridge.py" --root "$ROOT" \
  --output "$ROOT/config/reconstruction_R1_waszkiewicz_9bar.json" --check
python3 "$ROOT/scripts/prepare_case.py" --root "$ROOT" \
  --config "$ROOT/config/reconstruction_R1_waszkiewicz_9bar.json" \
  --case-dir "$R1_CASE" --nprocs 32
cd "$R1_CASE"
blockMesh
checkMesh -allGeometry -allTopology
decomposePar -force
ESPRESSO_CASE_ROOT="$R1_CASE" mpirun -np 32 \
  "${SOLVER_EXECUTABLE:?set exact SOLVER_EXECUTABLE}" -parallel
reconstructPar -latestTime
