#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:?output JSON required}
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
(cd "$ROOT/tests/fixtures/wp03_001_poroelastic" && wmake)
"$(command -v wp03001PoroelasticFixture)" "$OUT"
