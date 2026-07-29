#!/usr/bin/env bash
set -euo pipefail
: "${WP02_ROOT:?}"; : "${WP02_EXECUTABLE:?}"; : "${WP02_FIXTURE_CASE_ROOT:?}"; : "${WP02_FIXTURE_RESULT:?}"
test -x "$WP02_EXECUTABLE"
python3 "$WP02_ROOT/scripts/wp02_contract_bridge.py" --root "$WP02_ROOT" --check
python3 "$WP02_ROOT/scripts/prepare_case.py" --root "$WP02_ROOT" --config "$WP02_ROOT/config/fixture_WP02_001_uniform_pressure.json" --case-dir "$WP02_FIXTURE_CASE_ROOT" --nprocs 1
(
 cd "$WP02_FIXTURE_CASE_ROOT"
 blockMesh
 checkMesh
 ESPRESSO_CASE_ROOT="$WP02_FIXTURE_CASE_ROOT" "$WP02_EXECUTABLE"
)
python3 "$WP02_ROOT/scripts/verify_wp02_uniform_fixture.py" --root "$WP02_ROOT" --case "$WP02_FIXTURE_CASE_ROOT" --executable "$WP02_EXECUTABLE" --output "$WP02_FIXTURE_RESULT"
