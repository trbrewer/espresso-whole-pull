# VAL-001 source adapters and first component comparisons

**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`
**Issue:** #37
**PR:** #38, open and unmerged

## Post-result hardening and corrected interpretation

The retained V2 result remains byte-identical at SHA-256
`7968e3b99045da9500442932c536bf920d559ebe660d2bad01f954f36b3f75b5`.
This cycle performed no comparison and no OpenFOAM execution. The corrected
scientific evaluation is `POST_FIT_SOURCE_RECONSTRUCTION_ONLY`,
`QUANTITATIVE_VARIANT_DISCRIMINATION_NOT_ASSESSED`, and
`MECHANISM_UNIQUENESS_NOT_ASSESSED`. The unchanged policy decision
`ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS` is conservative guidance based on
insufficient independent uncertainty-characterized evidence, not proof of a
statistical or mechanism-uniqueness test. The three current-head OpenFOAM runs
are framework-qualification artifacts and did not generate the V2 sweep.
**Correction status:** `VAL001_PR38_SECOND_CORRECTION_COMPLETE_READY_FOR_READJUDICATION`
**Physical validation:** `NOT_ESTABLISHED`

The additive correction preserves the original PR history and result bytes.
The original ten-row arithmetic is verified, but its prospective-governance
status is `INVALIDATED` because the initial freeze and invocation accounting
were incomplete. It is retained only as `SUPERSEDED_FOR_GOVERNANCE` audit
evidence; it is not blind, independent, physical validation, or a current-head
solver comparison.

The corrected framework uses deep closed schemas plus runtime schema and
semantic enforcement. It binds evidence, rights, locked dependencies, source
hashes, mappings, quantity roles, exact row support, method formulas,
interpretation rules, and execution counts. Ordinary tests use synthetic data
and are prohibited from opening the governed real comparison source. Six
historical results are re-expressed without new scoring, and the Gagné DE1
evidence-gap adapter is intentionally non-executable.

The corrected row contract records one header, 11 data rows, 10 selected
`IN_DOMAIN` rows at nominal pressures 1, 2, 3.5, 4, 5, 6, 7, 8, 9, and 11 bar,
and one excluded 13-bar row marked `OUTSIDE_LOCAL_CONSTITUTIVE_DOMAIN`.
Residual is prediction minus observation. RMSE, MAE, mean bias, maximum
absolute error, and `1 - SSE/SST` are equally weighted by selected pressure
condition. They are descriptive, with
`SOURCE_UNCERTAINTY_NOT_REPORTED` and no uncertainty gate.

Three unchanged current-head configurations completed with the activated
Foundation OpenFOAM 12 executable at 32 ranks: R1 9 bar, WP02-001 9 bar, and
WP02-001 8 bar. All retained external traces were finite; no coupling
fallback or non-converged operating-point step occurred.

The first corrected real-data invocation read the ten selected rows
and computed metrics in memory, then failed before result assembly because the
frozen Python runner used `false` instead of `False`. The partial score
exposure counts as one real-data comparison invocation and zero governed
result-producing invocations. That failure remains invalidated.

Fresh human-owner authority bound the one-token software repair, a second
freeze, a separate replacement-invocation authority, and reuse of the three
hash-verified OpenFOAM artifacts. No new solver build or case execution was
performed. Exactly one replacement invocation produced
`validation/val001/results/VAL_001_CORRECTED_COMPONENT_COMPARISONS_V2.json`
with SHA-256
`7968e3b99045da9500442932c536bf920d559ebe660d2bad01f954f36b3f75b5`.
It is `POST_OBSERVATION_REPRODUCTION`, `NOT_BLIND`, `NOT_INDEPENDENT`, and
`DESCRIPTIVE_COMPARISON_NO_UNCERTAINTY_GATE`.

The retained V2 reproduction matches the previously audited arithmetic:

| Comparison | n | RMSE (g/s) | MAE (g/s) | mean bias (g/s) | descriptive R² |
|---|---:|---:|---:|---:|---:|
| Universal source curve | 10 | 0.246382 | 0.205631 | +0.006056 | 0.858266 |
| Finite-porosity curve | 10 | 0.246420 | 0.205516 | -0.002008 | 0.858223 |

Those values remain post-fit same-campaign reconstruction statistics. The
finite-porosity branch additionally has direct 9-bar matching circularity.
Frozen rules fire because source uncertainty or an independent discrimination
criterion is unavailable, the exercise is post-fit reconstruction, and the
residual is not mechanism-unique. Thus variant discrimination is not
established and additional data are required before new physics. This does not
establish physical equivalence, model correctness, rejection of either model,
or a missing mechanism. No additional admissible component comparison exists
at the locked evidence state, and no new physics is selected or authorized.

Accounting retains at least three pre-correction computations, one failed
first-correction invocation, and one successful replacement: the minimum known
total is five. The exact pre-correction local count is not reconstructable.

Final framework completion does not add a comparison. It inventories 64
governed records, applies an explicit deep-schema or immutable exact-hash and
structure-signature treatment to each, and deterministically derives the
summary ledger from four journal events. Quantitative variant discrimination
was not assessed and mechanism uniqueness was not assessed. Additional data
remain required before new physics as a conservative policy decision.
