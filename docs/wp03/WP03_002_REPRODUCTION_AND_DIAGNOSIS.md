# WP03-002 reproduction and diagnosis

The exact VAL-CORPUS-001 failures were reproduced with the accepted executable
SHA-256 `0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c`,
the frozen configuration hashes, and 16 MPI ranks.

| Case | Failure time | Closure | Closure/tolerance |
|---|---:|---:|---:|
| `WASZ-5-COMPACT` | 6.62 s | `6.802198601e-13` | 6.8022 |
| `WASZ-9-COMPACT` | 4.36 s | `2.820755901e-13` | 2.8208 |
| `WASZ-11-COMPACT` | 5.30 s | `1.090336947e-13` | 1.0903 |

In every failure, the reported nonlinear residual equals the continuous
analytical flow-closure term. That term compares the discretized OpenFOAM
flux with the continuous exact scalar puck-flow integral; it is a verification
diagnostic, not a residual of the discretized nonlinear fixed-point equation.
Promoting it to the iteration acceptance conjunction at `1e-13` makes
convergence depend on roundoff/discretization agreement with a different
mathematical representation.

The independent Python evaluator reproduces the finite-porosity integral,
matches its derivative to the permeability ratio, fails closed outside the
admissible domain, and reproduces the retained 11-bar exact scalar flow with
zero relative difference in binary64. The 5- and 9-bar cases fail on their
first saturated compaction step and therefore have no earlier converged
compaction row.

Diagnosis: `IMPLEMENTATION_DEFECT`.

The bounded correction is to retain and report the analytical closure
diagnostic but remove it from the nonlinear fixed-point acceptance conjunction.
Flow change, pressure change, and the linear pressure residual must still meet
their unchanged configured controls. This preserves the governing equations,
physical inputs, admissible domain, and diagnostics; it does not relax a
physical bound or accept a nonconverged discrete state.

Complete logs and traces remain outside Git. Their hashes and reduced failure
states are recorded in
`validation/wp03/WP03_002_REPRODUCTION_AND_DIAGNOSIS.json`.

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`.
