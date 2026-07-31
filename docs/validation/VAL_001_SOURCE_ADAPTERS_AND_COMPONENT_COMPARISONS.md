# VAL-001 source adapters and first component comparisons

**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`
**Issue:** #37
**PR:** #38, open and unmerged
**Correction status:** `VAL001_PR38_CORRECTION_EXECUTION_OR_VALIDATION_FAILED`
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

The one authorized corrected real-data invocation read the ten selected rows
and computed metrics in memory, then failed before result assembly because the
frozen Python runner used `false` instead of `False`. The partial score
exposure counts as one real-data comparison invocation and zero governed
result-producing invocations. The failure is invalidated and the prospective
rule prohibits a silent retry. No corrected result bundle exists.

The original audit arithmetic remains:

| Comparison | n | RMSE (g/s) | MAE (g/s) | mean bias (g/s) | descriptive R² |
|---|---:|---:|---:|---:|---:|
| Universal source curve | 10 | 0.246382 | 0.205631 | +0.006056 | 0.858266 |
| Finite-porosity curve | 10 | 0.246420 | 0.205516 | -0.002008 | 0.858223 |

Those values remain post-fit same-campaign reconstruction statistics. The
finite-porosity branch additionally has direct 9-bar matching circularity.
They do not establish variant discrimination, physical equivalence, model
correctness, rejection of either model, or a missing mechanism. No additional
admissible component comparison exists at the locked evidence state, and no
new physics is selected or authorized.
