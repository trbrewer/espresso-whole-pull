# WP03-002 prospective diagnostic protocol

**Status:** prospectively frozen before new OpenFOAM execution  
**Issue:** #51  
**Branch:** `solver/wp03-002-finite-porosity-nonlinear-robustness`  
**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`

WP03-002 reproduces and diagnoses the finite-porosity failures in
`WASZ-5-COMPACT`, `WASZ-9-COMPACT`, and `WASZ-11-COMPACT`. Physical inputs,
time step, nonlinear controls, initialization, evidence mappings, and the
16-rank execution mode are frozen to the original VAL-CORPUS-001 definitions
for reproduction.

The machine-readable protocol at
`validation/wp03/WP03_002_DIAGNOSTIC_PROTOCOL.json` controls exact identities,
configuration hashes, required diagnostics, diagnosis classes, permitted
equation-preserving numerical corrections, verification, comparison metrics,
and acceptance criteria.

Solver source may change only after unchanged failures are reproduced and an
independent residual-domain and derivative analysis demonstrates the cause.
No source-linked physical parameter may be changed to obtain convergence. A
no-root or out-of-domain result must be retained rather than forced.

Complete generated cases, logs, fields, processor directories, executables,
and traces remain outside Git under the authorized WP03-002 runtime paths.
Only reduced, reviewable records and aggregate identities may be committed.

Passing this protocol establishes numerical diagnosis or qualification only.
`PHYSICAL_VALIDATION: NOT_ESTABLISHED`.
