# SCI-MD-MORONEY-TRANSFER-001 — EWP development handoff

**CALIBRATION_INADEQUATE. Do not prioritize integration of the tested formulation
on this evidence.** Puckworks executed the independently approved, conservative
Moroney 2015 JK 60 g to JK 12.5 g retrospective comparison. All ten startup/volume
families fail deep cumulative-delivery adequacy throughout the declared
readout/start sensitivity. Numerical checks qualify. The run therefore earns
neither mechanistic transfer advantage nor an independently established transfer
failure. Spatial-storage architecture remains **NOT_ADJUDICATED**.

| Central deep-selected candidates | Deep outlet RMSE, mg/g | Deep delivery error, EY pp | Shallow outlet RMSE, mg/g | Shallow delivery error, EY pp |
|---|---:|---:|---:|---:|
| Ten mechanistic families (range) | 5.388–5.954 | 2.759–3.374 | 1.689–14.140 | 3.085–10.805 |
| N_M, dose-scaled widths | 6.128 | 4.249 | 8.702 | 11.073 |
| N_T, outflow-time-scaled widths | 6.128 | 4.249 | 8.762 | 6.477 |

Budgets accepted before scoring were 5 mg/g and 1.0 dry-dose EY percentage point.
The most favorable deep delivery error across all tested source/start variants,
including numerical allowance, is still 2.185 EY pp. Some models improve on both
baselines arithmetically, but calibration and shallow delivery inadequacy prevent
an earned advantage. Neither baseline is an adequate replacement established by
this run. Startup materially affects shallow outlet predictions, without changing
the overall decision. This finite two-start procedure does not prove inadequacy
of all admissible parameters or all mechanistic models, and it does not isolate
kinetics or identify wetting physics.

The owner-supplied original PDF resolved the source gate. Puckworks independently
checked original Fig3 / page219 and Fig11 / page233 marker objects and page renders:
44 accepted deep observations (22 outlet + 22 pot), 28 shallow (14 + 14),
44 duplicated deep Fig11 points excluded, and four **confirmed legend symbols**
excluded at stable data rows 7, 33, 45, 71. Every one of the 120 selected raw rows has
a matched object identity. Raw CSVs are preserved. Later papers/blue Fig11 curves
are duplicate lineage; fitted Fig7 model lines are reconstruction references.
Only selected Moroney files and the original PDF were inspected; other families
remain catalog-only for this task.

Deep outlet was primary calibration, with dependent pot-derived delivery as the
mass constraint. Shallow concentrations never entered fitting, startup choice,
axis conversion or prediction construction. Sixty-six deterministic starts across
33 family/readout fits completed; five bound hits remain recorded. All 144
predictions were frozen before one target-scoring pass. Three meshes and tightened
tolerances gave maximum numerical differences 0.135206 mg/g and 0.059658 EY pp;
relative balance residual <=6.203e-10. Separate mobile/internal/surface/delivered
reservoirs are retained. Original-source density 965.3 kg/m3, prescribed 250 mL/min,
first-outflow origin and 4% moisture dry-dose conversion are explicit. The
printed same-sign internal exchange inconsistency is conservatively corrected
and disclosed, not represented as an author-confirmed erratum.

The development choice is to withhold integration priority for this tested
combined transport/startup formulation and retain the executable diagnostic.
Any separately proposed revision would need to address the demonstrated **deep
joint-observable calibration mismatch** before renewing a transfer claim. This
is not automatic retuning, a rejection of all spatial physics, a programme-wide
data-exhaustion claim, or a recommendation for new experiments. No successor is
executed or authorized by this handoff.

Puckworks owns the G2 research numerical implementation, G1 source contract and
G3 retrospective scoring. This EWP change is **G1 scientific decision consumption /
NO_GOVERNING_PHYSICS_CHANGE**. Source pot and outlet points are dependent, not
replicate experiments; engineering budgets are not source measurement errors.
This is retrospective same-source model development, not blind or independent
espresso validation. PHYSICAL_VALIDATION remains **NOT_ESTABLISHED**.

[HANDOFF.json](HANDOFF.json) binds the exact producer commit/tree, immutable
prediction/score/decision hashes and independent review, separately from EWP's
unchanged production dependency. Producer artifacts include the protocol,
qualified-source mapping, all fits and alternatives, frozen predictions, scores,
reservoir/numerical sensitivities and three VizSpec-bound figures. Local full
suites passed (Puckworks 4,617 tests; EWP 1,592 tests with 9 skips); focused reporting
and solver tests also passed. Exact-head CI and independent final review are
reported on the linked open PRs. Production/default/interface/dependency-lock
changes, native builds/integrations, new experiments, author contact, merges and
successor execution are all zero. PRs remain OPEN and UNMERGED.
