# WP-0.1F freeze-finalization specification — v0.1.4

## Purpose

Version 0.1.4 is a no-governing-physics-change release that turns the successful v0.1.3 numerical qualification into a reproducible, internally consistent, immutable reference record.

The release is complete only after a clean package executes:

```bash
./Allrun
./Allverify
```

and the terminal freeze manifest passes its read-only verification.

## Governing no-physics-change rule

A release is eligible for finalization only when `verify_no_physics_change.py` passes all comparisons against the bundled target-qualified v0.1.3 source contract.

The comparison covers:

- normalized OpenFOAM solver source, allowing only package-version labels;
- normalized independent reduced-twin mathematics, allowing only artifact-version labels;
- physics projections of the R0 and layered-fixture configurations;
- exact `Make/files` and `Make/options` identity;
- exact initial field templates for both cases;
- exact `fvSchemes` and `fvSolution` identity for both cases.

The routine MPI default, reporting schemas, diagnostics, tests, orchestration, documentation, and provenance machinery are release-engineering concerns and may change without altering the governing model.

## Required execution states

### After `./Allrun`

The reference acceptance must report:

```text
status:                                PASS
all_required_reference_gates_pass:     true
reference_qualification_status:        PENDING_STANDARD_ALLVERIFY
release_provenance_status:             PENDING_TERMINAL_FREEZE_MANIFEST
reference_freeze_status:               NOT_FROZEN
```

The run status must report a completed PASS reference execution. The exact executable, source/build inputs, OpenFOAM build environment, and timestamp normalization record must be present under the reference `preflight/` directory.

### After the standard qualification matrix

The standard qualification report must record:

```text
profile:                    standard
status:                     PASS
all_required_gates_pass:    true
gate_summary:               9 PASS / 0 FAIL / 9 total
matrix run count:           10
```

Every matrix run must have a PASS acceptance report whose recorded SHA-256 matches the file on disk.

### After finalization

The finalizer must update the mutable acceptance and run-status records before the terminal manifest is generated. The acceptance becomes:

```text
reference_qualification_status:     PASS
reference_freeze_status:            QUALIFIED
all_required_freeze_prerequisites:  PASS
```

The run status becomes:

```text
reference_qualification_status: PASS
reference_freeze_status:        QUALIFIED_PENDING_TERMINAL_MANIFEST
```

The finalization-status artifact records the hashes of the exact qualified acceptance, finalized run status, and standard qualification report.

### Terminal manifest

`generate_freeze_manifest.py` is invoked only after every mutable controlling record is final. It binds:

- source-package manifest and controlling strategy;
- exact reference build provenance and read-back verification;
- timestamp-normalization report;
- pre- and post-qualification no-physics-change reports;
- executed scenario and run environment;
- immutable scientific-input manifest;
- reference stage timings and finalized run status;
- qualified reference acceptance and trace;
- reference field index and every indexed field file;
- ParaView entry point;
- layered-pressure fixture acceptance;
- standard qualification JSON and reduced CSV;
- every qualification-run acceptance report;
- freeze-finalization status.

It is generated last and does not embed a self-hash. No artifact hashed by it depends on the terminal-manifest hash.

## Acyclic provenance contract

```text
source package
   ├── controlling strategy
   ├── solver source and Make contract
   └── case templates/configuration
                ↓
scientific-input manifest
                ↓
exact compiled executable and build provenance
                ↓
reference/fixture outputs and field index
                ↓
reference acceptance
                ↓
qualification matrix and per-run acceptance reports
                ↓
qualified acceptance + finalized run status
                ↓
terminal freeze manifest
```

The scientific-input manifest may not contain an `outputs` key. The acceptance report may hash immutable result artifacts but does not hash the terminal manifest. The terminal manifest is the sole top-level release binding.

## Explicit v0.1.4 state gates

In addition to the v0.1.3 numerical and B0 gates, reference acceptance requires:

- maximum dissolved concentration no greater than the declared saturation concentration plus tolerance;
- remaining extractable inventory between zero and its initial inventory plus tolerance;
- retained water no greater than saturated pore-water capacity plus tolerance;
- cumulative inlet-water mass nondecreasing;
- cumulative cup-water mass nondecreasing;
- cumulative cup-solute mass nondecreasing.

These are acceptance/reporting gates over unchanged v0.1.3 physics.

## Exact-build reuse contract

`./Allrun` produces `BUILD_PROVENANCE_V0_1_4.json`. Standard `./Allverify` verifies:

- every recorded build-input hash;
- exact runtime executable byte size and SHA-256;
- portable archived executable byte size and SHA-256;
- runtime/archive byte identity;
- executable permission;
- `WM_PROJECT`, `WM_PROJECT_VERSION`, and `WM_OPTIONS` consistency.

Standard qualification then uses that same runtime executable. It does not invoke `Allwmake`. Smoke mode also reuses the same executable but writes only profile-isolated, nonqualifying reports. `./Allrun` stores a byte-identical portable copy under the reference preflight directory, and the terminal manifest binds that archived copy independently of the external OpenFOAM user-application path.

## Diagnostic contract

The exact OpenFOAM line:

```text
sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).
```

is informational. A numeric metric such as:

```text
Mesh-volume relative error: 5.69e-15
```

is also informational. An actual floating-point exception, `FOAM FATAL`, compiler failure, MPI abort, segmentation fault, missing file, shell expansion error, or explicit failed stage remains a detected issue.

## Freeze decision

The terminal manifest may report `FROZEN / QUALIFIED` only when all of the following are true:

- reference execution PASS;
- all reference numerical, B0, bounded-state, and monotonicity gates PASS;
- heterogeneous pressure fixture PASS;
- standard ten-run qualification PASS with 9/9 aggregate gates;
- source-package and scientific-input verification PASS;
- exact-build verification PASS;
- pre- and post-qualification no-physics-change verification PASS;
- reference artifacts and every indexed field file verify;
- every qualification acceptance hash verifies;
- finalization cross-links verify;
- physical validation remains explicitly `NOT_ESTABLISHED`.

## Next milestone

A successful freeze closes WP-0.1F and records WP-0.1H as `FROZEN / QUALIFIED`. The next scientific milestone is WP-0.1R: the distinct 18.5 g, 58 mm, 9 bar Waszkiewicz-linked reconstruction, followed by formal Puckworks registration.
