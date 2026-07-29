#!/usr/bin/env bash
set -euo pipefail

: "${WP02_ROOT:?set WP02_ROOT}"
: "${WP02_EXECUTABLE:?set WP02_EXECUTABLE}"
: "${WP02_CASE_ROOT:?set WP02_CASE_ROOT}"
: "${NPROCS:=32}"

run_case() {
    scenario="$1"
    case_dir="$2"
    test ! -e "$case_dir"
    python3 "$WP02_ROOT/scripts/prepare_case.py" --root "$WP02_ROOT" \
        --config "$scenario" --case-dir "$case_dir" --nprocs "$NPROCS"
    (
        cd "$case_dir"
        blockMesh
        checkMesh
        decomposePar -force
        ESPRESSO_CASE_ROOT="$case_dir" mpirun -np "$NPROCS" \
            "$WP02_EXECUTABLE" -parallel
        reconstructPar -latestTime
    )
}

run_case "$WP02_ROOT/config/reconstruction_WP02A_waszkiewicz_9bar.json" \
    "$WP02_CASE_ROOT/9bar"
run_case "$WP02_ROOT/config/reconstruction_WP02A_waszkiewicz_8bar.json" \
    "$WP02_CASE_ROOT/8bar"
