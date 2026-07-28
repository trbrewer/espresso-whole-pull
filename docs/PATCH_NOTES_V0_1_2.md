# Patch notes — v0.1.2

## Target feedback addressed

The v0.1.1 target run successfully detected OpenFOAM Foundation 12 and completed
all static/package tests, then failed before invoking `wmake`:

```text
Allwmake: line 10: LIB_SRC: unbound variable
```

The Foundation environment was otherwise valid. The diagnostic showed
`WM_PROJECT=OpenFOAM`, `WM_PROJECT_VERSION=12`, a valid `WM_PROJECT_DIR`, and a
valid user application directory. This is therefore a package shell-portability
defect, not evidence of an OpenFOAM installation problem.

## Root cause

OpenFOAM Foundation 12 exports `FOAM_SRC=$WM_PROJECT_DIR/src` for shell use.
Its `Make/options` files commonly use `$(LIB_SRC)`, but that name belongs to the
wmake/make context and is not guaranteed to be exported as a shell variable.
The v0.1.1 `Allwmake` script incorrectly dereferenced `$LIB_SRC` while running
with `set -u`.

## Corrections

- `Allwmake` now uses:

  ```bash
  FOAM_SOURCE_ROOT="${FOAM_SRC:-${WM_PROJECT_DIR}/src}"
  ```

- all shell-level dependencies on `LIB_SRC` have been removed;
- `load_openfoam12` validates and normalizes `FOAM_SRC`;
- sourcing the Foundation bashrc is nounset-safe;
- the run-status JSON now records `FOAM_SRC`;
- shell errors including `unbound variable`, `parameter not set`, `bad
  substitution`, and `command not found` are automatically extracted;
- a unit/integration test exercises `Allwmake` with both `FOAM_SRC` and
  `LIB_SRC` initially absent and a mocked Foundation-12 source tree;
- the package, solver, run-status, static-validation, and source-manifest
  versions are incremented to 0.1.2.

## Unchanged scientific scope

No governing equation, material parameter, geometry, mesh, time step,
calibration declaration, numerical gate, or scientific claim ceiling was
changed. The detailed scientific acceptance artifacts retain their `V0_1`
schema names.

## Runtime boundary

The packaging environment does not contain OpenFOAM Foundation 12. Version
0.1.2 has therefore not been represented as compiled or simulated here. The
next target-machine run remains the controlling test. Share:

```text
cases/reference_R0_20g_58mm_9bar/
ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_2.json
```
