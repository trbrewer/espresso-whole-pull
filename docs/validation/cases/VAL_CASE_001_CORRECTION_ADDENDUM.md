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

## Representation-only endpoint assembly correction

After the replacement runs completed, the predeclared selector stopped before
derivative calculation because OpenFOAM serialized the nominal 30 s endpoint
as `29.9999999999994`. The reducer now maps a requested endpoint to the
retained endpoint only when their physical-time difference is at most
`1e-9 s`; larger out-of-support requests still fail. A focused test covers
both behaviors. This is a
`SOFTWARE_ASSEMBLY_DEFECT_WITH_UNCHANGED_ARITHMETIC`: it preserves the frozen
30 s feature, changes no run or scientific method, and requires no rerun.

`NO_GOVERNING_PHYSICS_CHANGE`

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`

## Independent-review correlation-method correction freeze

**Status:** `CORRECTION_FROZEN_NOT_YET_EXECUTED`

- Authority file: controlling parent-workspace `AGENTS.md` (reported by full
  host path outside committed repository metadata)
- Authority-file SHA-256: `05ec2f82ffa969bda8f4e274a4f7ecc3d9d17b28bb05e6684908349c60ba2db2`
- Superseded candidate: `a573df5b0b40d2e8db596821fff2262477a3860e` / `cf389fca0d513ebefc46472be6358fba4343c04e`
- Superseded result SHA-256: `61ab136645811608e4ed9e35f2ab034f925f56bcd3519c4fc6ae71263b09dd4c`
- Finding: `FROZEN_PROTOCOL_CENTERED_CORRELATION_REPLACED_BY_UNCENTERED_COSINE`
- Classification: `RESULT_AFFECTING_METHOD_OR_DATA_DEFECT`
- Retained immutable input: `VAL-CASE-001-OPENFOAM12-20260801`, aggregate `a1a9814ad043c1b33186ea5783f26eafc6cb4006d910984cbe23c4c37a9ae6b8`, 47 valid traces.
- New OpenFOAM launches authorized or required: zero.

The invalidated fields are the correlation matrices, primary method selection,
primary near-collinearity flags, and interpretations derived from those flags.
Physical derivatives, fixed-scale normalized sensitivities, ranking,
derivative stability, repeatability, Jacobians, singular values, effective
ranks, condition numbers, physical and fixed-scale branch separation, trace
identities, case summaries, execution accounting, admissibility, framework
disposition, and claim ceiling are provisionally unaffected.

For each parameter pair, the corrected primary method centers both sensitivity
columns and uses Pearson correlation when both centered norms are finite and
nonzero. Uncentered cosine is the primary fallback only when centered
correlation is undefined due to a zero centered norm. If neither is defined,
the value is `null` with an explicit reason. Primary near-collinearity uses
finite `abs(value) >= 0.95`. Uncentered cosine is also retained separately as a
supplemental directional diagnostic and never substitutes for the primary
classification.

Local logarithmic sensitivity is
`(parameter_baseline / output_baseline) * physical_derivative` only for a
positive finite output baseline; otherwise it is `null` with an explicit
reason. Model-form separation divided by an exact zero repeatability value is
recorded as `value: null`, `disposition: UNDEFINED_ZERO_DENOMINATOR`, and
`denominator: 0.0`.

The correction must reproduce the following centered-correlation regressions
within `1e-12`: SET_A Qfree/Ru `-0.7510065044413317`, Ru/pshut
`-0.5214655798964295`, k0/pc `0.9986439395384199`, k0/phi0
`0.9993432759777302`, pc/phi0 `0.9998744993660710`; SET_B Qfree/Ru
`-0.8829056531458825`, Ru/pshut `-0.9632316875121999`; SET_C Qfree/Ru
`-0.9522541036921677`, Ru/pshut `-0.9748127684142938`; and SET_D Qfree/Ru
`-0.9580924168083030`, Ru/pshut `-0.9573958657715449`. The superseded values
must be reproduced as supplemental cosines. Direct double-precision SVD must
preserve the singular spectra, effective ranks, and approximate condition
numbers SET_A `398232.727`, SET_B `141580.914`, SET_C `3318.371`, and SET_D
`1637.500`, together with ranking `phi0`, `pshut`, `k0`, `pc`, `Qfree`, `Ru`,
`Cu` and all otherwise unaffected fields.

Review status remains `CORRECTED_PENDING_EXACT_HEAD_INDEPENDENT_REVIEW` after
execution. Physical validation remains `NOT_ESTABLISHED`; the claim ceiling
remains `VALIDATION_SUPPORT_ONLY_PHYSICAL_VALIDATION_NOT_ESTABLISHED`.

## Corrected analysis result

- Corrected result SHA-256: `bb7bba7481a56ac8729758a6d5cd36e7d046b889256a7c1d1c8ed7cff998375a`
- Corrected result commit: `CORRECTED_RESULT_COMMIT_PENDING_CURRENT_COMMIT`
- Allowed-field comparison: `PASS_ONLY_DECLARED_FIELDS_DIFFER`
- Two independent analysis-only reductions: `BYTE_IDENTICAL`
- Valid retained cases: 47
- New OpenFOAM launches: 0
- External trace immutability: all 47 trace hashes, sizes, timestamps, and
  modes unchanged across analysis; inventory identity unchanged.

The corrected primary classifications are: SET_A compaction triple only;
SET_B compaction triple plus `Ru`/`pshut`; SET_C and SET_D `Qfree`/`Ru` plus
`Ru`/`pshut`. LOW flags no compaction pair, while MID and HIGH flag only
`k0`/`pc`. Supplemental cosine is retained but does not determine these flags.
