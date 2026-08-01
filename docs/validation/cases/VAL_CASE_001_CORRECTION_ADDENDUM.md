# VAL-CASE-001 bounded correction addendum

## Material defect and causal path

The frozen protocol required every perturbation to remain within the existing
solver/contract domain and specifically required the critical compaction
pressure to exceed the maximum possible applied bed pressure drop. The generic
5% generator produced `pc -5% = 1,177,197.25 Pa`, below the machine
`pshut = 1,200,000 Pa`, and `pshut +5% = 1,260,000 Pa`, above
`pc = 1,239,155 Pa`. `prepare_case.py` failed closed before OpenFOAM launch.

This is a `RESULT_AFFECTING_METHOD_OR_DATA_DEFECT` because an asymmetric or
out-of-domain derivative pair could affect numerical correctness and
scientific interpretation. It is not a scientific result and was discovered
without inspecting a derivative or external observation.

## Invalidation and bounded replacement

- Invalid preparation attempts retained externally: `A-pc-MINUS` and
  `A-pshut-PLUS`; OpenFOAM execution count for each is zero.
- Audit-complete endpoints invalidated from derivative use:
  `A-pc-PLUS` and `A-pshut-MINUS` at 5%.
- Corrected primary probes: `pc +/-2.5%` and `pshut +/-2.5%`.
- Corrected half-step probes, only if selected by the unchanged frozen rule:
  `pc +/-1.25%` and `pshut +/-1.25%`.
- All other primary probes remain +/-5%; all other selected half steps remain
  +/-2.5%.
- The intended valid scientific matrix remains exactly 47 OpenFOAM runs.
  Completed invalid endpoints are recorded separately and excluded from the
  valid-run count. The two failed preparation attempts are not OpenFOAM runs.
- Stage-A ranking, features, scales, conditions, SVD tolerances, reporting,
  framework pin, solver, and claim ceiling are unchanged.

The replacement is the largest simple symmetric protocol-listed half-step
that preserves strict `p_shut < p_c` in both corrected endpoint pairs. This is
the single bounded correction cycle authorized for VAL-CASE-001.

`NO_GOVERNING_PHYSICS_CHANGE`

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`
