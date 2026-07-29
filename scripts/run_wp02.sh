#!/usr/bin/env bash
set -euo pipefail

: "${WP02_ROOT:?set WP02_ROOT}"
: "${WP02_EXECUTABLE:?set WP02_EXECUTABLE}"
: "${WP02_CASE_ROOT:?set WP02_CASE_ROOT}"
: "${WP02_UNIFORM_FIXTURE_RESULT:?set WP02_UNIFORM_FIXTURE_RESULT}"
: "${NPROCS:=32}"

python3 - "$WP02_UNIFORM_FIXTURE_RESULT" "$WP02_EXECUTABLE" <<'PY'
import hashlib, json, pathlib, sys
result=json.load(open(sys.argv[1]))
exe=hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest()
assert result["fixture_status"]=="PASS"
assert result["execution"]["case_execution_count"]==1
assert result["execution"]["executable_sha256"]==exe
assert result["physical_validation"]=="NOT_APPLICABLE"
PY
echo "Uniform fixture PASS. R0 and constant-R1 regressions remain mandatory external release gates."

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
