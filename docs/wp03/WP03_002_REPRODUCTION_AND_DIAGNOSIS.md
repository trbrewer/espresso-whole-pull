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

## Exact-head-review diagnostic closure

The original retained logs lacked the component-wise iteration history. A
telemetry-only executable built from exact merged base
`bafcb2bc6fb2d1fbc0680d8835efcc2133e714d1` preserved the original four-term
gate and reproduced the same failure times and terminal closure/fatal values
for all three cases. Its SHA-256 is
`12c16d835c550a846fdb11f34a5930d1f7c481bceee83bd00726b5a17ff6ae22`;
the exact diagnostic source diff is retained externally with SHA-256
`927ab626563e11f0321fa324b4cc9cd00a74d56cf0f2456d658d957c9d25c2a4`.

Independent gate reduction shows iterations for which the three retained
components are within their frozen mixed relative/absolute tolerances while
the continuous closure ratio remains above one. The corrected solver reports
convergence exactly when the independently reconstructed retained gate does,
with maximum accepted retained-gate ratio `0.8588275788`. This closes the
evidence gap without tolerance or physical-input changes.

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`.
