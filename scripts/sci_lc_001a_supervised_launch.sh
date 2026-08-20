#!/usr/bin/env bash
set -euo pipefail

: "${SCI_LC_CONTROL_ROOT:?required}"
: "${SCI_LC_CONTROL_AUTHORITY:?required}"
: "${SCI_LC_EXECUTION_AUTHORITY:?required}"
: "${SCI_LC_OUTPUT_ROOT:?required}"
: "${SCI_LC_DIAGNOSTICS_CONFIG:?required}"
: "${SCI_LC_LOG_ROOT:?required}"

[[ -d "$SCI_LC_LOG_ROOT" ]] || { echo "SCI_LC_LOG_ROOT must pre-exist" >&2; exit 64; }
exec >>"$SCI_LC_LOG_ROOT/controller.stdout.log" 2>>"$SCI_LC_LOG_ROOT/controller.stderr.log"

controller="$(dirname "$0")/sci_lc_001a_family_controller.py"
executor="$(dirname "$0")/sci_lc_001a_executor.py"
terminalized=0

terminalize() {
  local exit_code=$?
  if [[ "$terminalized" -eq 0 ]]; then
    terminalized=1
    python3 "$controller" --control-root "$SCI_LC_CONTROL_ROOT" --mode transition --authority "$SCI_LC_CONTROL_AUTHORITY" --target FINALIZING --cause "WRAPPER_EXIT_${exit_code}" || true
    if [[ "$exit_code" -eq 0 ]]; then
      python3 "$controller" --control-root "$SCI_LC_CONTROL_ROOT" --mode transition --authority "$SCI_LC_CONTROL_AUTHORITY" --target COMPLETE --cause NORMAL_COMPLETION || true
    else
      python3 "$controller" --control-root "$SCI_LC_CONTROL_ROOT" --mode transition --authority "$SCI_LC_CONTROL_AUTHORITY" --target FAILED --cause "WRAPPER_EXIT_${exit_code}" || true
    fi
  fi
  exit "$exit_code"
}
trap terminalize EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python3 "$controller" --control-root "$SCI_LC_CONTROL_ROOT" --mode transition --authority "$SCI_LC_CONTROL_AUTHORITY" --target STARTING --cause SUPERVISED_WRAPPER_START
python3 "$controller" --control-root "$SCI_LC_CONTROL_ROOT" --mode transition --authority "$SCI_LC_CONTROL_AUTHORITY" --target RUNNING --cause EXECUTOR_START
python3 "$executor" --mode execute --execution-authority "$SCI_LC_EXECUTION_AUTHORITY" \
  --output-root "$SCI_LC_OUTPUT_ROOT" --family-control-root "$SCI_LC_CONTROL_ROOT" \
  --multiplier-diagnostics-config "$SCI_LC_DIAGNOSTICS_CONFIG"
