# Independent scientific review — SCI-MD-WASZ-RESTART-RESPONSE-001

Disposition: **PASS within the declared descriptive and conditional scope. No
material correction requested.** This is an independent AI scientific review,
not a human GitHub approval, independent acquisition, or physical validation.

Reviewed candidate: `e902a3d594d12b79a71d963b684cdd9a6e3c4673`, tree
`57ce676517747053b710da58c9dc27a631abf139`; actual base
`adb50c634f0e7959eb1e5a63405ee881cde7be72`. The candidate working tree was clean.
The frozen plan was introduced by `20f982d004486c910dddf0dc323c0679aff00e54`
and has no subsequent diff. Review date: 2026-10-20. Later recordkeeping,
final-head hosted CI, and PR lifecycle must be attributed separately.

The review inspected the plan, implementation, 19 focused tests, source manifest,
JSON/CSV results, result prose, rendered raw-clock figure, current project-state
and programme/ledger entries, source plotting script, and relevant EWP/Puckworks
source and claim-scope guidance. The separate proposed rebrew protocol was read
as conceptual prior work. The paper's apparatus and Figure 10 discussion were
checked directly. Puckworks and repository files were not edited by this reviewer.
The candidate's pending overall QA/review markers were not treated as passed CI.

## Reviewed artifact bindings

SHA-256 bindings for the exact scientific candidate (relative to EWP root):

| Artifact | SHA-256 |
|---|---|
| `docs/analysis/sci_md_wasz_restart_response_001/PLAN.md` | `0ad18c251b5473a9a9c7f81250d620661abec1d6cb8b41f117960da53896b97c` |
| `tools/sci_md_wasz_restart_response_001/analyze.py` | `dbb974b93741128b7b5ae0ae8fce46000cbbf65c30ece748913c8693b3ace5f4` |
| `docs/analysis/sci_md_wasz_restart_response_001/SOURCE_MANIFEST.json` | `65d7a5fe077a28a650a770477f7a104b44077a48d0156b4d97b83457d9cc5f61` |
| `docs/analysis/sci_md_wasz_restart_response_001/RESULT.json` | `776fd5ad639461f2071a45f20ef1fb27d5dcb6d5f78cb2ec554382a6ccb6419a` |
| `docs/analysis/sci_md_wasz_restart_response_001/RESULT.md` | `b2fb19af5d183b9c2f5e8a1f00658389f25ccdc10c042eb66f6f5638ee4f3626` |

External review evidence locators below are relative to the task evidence root;
raw source files remain at the authenticated source-root-relative paths in
SOURCE_MANIFEST.json. These evidence files are outside Git.

| Locator | SHA-256 |
|---|---|
| `independent_review_recompute.py` | `ba0b8e8455064393f241b6ef1143ff7616b0559724f7cc26652affebfecc4d74` |
| `independent_review_receipt.json` | `64fa3d8f89afe7a5911d361cd967676a175b0c04a21b0dca8a3de5d15107547d` |
| `independent_reproduction_hashes.json` | `e2f1f3eb58cbeaccfa72319260786065cbff72f970f063eed0e7343e2e34df8a` |
| `independent_focused_tests.log` | `bf0ac28a4b0bf073e4e5e169857c304e568377fe60e8427979852638c4df3268` |

## Source identity and temporal support

I independently computed Git blob hashes with the Git object header and SHA-256
from source bytes. The acquisition is blob
`7940d6aa008e7cae37bb1bf8ceece44fa07d0bff`, SHA-256
`e82430cde25574140d2026882a883fba21a0f0ac6d9588b15df22571836f68e9`,
163,514 bytes. The plotting script is blob
`f93c4c2abb6847d70b21df669bd6940089c226b3`, SHA-256
`aa35ade18cc8b6946164279d6e2e82337435c3165698be932ff3d0f32b47cd74`,
1,783 bytes. Both agree with the pinned tree at
`fbc33d3380a9c8cff2467bae70fec7137a6ed46f`; the source checkout HEAD matches.
Data attribution and GPLv3 software treatment are kept separate. Neither the
upstream plotting script nor the upstream analysis pipeline was executed.

Independent pressure-only grouping reproduces 1,818 original samples,
0.126–170.031 s, all adjacent differences between 93 and 95 ms, six active
spans E0–E5, and seven low-pressure spans L0–L6. All 13 first/last indices and
both adjacent transition brackets agree with the result. The raw-clock figure
shows these spans and primary windows without shifting episode clocks. Its
five-sample derivative is explicitly separated as lineage only.

The observer checks both endpoint brackets and every intervening edge; it does
not merely check endpoint values. Negative increments remain signed. Missing
mass/pressure, nonfinite values, prohibited edges, out-of-domain endpoints,
nonincreasing time and gaps beyond the fixed inspected cadence cannot silently
supply a primary supported interval. The tests cover these failure modes and
pressure-transition crossing. Missing or nonincreasing original time makes the
observer conservatively unavailable globally rather than dropping the bad row
and joining its neighbors. This conservative behavior is acceptable for this
finite authenticated acquisition, which has no such clock defects. The 95 ms
support bound is an acquisition cadence check, not an apparatus-response bound.
The script is deliberately pinned to this acquisition, not qualified as a
general-purpose damaged-file recovery pipeline.

## Independent arithmetic, pressure comparison and reproducibility

The external script `independent_review_recompute.py` imports neither the EWP
observer nor upstream code. It parses decimal tokens as exact rational numbers,
independently segments pressure, constructs the prescribed windows, interpolates
mass, integrates piecewise-linear pressure, and recomputes all 46 intervals and
66 contrasts (60 A–D and six drift). Squared pressure mismatch is independently
integrated by exact Simpson integration on the union of relative knots; Simpson
is exact because the squared difference is quadratic within each such segment.
All 15 early/later pairs are supported and nonoverlapping. No eligibility rescue
or unrequested design is present.

The comparison to stored floating outputs gives maximum differences of
2.043e-14 g/s for interval rates, 2.842e-14 g/s for contrasts, 2.221e-15 bar
for pressure means, 8.674e-16 bar for pressure RMS, and 6.356e-15 bar for maximum
pressure mismatch. These are arithmetic checks, not measurement uncertainties.
Endpoint indices agree throughout; rational versus floating interpolation
fractions differ by at most 1.996e-13.

Representative independent results below are rounded for readability. A is
later minus E0, B later minus previous active later, C later minus early, and
D early minus E0. All entries are g/s; complete precision and rational contrast
values are retained in `independent_review_receipt.json`.

| Design | Episode | E0 baseline | Early | Later | A | B | C | D |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PRIMARY | E1 | 1.823690 | 3.338857 | 3.232878 | +1.409189 | +1.409189 | -0.105978 | +1.515167 |
| PRIMARY | E5 | 1.823690 | 4.588719 | 4.305350 | +2.481661 | +0.076981 | -0.283368 | +2.765029 |
| SENSITIVITY_A | E1 | 1.833255 | 3.303989 | 3.207553 | +1.374299 | +1.374299 | -0.096435 | +1.470734 |
| SENSITIVITY_A | E5 | 1.833255 | 4.551194 | 4.312440 | +2.479185 | +0.044060 | -0.238754 | +2.717939 |
| SENSITIVITY_B | E1 | 1.836917 | 3.262610 | 3.225697 | +1.388780 | +1.388780 | -0.036913 | +1.425693 |
| SENSITIVITY_B | E5 | 1.836917 | 4.523970 | 4.304662 | +2.467745 | +0.007747 | -0.219308 | +2.687053 |

E1's B is exactly the same comparison as A. Cumulative and successive changes
are distinguished, including the much smaller and window-sensitive final E5–E4
increment. All initial drift and pressure-off mass changes also reproduce; the
intervening L1–L5 gains are 0.56658, 0.7329, 1.0092, 1.1783 and 1.2308 g.
They are neither set to zero nor subtracted as an assumed storage correction.

The published lineage matches the inspected source mathematics: trailing
five-sample mass mean, then adjacent difference divided by the current adjacent
elapsed time. Exact rational rolling subtraction agrees with
`(m[i]-m[i-5])/(5*dt[i])` at every defined row. Means are absent at rows 0–3,
derivatives at 0–4. In this record, 1,809 defined derivative rows differ from
the five-interval mass change divided by its total elapsed time, confirming the
importance of the stated distinction. No derivative maximum enters a contrast.

The 19 focused tests pass independently. A separate execution of the candidate
CLI into an external directory reproduces RESULT.json, SOURCE_MANIFEST.json,
EPISODES.csv, INTERVALS.csv, CONTRASTS.csv and RAW_CLOCK.svg byte for byte. The
hash receipt is `independent_reproduction_hashes.json`; the focused test log is
`independent_focused_tests.log`. These checks do not replace the main agent's
repository-wide checks or final-head hosted CI.

## Scientific interpretation

The observed result is supported: selected later recorded mass-delivery rates
exceed the initial late reference for all restarts and all three fixed designs,
while later rates are below their respective early rates. Thus this is not an
early-only pattern on the specified support. The prose correctly avoids calling
these guarded intervals steady state or declaring storage/scale/transit effects
finished. The final selected endpoint is 165.319 s, within active support ending
at 167.319 s. The three E0 drift intervals supply context, not an uninterrupted
counterfactual.

Pressure means, ranges, sample-weighted quartiles, direction/variation and full
piecewise-linear histories are retained. The common relative-knot comparison is
valid and uses trajectories rather than means alone. Primary A RMS mismatches
of 0.043121–0.089941 bar do not establish pressure equivalence without an
independent response bound. The report makes the nonlinear averaging issue
explicit and correctly withholds rejection of unrestricted memoryless F from
approximate matching. It introduces no fitted pressure slope, effect-driven
pressure tolerance, cohort transfer, or flow-derived basket-pressure explanation.

The apparatus and Figure 10 discussion are context, not additional channels:
the primary paper describes pump-outlet pressure and a cup scale, and its restart
discussion interprets valve/backflow behavior. It does not furnish a same-record
chemical-exhaustion assay or internal structural observation for this acquisition.
The reviewed report appropriately does not inherit chemical exhaustion, observed
channels, or an interruption-specific causal effect from that discussion or the
proposed protocol. See [the primary paper](https://arxiv.org/html/2512.21528v1).

One puck is preserved as the unit, with repeated episodes and no pseudo-replicate
inference. The model implication is appropriately conditional on stable apparatus,
observation and other conditions. A model must reproduce observed mass increments
through a suitable observation operator, but the record does not locate any
required change in the puck. Dissolution, temperature/viscosity, liquid storage
and transit, machine/valve behavior, scale response, and ordinary time evolution
remain unresolved. Measurement uncertainty remains uncalibrated; numerical
precision is not used as sensor accuracy.

The candidate diff preserves the completed #207 theorem and applicability limits,
#209 results and historical producer caveat, accepted cohort/aliases, production
solver/defaults/dependency lock, and Puckworks. Its narrow shared metadata entries
agree with the quantitative outcome and unresolved physical implications.
PHYSICAL_VALIDATION remains NOT_ESTABLISHED.

**Development consequence accepted:** retain the quantitative later within-puck
delivery observation and its early attenuation and pressure histories. Withhold
an interruption-specific mechanical requirement because pressure-response,
apparatus/observation comparability and ordinary-time evolution remain unresolved.
This review authorizes no successor, model fit, solver adoption or laboratory work.
