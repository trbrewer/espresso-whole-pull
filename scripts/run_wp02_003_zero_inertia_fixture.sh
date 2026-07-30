#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${WP02_003_ZERO_INERTIA_OUTPUT:=${1:-/tmp/WP02_003_ZERO_INERTIA_FIXTURE.json}}"
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
wmake "$ROOT/tests/fixtures/wp02_003_zero_inertia"
EXE=$(command -v wp02003ZeroInertiaFixture)
test -x "$EXE"
"$EXE" "$WP02_003_ZERO_INERTIA_OUTPUT"
python3 -m json.tool "$WP02_003_ZERO_INERTIA_OUTPUT" >/dev/null
