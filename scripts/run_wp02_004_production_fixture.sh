#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUTPUT=${1:-/tmp/WP02_004_PRODUCTION_FIXTURE.json}
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
wmake "$ROOT/tests/fixtures/wp02_004_radial"
"$(command -v wp02004RadialFixture)" "$OUTPUT"
python3 -m json.tool "$OUTPUT" >/dev/null
