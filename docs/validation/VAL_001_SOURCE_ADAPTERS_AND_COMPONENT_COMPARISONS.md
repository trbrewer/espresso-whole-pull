# VAL-001 source adapters and first component comparisons

> Correction status (31 July 2026): the initial ten-row arithmetic is retained
> as correct audit evidence, but its prospective-governance status is
> invalidated. The corrected cycle is additive and classifies any recomputation
> as `POST_OBSERVATION_REPRODUCTION`, `NOT_BLIND`, `NOT_INDEPENDENT`, and
> `NOT_PHYSICAL_VALIDATION`. The original result is not a current-head solver
> comparison.

**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`
**Issue:** #37
**Physical validation:** `NOT_ESTABLISHED`

VAL-001 adds a fail-closed source-adapter framework and performs two bounded,
source-linked pressure–flow component comparisons. It changes no governing
equation, solver source, scientific configuration, calibration value,
numerical scheme, acceptance threshold, dependency lock, or claim ceiling.

The adapter binds the exact Puckworks commit and tree, source paths, evidence
class, rights, circularity, quantity roles, units, pressure node, uncertainty,
and solver mapping. Semantic validation rejects missing pressure nodes,
unsupported rights, calibration/comparison overlap, protected access, holdout
scoring, and post-hoc thresholds. Missing uncertainty is explicitly
`SOURCE_UNCERTAINTY_NOT_REPORTED`.

Commit `6e51d91` froze the adapter, input SHA-256
`0a789ed20039ff5ea21b7e1773f2f62f74a4122775e2cb3fa12ff6c24c53a831`,
mappings, metrics, zero thresholds, and one analyzer invocation. Its stated
nine-row count was a bookkeeping error: the byte-identical file has ten data
rows and the frozen filter selected all ten. The amendment records this
without a rerun or change to mappings, metrics, or results.

| Comparison | n | RMSE (g/s) | MAE (g/s) | mean bias (g/s) | descriptive R² |
|---|---:|---:|---:|---:|---:|
| Universal source curve | 10 | 0.246382 | 0.205631 | +0.006056 | 0.858266 |
| Finite-porosity curve | 10 | 0.246420 | 0.205516 | -0.002008 | 0.858223 |

The variants are practically indistinguishable under these descriptive
metrics. Residuals are nonmonotonic and largest in the low-to-mid-pressure
part of the sweep. The closure is source-linked and post-fit and pointwise
uncertainty is unavailable, so no threshold or model preference is claimed.

Execution comprised one analyzer invocation, zero fresh OpenFOAM runs, zero
protected accesses, zero holdout scores, and zero fits or retunes. The
disposition is `ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS`; synchronized
deformation, basket pressure, and flow with uncertainty is the highest-ranked
next evidence. No experiment is authorized here.

This is a `SOURCE_LINKED_POST_FIT_COMPONENT_COMPARISON`. General whole-solver
physical validation remains `NOT_ESTABLISHED`.
