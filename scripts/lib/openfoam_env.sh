#!/usr/bin/env bash
# This file is sourced by Allrun/Allwmake/Allclean.

_openfoam12_normalize_environment() {
    if [[ -z "${WM_PROJECT_DIR:-}" || ! -d "${WM_PROJECT_DIR:-}" ]]; then
        return 1
    fi

    # Foundation 12 exports FOAM_SRC from etc/config.sh/settings.  Keep a
    # conservative fallback for already-sourced/minimal environments while
    # avoiding the wmake-only LIB_SRC make variable in shell code.
    export FOAM_SRC="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"

    if [[ ! -d "$FOAM_SRC" || -z "${FOAM_USER_APPBIN:-}" ]]; then
        return 1
    fi

    return 0
}

_openfoam12_environment_ready() {
    command -v wmake >/dev/null 2>&1 \
        && [[ "${WM_PROJECT:-}" == "OpenFOAM" ]] \
        && [[ "${WM_PROJECT_VERSION:-}" == "12" ]] \
        && _openfoam12_normalize_environment
}

load_openfoam12() {
    local optional=0
    if [[ "${1:-}" == "--optional" ]]; then
        optional=1
    fi

    if _openfoam12_environment_ready; then
        return 0
    fi

    local candidates=()
    if [[ -n "${OPENFOAM_BASHRC:-}" ]]; then
        candidates+=("$OPENFOAM_BASHRC")
    fi
    candidates+=(
        "/opt/openfoam12/etc/bashrc"
        "/usr/lib/openfoam/openfoam12/etc/bashrc"
    )
    if [[ -n "${HOME:-}" ]]; then
        candidates+=(
            "$HOME/OpenFOAM/OpenFOAM-12/etc/bashrc"
            "$HOME/OpenFOAM/OpenFOAM-v12/etc/bashrc"
        )
    fi

    local candidate
    local source_status=1
    local nounset_was_enabled=0
    case "$-" in
        *u*) nounset_was_enabled=1 ;;
    esac

    for candidate in "${candidates[@]}"; do
        if [[ -f "$candidate" ]]; then
            # Foundation bashrc is intended to be sourced, but it predates
            # nounset-safe shell conventions.  Disable nounset only during the
            # source operation and restore the caller's setting immediately.
            if (( nounset_was_enabled == 1 )); then
                set +u
            fi
            # shellcheck disable=SC1090
            if source "$candidate"; then
                source_status=0
            else
                source_status=$?
            fi
            if (( nounset_was_enabled == 1 )); then
                set -u
            fi

            if (( source_status == 0 )) && _openfoam12_environment_ready; then
                return 0
            fi
        fi
    done

    if (( optional == 1 )); then
        return 1
    fi

    cat >&2 <<'EOF_MESSAGE'
OpenFOAM Foundation 12 was not detected as a complete build environment.

Source the Foundation v12 environment before running, for example:
    source /opt/openfoam12/etc/bashrc

Or point this package at the installation explicitly:
    export OPENFOAM_BASHRC=/path/to/OpenFOAM-12/etc/bashrc
    ./Allrun

The environment must provide WM_PROJECT=OpenFOAM, WM_PROJECT_VERSION=12,
WM_PROJECT_DIR, FOAM_SRC (or a conventional WM_PROJECT_DIR/src tree),
FOAM_USER_APPBIN, and wmake.  OpenCFD/OpenFOAM.com editions and non-v12
Foundation installations are intentionally outside the frozen target.
EOF_MESSAGE
    return 2
}
