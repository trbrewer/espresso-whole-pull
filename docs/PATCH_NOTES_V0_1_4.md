# Patch notes — v0.1.4 freeze finalization

## Release role

Version 0.1.4 is a no-governing-physics-change finalization release. It does not alter the v0.1.3 equations, physical parameters, calibrated permeability, wetting model, extraction closure, mesh discretization, initial fields, or finite-volume schemes.

## Qualified predecessor

The bundled v0.1.3 evidence records:

- successful OpenFOAM Foundation 12 reference execution;
- exact analytical wedge, first-drip, and Darcy checks;
- heterogeneous two-layer pressure verification;
- OpenFOAM/B0 parity;
- ten qualification runs;
- all nine aggregate time-step, mesh, rank, and fixture-equivalence gates passing.

## Problems corrected

### Circular/stale artifact hashes

The v0.1.3 case manifest and acceptance lifecycle allowed a downstream report to be rewritten after another artifact had recorded its hash. Version 0.1.4 separates:

- immutable scientific-input manifest;
- mutable prequalification acceptance;
- finalized postqualification acceptance and run status;
- terminal freeze manifest generated last.

The terminal record is acyclic and no hashed artifact depends on its hash.

### Stale pre-qualification acceptance state

Standard `./Allverify` now automatically finalizes acceptance and run status after the full matrix passes, binding the qualification path, SHA-256, status, gate summary, and completion timestamp.

### Executable provenance gap

`./Allrun` now invokes the newly built solver by its recorded absolute `FOAM_USER_APPBIN` path, preventing a same-named executable earlier in `PATH` from being used accidentally. Standard qualification verifies and reuses those exact executable bytes and the same absolute path; it does not rebuild a potentially different binary before the matrix. `./Allrun` additionally archives a byte-identical portable copy inside the case preflight directory, and the terminal freeze manifest binds both the matrix-executable identity and that portable copy.

### Diagnostic false positive

Successful numeric `relative error:` metric lines are classified as informational, while actual numerical, compiler, shell, OpenFOAM, and MPI failures remain issues.

### Implicit state bounds

Reference acceptance now explicitly gates concentration capacity, remaining extractable inventory, retained-water capacity, and monotonic cumulative inlet/cup inventories.

### Routine rank choice

The R0 default changes from 64 to 32 MPI ranks because 32 was the fastest tested configuration for the qualified 131,072-cell reference mesh. Rank override remains supported, and the full qualification matrix still compares 1, 16, 32, and 64 ranks.

### Replay hygiene

All qualification products are treated as runtime files and excluded from the source manifest. A fresh `./Allrun` removes prior qualification/freeze products, ensuring that a new reference run begins an unambiguously unfrozen evidence chain.

## New principal artifacts

```text
cases/reference_R0_20g_58mm_9bar/preflight/
  BUILD_PROVENANCE_VERIFICATION_V0_1_4.json

qualification/
  NO_PHYSICS_CHANGE_VERIFICATION_STANDARD_V0_1_4.json
  ESPRESSO_WHOLE_PULL_FREEZE_FINALIZATION_STATUS_V0_1_4.json

cases/reference_R0_20g_58mm_9bar/
  ESPRESSO_WHOLE_PULL_REFERENCE_FREEZE_MANIFEST_V0_1_4.json
```

## Claim ceiling

A passing release is an immutable, numerically qualified R0 calibration baseline. Physical validation remains `NOT_ESTABLISHED`.
