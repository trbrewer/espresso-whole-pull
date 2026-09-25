# SCI-MD-GRUDEVA-CLOCK-001 research handoff

Prefer **MASS** for the tested reduced research predictor: given a shot's measured
beverage masses, cumulative beverage mass materially improves Grudeva vial-solute
prediction beyond elapsed collection time. This changes research preference only.
EWP receives no runtime integration or production parameter/dependency update.

Canonical Puckworks [result](https://github.com/trbrewer/puckworks/blob/f395dc004a34f00d8e4583e62d5c22f066198d9f/docs/analysis/sci_md_grudeva_clock_001/RESULT.md),
commit `f395dc004a34f00d8e4583e62d5c22f066198d9f`,
tree `3fddf9dca7543a1229ef71192cf2d71defde4b83`.
[HANDOFF.json](HANDOFF.json) binds protocol, source, review, predictions,
aggregate result and private-evidence manifest by SHA-256. These pins are research
authority, not a change to `dependencies/puckworks.lock.json`.

| Form | Mean shot vial RMSE (g) | Mean absolute support-total error (g) | Adequate shots (need 10/13) |
|---|---:|---:|---:|
| TIME | 0.04307544 | 0.47449430 | 3/13 |
| MASS | 0.01653832 | 0.11340477 | 11/13 |
| MIXED | 0.01653832 | 0.11340477 | 11/13 |
| TEMPLATE | 0.04408708 | 0.50382825 | 2/13 |

MASS versus TIME: 61.6061% and 0.02653711 g lower mean RMSE, 11/13 shots
improved, 0.36108953 g lower mean absolute support-total error. All four material
gain conditions pass. MASS also materially beats TEMPLATE (62.4871% lower mean
RMSE, all 13 paired shots improve), beyond merely being competitive. MIXED does
not earn its extra coefficient: its fits reach the zero time-rate limit and
fail the required material increment against MASS. No statistical-equivalence
claim follows from their small numerical difference.

Source qualification used the joint raw CSV and analysis notebook plus thesis
methods. First 13 blocks are source-supported physical-shot groups, each with
16 nominal two-second vials from pump/wheel start. The extra fourteenth block
has unresolved cohort identity; its comparison is
SOURCE_CONTRACT_BLOCKED_FOR_NAMED_COMPARISON. Raw blocks and terminal vials
remain inventoried privately; no upstream raw payload is copied here.

Primary support has 208 vials: 180 positive-mass chemistry observations, 26
structural zeros, and two positive-mass ambiguous-zero chemistry gaps. Eleven
shots have full regular-window support; two have observed-support sums. Known
mass contributes to the cumulative coordinate through chemistry gaps. Terminal
vials have unqualified collection intervals and remain excluded. No missing
chemistry is imputed or terminal liquid silently claimed as complete-cup delivery.

The predictor's conditional input contract is measured beverage mass in grams,
qualified intervals in seconds, and shared coefficients fitted on training
shots. It integrates c(t,b) with respect to beverage mass over each vial to
produce delivered solute grams. It enforces zero delivery at zero liquid and
bounded nonnegative delivery. This is a delivery observation balance, not a
solid/liquid puck-inventory closure or beverage-flow model.

Separate dispositions:

- Source: qualified primary; alternate cohort unqualified.
- Software/QA: Puckworks 20 synthetic tests, offline quick suite and registry
  gates/lint pass; final hosted CI/review remain separate PR statuses.
- Numerical: qualified in all executed treatments, maximum integration
  allowance 8.414e-13 g/vial against frozen 1e-6 g target.
- Adequacy: MASS/MIXED adequate; TIME/TEMPLATE inadequate for the joint contract.
- Mass increment: MASS_CLOCK_GAIN_UNDER_DECLARED_CONDITIONS.
- Mixed increment: MIXED_CLOCK_COMPLEXITY_NOT_EARNED.
- Empirical competitiveness: MASS/MIXED competitive and materially better
  than TEMPLATE.
- Sensitivity: same conclusion with literal-zero chemistry and both refitted
  timing assumptions; MASS/TEMPLATE reused where inputs unchanged. No qualified
  alternate-cohort result and no robustness claim over every assumption combination.

Execution was approved by an independent agent against the exact pre-scoring
freeze. All 1,040 starts across 130 fits converged, with 57,362 objective calls.
Every authorized prediction was frozen before one scoring pass. No scientific
retuning, failed-fold exclusion or post-score correction occurred. Raw inputs,
per-shot metrics/paired differences, row predictions and four useful plots stay
private in Puckworks evidence, addressed by the sanitized manifest.

This is retrospective, source-conditioned, whole-shot-grouped predictive
evaluation on already-exposed source data, not prospective independent validation.
The result establishes no pressure/permeability/porosity law, diffusion or other
mechanism, grain-to-bed inventory mapping, flow/duration prediction, or external
coffee/apparatus transfer. It does not supersede historical negative results.

```text
PHYSICAL_VALIDATION = NOT_ESTABLISHED
NATIVE_EWP_BUILDS = 0
NATIVE_EWP_INTEGRATIONS = 0
PRODUCTION_DEFAULTS_CHANGED = false
PRODUCTION_DEPENDENCY_LOCK_CHANGED = false
```

G1 / NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE; repository declaration
NO_GOVERNING_PHYSICS_CHANGE. Owner task authorizes this bounded handoff and
ledger update; leave both PRs open and unmerged. No integration, laboratory
work, rescue matrix or successor execution is authorized.
