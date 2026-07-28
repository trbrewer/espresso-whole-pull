# OpenFOAM Foundation 12 compatibility — v0.1.4

## Frozen target

The package requires:

```text
WM_PROJECT=OpenFOAM
WM_PROJECT_VERSION=12
```

It is not claimed compatible with OpenCFD/OpenFOAM.com releases, foam-extend, or another Foundation version.

## Environment loading

`scripts/lib/openfoam_env.sh` searches standard Foundation locations and accepts an explicit `OPENFOAM_BASHRC`. It temporarily relaxes Bash `nounset` while sourcing the Foundation environment and immediately restores the caller’s setting.

For shell-level source paths, the package uses:

```bash
FOAM_SOURCE_ROOT="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"
```

It does not assume that `LIB_SRC` is exported to Bash. `$(LIB_SRC)` remains valid only inside `Make/options`, where it belongs to the `wmake` context.

## Explicit solver headers

The custom solver uses explicit Foundation-12 interfaces rather than the obsolete `fvCFD.H` umbrella header. `Allwmake` verifies all required headers in the active `lnInclude` directories before compilation.

## Build workflow

`Allwmake`:

1. validates `WM_PROJECT`, `WM_PROJECT_VERSION`, `WM_PROJECT_DIR`, `FOAM_SRC`, and `FOAM_USER_APPBIN`;
2. checks the required Foundation headers;
3. normalizes future-dated solver and Make inputs;
4. runs `wclean` then `wmake`;
5. confirms that the user executable exists and is executable;
6. records build-input hashes, executable size/hash, and Foundation build environment.

## Exact executable used for qualification

Standard `./Allverify` does not rebuild. It invokes `verify_build_provenance.py`, which checks:

- every build input against `BUILD_PROVENANCE_V0_1_4.json`;
- exact executable bytes and SHA-256;
- executable permission;
- `WM_PROJECT`, `WM_PROJECT_VERSION`, and `WM_OPTIONS` identity.

Both standard and smoke profiles run the exact absolute executable path recorded by `./Allrun`; neither profile resolves the solver by name through `PATH`. Smoke mode remains nonqualifying and cannot finalize or overwrite the standard freeze record.

## Output settings

Generated `controlDict` files request:

```text
writeFormat      binary;
writeCompression off;
```

This avoids Foundation 12’s ineffective compressed-binary warning.

## MPI

Parallel reference execution uses `mpirun` or `mpiexec`. The routine R0 default is 32 ranks; the standard matrix also exercises 1, 16, and 64 ranks. OpenFOAM decomposition uses `scotch`.

## Floating-point exception trapping

Foundation’s `FOAM_SIGFPE` enablement line is recorded as an informational safeguard. An actual floating-point exception remains a hard diagnostic issue.
