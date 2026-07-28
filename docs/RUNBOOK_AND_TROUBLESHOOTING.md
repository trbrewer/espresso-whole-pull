# Runbook and troubleshooting — v0.1.4

## Clean installation

```bash
unzip espresso_puck_whole_pull_reference_v0_1_4_openfoam12.zip
cd espresso_puck_whole_pull_reference_v0_1_4_openfoam12
```

Do not overlay v0.1.4 on a prior package directory. A fresh extraction keeps the source manifest and permissions unambiguous.

## Reference run

```bash
./Allrun
```

The routine default is 32 MPI ranks. Explicit selection remains available:

```bash
NPROCS=32 ./Allrun
```

A nonstandard Foundation environment can be selected with:

```bash
OPENFOAM_BASHRC="$HOME/OpenFOAM/OpenFOAM-12/etc/bashrc" ./Allrun
```

### Reference workflow order

```text
Foundation-12 environment
source-manifest verification
static package validation
no-physics-change verification
unit/integration tests
timestamp normalization and clean build
layered fixture: prepare → mesh → check → solve → acceptance
reference: prepare → mesh → check → decompose → solve → reconstruct
reference postprocessing and acceptance
run-status and stage-timing reports
```

Every long-running stage is displayed live and retained in a `log.*` file.

### Successful reference completion

A successful terminal message identifies:

```text
ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json
ESPRESSO_WHOLE_PULL_REFERENCE_ACCEPTANCE_V0_1_4.json
ESPRESSO_WHOLE_PULL_STAGE_TIMINGS_V0_1_4.json
ESPRESSO_LAYERED_PRESSURE_FIXTURE_ACCEPTANCE_V0_1_4.json
reference_R0.foam
```

The reference is still `NOT_FROZEN` at this point.

## Standard qualification and freeze

Run only after `./Allrun` passes:

```bash
./Allverify
```

Standard `./Allverify` checks that the exact reference runtime executable, its byte-identical portable archive, and build inputs are unchanged; executes the full ten-run matrix; repeats the no-physics-change comparison; finalizes acceptance/run status; generates the terminal freeze manifest; and verifies it read-only.

Successful completion identifies:

```text
qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json
qualification/ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_RUNS_V0_1_4.csv
qualification/ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json
cases/reference_R0_20g_58mm_9bar/ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json
```

The final manifest is the controlling release artifact.

## Smoke workflow

```bash
PROFILE=smoke ./Allverify
```

Smoke mode verifies orchestration only. It cannot finalize or overwrite a standard freeze.

## Monitoring

The terminal receives live stage output. Additional monitoring commands include:

```bash
pgrep -af 'wmake|g\+\+|cc1plus|espressoWholePullFoam|mpirun|reconstructPar'
```

```bash
tail -f cases/reference_R0_20g_58mm_9bar/log.espressoWholePullFoam
```

```bash
tail -f qualification/log.qualification.standard
```

## Single diagnostic file

On any controlled `./Allrun` failure, send:

```text
cases/reference_R0_20g_58mm_9bar/
  ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_4.json
```

On qualification/finalization failure, also send:

```text
qualification/
  ESPRESSO_WHOLE_PULL_NUMERICAL_QUALIFICATION_V0_1_4.json
  ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json
```

The run-status JSON contains the failed stage, exit code, command, selected Foundation environment, stage timings, artifact presence, log hashes/tails, and classified issue lines.

## Common failures

### Wrong OpenFOAM distribution or version

The package requires Foundation 12:

```text
WM_PROJECT=OpenFOAM
WM_PROJECT_VERSION=12
```

Select the correct `etc/bashrc` with `OPENFOAM_BASHRC`.

### Future-dated files

`Allwmake` automatically detects and normalizes future-dated solver and Make inputs before dependency generation. The timestamp report is written under reference `preflight/`.

### Source-manifest failure

A source-manifest failure means a source-controlled file is missing, modified, has the wrong executable mode, or an unmanifested source file was added. Re-extract the original ZIP in a clean directory rather than editing the package in place.

### No-physics-change failure

A failure means the current solver, reduced mathematics, physical configuration, Make contract, initial fields, or discretization dictionaries no longer match qualified v0.1.3 within the explicitly allowed version-label normalization. Do not bypass this gate for the v0.1.4 release.

### Build-provenance failure in `./Allverify`

Standard qualification requires the exact executable produced by `./Allrun`, plus its byte-identical archived copy under the reference preflight directory. Rebuilding, replacing, stripping, or deleting either copy between the two commands causes a controlled failure. Run `./Allrun` again, then `./Allverify` without rebuilding the solver separately.

### MPI launch failure

The launcher defaults to `mpirun`, then `mpiexec`. Override where required:

```bash
MPI_LAUNCHER=/path/to/mpirun MPI_ARGS="..." ./Allrun
```

Oversubscription is blocked unless explicitly enabled:

```bash
ALLOW_OVERSUBSCRIBE=1 MPI_ARGS="--oversubscribe" NPROCS=64 ./Allrun
```

### Reconstruction requirement

Parallel reference acceptance requires reconstructed fields. `RECONSTRUCT=none` is therefore rejected for `NPROCS>1`.

### Informational `FOAM_SIGFPE`

This line is not a failure:

```text
sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).
```

An actual floating-point exception is still reported as an issue.

### Numeric “relative error” line

A successful metric such as:

```text
Mesh-volume relative error: 5.69e-15
```

is informational and no longer enters the issue count.

## Re-running

A new `./Allrun` deliberately invalidates and removes prior qualification/freeze products. Complete a new standard `./Allverify` to create a new terminal binding.

Standard `./Allverify` can be replayed after a successful reference run; it removes its own prior matrix/finalization outputs and re-verifies the reference executable before proceeding.

## Cleaning

Copy all desired reports and fields first, then run:

```bash
./Allclean
```

Cleaning removes runtime results, qualification directories, logs, reports, preflight records, and local solver build products. It retains source and bundled historical evidence.
