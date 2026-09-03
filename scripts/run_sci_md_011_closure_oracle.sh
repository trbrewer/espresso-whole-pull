#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:?output CSV required}
source "$ROOT/scripts/lib/openfoam_env.sh"
load_openfoam12
(cd "$ROOT/tests/fixtures/sci_md_011_closure_oracle" && wmake)
"$(command -v sciMd011ClosureOracle)" >"$OUT"
