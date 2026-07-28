#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

clean_one_case() {
    local case_dir="$1"
    [[ -d "$case_dir" ]] || return 0

    rm -rf \
        "$case_dir/0" \
        "$case_dir/constant/polyMesh" \
        "$case_dir"/processor* \
        "$case_dir/postProcessing" \
        "$case_dir/preflight" \
        "$case_dir"/*.foam \
        "$case_dir"/log.* \
        "$case_dir"/ESPRESSO_*.json \
        "$case_dir"/ESPRESSO_*.csv \
        "$case_dir"/RUN_ENVIRONMENT*.json \
        "$case_dir"/CASE_SCENARIO*.json \
        "$case_dir"/stage_timings*.tsv

    find "$case_dir" -mindepth 1 -maxdepth 1 -type d \
        -regextype posix-extended -regex '.*/[0-9]+([.][0-9]+)?' \
        -exec rm -rf {} + 2>/dev/null || true

    rm -f \
        "$case_dir/constant/espressoModelProperties" \
        "$case_dir/system/blockMeshDict" \
        "$case_dir/system/controlDict" \
        "$case_dir/system/decomposeParDict"
}

if (( $# > 0 )); then
    for value in "$@"; do
        if [[ "$value" = /* ]]; then
            clean_one_case "$value"
        else
            clean_one_case "$ROOT_DIR/$value"
        fi
    done
else
    clean_one_case "$ROOT_DIR/cases/reference_R0_20g_58mm_9bar"
    clean_one_case "$ROOT_DIR/cases/fixture_layered_pressure_v0_1_4"
fi
