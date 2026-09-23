# SCI-MD-RHEOLOGY-009 result

Compatibility: **PRESSURE_HISTORY_LOCAL_VISCOSITY_COMPATIBILITY_QUALIFIED**.

Transfer: **E2_PRESSURE_HISTORY_TRANSFER_SUFFICIENT_FOR_TESTED_OUTPUTS**. All 24 metric decisions PASS with newly computed empirical allowances; no retuning. This is a source-conditioned computational transfer result for the two frozen histories and tested outputs, not physical validation.

## Compatibility and qualification

Eight new legacy C/E2 numerical radial payloads match accepted references exactly. Eight equivalent flat histories match the new legacy controls within the inherited normalized 1e-10 tolerance; maximum drift is 3.154202539320819e-12 (E2 SW/9 bar pore-Courant diagnostic). The small flat-history interpolation roundoff is disclosed rather than rebased. Six separately counted viscosity-off old/new regression runs match exactly. Fourteen short analytical/dynamic runs and sixteen direct startup rejection checks passed.

The short non-grid-aligned histories each have continuous pressure integral 120000 Pa s; endpoint sums are 126000 (UP) and 114000 (DOWN). Native constant-viscosity water shows those +6000/-6000 Pa s quadrature discrepancies. It is not replaced by continuous analytical cup water.

All native admissibility gates passed: native/independent conservation, source-domain and old/next-state concentration/viscosity bounds, negligible corrections, reverse-flow limits, exact serialized pressure/end-time joins, flux/delivery consistency, full duration and native annular geometry/inventory accounting. Explicit limits are in [CONTRACT.json](CONTRACT.json); observed extrema are in [QUALIFICATION.json](QUALIFICATION.json). Maximum independent primary solute balance residual is 5.92885019e-12 kg against 1e-8 kg; water residual is 3.46944695e-18 kg. Maximum empirical allowance is 7.86166% of its budget, below the 20% qualification ceiling. No allowance is a confidence interval or continuum bound.

## Delivery support

Support was sealed from all nine qualified C variants per history before any E2 history run. Decimal downward rounding to 1e-9 kg gives UP **0.016584641 kg**, DOWN **0.016896355 kg**. Both laws and every refinement use these same endpoints. Every C/E2 trace reaches its endpoint.

| History | C scored fraction of terminal beverage | E2 scored fraction of terminal beverage |
|---|---:|---:|
| UP | 83.101931–94.999996% | 83.143345–95.004666% |
| DOWN | 80.597907–94.999998% | 80.603789–94.983472% |

[SUPPORT.json](SUPPORT.json), [SUPPORT_RECEIPT.json](SUPPORT_RECEIPT.json), and [COVERAGE.json](COVERAGE.json) record exact endpoints and every trace. The final reference tail is deliberately outside delivery scoring. Equal continuous pressure integrals imply neither equal extraction nor exactly equal endpoint-quadrature water.

## All 24 decisions

Q and solute-path metrics below are fractions; share and TDS metrics are percentage points. Every decision uses strict M+u<budget. Full time/axial/C-radial/property/arithmetic components are in [METRICS.json](METRICS.json).

| Law/history | Metric | M | u | Budget | Decision |
|---|---|---:|---:|---:|---|
| TR/UP | E_Qint | 0.000422592396 | 0.000142898502 | 0.01 | PASS |
| TR/UP | E_Qpeak | 0.000710898304 | 1.55596437e-05 | 0.02 | PASS |
| TR/UP | D_share_mean_pp | 0.112462487 | 0.0228731587 | 1 | PASS |
| TR/UP | D_share_peak_pp | 0.296252923 | 0.0175943226 | 2 | PASS |
| TR/UP | E_Spath | 0.000550107346 | 0.000208850751 | 0.01 | PASS |
| TR/UP | D_TDS_pp | 0.0155214643 | 0.00500606943 | 0.1 | PASS |
| TR/DOWN | E_Qint | 0.000238742026 | 0.00025801096 | 0.01 | PASS |
| TR/DOWN | E_Qpeak | 0.000993455686 | 0.000607600306 | 0.02 | PASS |
| TR/DOWN | D_share_mean_pp | 0.0702779372 | 0.00318355152 | 1 | PASS |
| TR/DOWN | D_share_peak_pp | 0.197927649 | 0.0120611786 | 2 | PASS |
| TR/DOWN | E_Spath | 0.000892514192 | 0.000119960327 | 0.01 | PASS |
| TR/DOWN | D_TDS_pp | 0.019605805 | 0.00176611344 | 0.1 | PASS |
| SW/UP | E_Qint | 0.000376873401 | 3.52217598e-05 | 0.01 | PASS |
| SW/UP | E_Qpeak | 0.000719048595 | 5.0048218e-05 | 0.02 | PASS |
| SW/UP | D_share_mean_pp | 0.141360471 | 0.00878220424 | 1 | PASS |
| SW/UP | D_share_peak_pp | 0.306191955 | 0.0187857331 | 2 | PASS |
| SW/UP | E_Spath | 0.000735415776 | 0.000326781033 | 0.01 | PASS |
| SW/UP | D_TDS_pp | 0.0210262645 | 0.007861663 | 0.1 | PASS |
| SW/DOWN | E_Qint | 0.000412971945 | 2.65006337e-05 | 0.01 | PASS |
| SW/DOWN | E_Qpeak | 0.00115268129 | 1.12288758e-05 | 0.02 | PASS |
| SW/DOWN | D_share_mean_pp | 0.160070285 | 0.00984287415 | 1 | PASS |
| SW/DOWN | D_share_peak_pp | 0.217349793 | 0.0120601927 | 2 | PASS |
| SW/DOWN | E_Spath | 0.000967743035 | 0.000189203678 | 0.01 | PASS |
| SW/DOWN | D_TDS_pp | 0.026955601 | 0.00619999825 | 0.1 | PASS |

## Execution accounting

| Category | Starts | Completed | Native failures/recovery starts |
|---|---:|---:|---:|
| Task short qualification | 14 | 14 | 0 / 0 |
| Full compatibility controls | 16 | 16 | 0 / 0 |
| C primary | 18 | 18 | 0 / 0 |
| E2 primary | 14 | 14 | 0 / 0 |
| Separately required viscosity-off regressions | 6 | 6 | 0 / 0 |
| Direct native rejection checks | 16 | 16 expected rejections | 0 unexpected / 0 |

48/48 task-specific full slots completed; no additional infrastructure attempts used. 68 integrating native runs plus 16 expected startup-rejection invocations = **84 native invocations**. No incomplete native attempt. One first-short post-run QA failure (15 versus 17 digit trace serialization) was requalified from unchanged native artifacts without reexecution; its original FAILED ledger event remains. Pre-score audit corrections changed execution safeguards, not native inputs/outputs; original freeze retained. The initial broad Python QA failed due environment, live-edit integrity checks and exception-type expectations; the stable corrected full suite passed. [RUNS.json](RUNS.json) preserves all attempt events; [ARTIFACT_RECEIPT.json](ARTIFACT_RECEIPT.json) binds external raw evidence.

Elapsed values include preparation, execution and validation. Full cases range 1.673–347.919 s with 1024/2048/32768/65536 cells. Short C/E2 meshes have 2048/64 cells, respectively; recorded completed-event short elapsed values 0.155–1.033 s (the requalified first fixture has a separate original execution event). Regression pairs have 64 cells and 0.132–0.142 s elapsed. Concurrent serial case launches and incidental timings are **not benchmark speedup evidence**.

## Review, reproducibility and figures

Independent pre-scoring agent audit PASS binds freeze `2c9ed0725d273f11daf9a75c1f4e1af209c75dcfef4cbbc8d1ee89fb097ff432`; reviewer `/root/prescoring_audit` is distinct from implementation author and is not an external human reviewer. Source/build/runtime identities are in [BUILD.json](BUILD.json), [REUSE.json](REUSE.json), and the freeze. Executable SHA256 `3de93829850829db53927e5a079a855d1c09922f238a3a330f5d01f32f9eb1fb`. Ordinary final exact-head review and final hosted CI are separate PR statuses. [Commands](README.md).

Figures: [imposed/applied pressure](pressure.svg), [total flow](flow.svg), [core share](share.svg), [solute versus beverage](solute.svg), [five fractions](fractions.svg), [metric and allowance relative to budget](budgets.svg).

## Limits and stop

E2 remains sufficient only for these two histories, geometry, laws, native numerical settings and scored support. This does not identify a unique lateral mechanism, establish arbitrary-profile/geometry/continuum equivalence, whole-shot equivalence beyond support, wetting/pre-infusion applicability, fresh-espresso source validity, physical validation or production readiness. TR dilute continuation/industrial-extract transfer and SW water anchoring/90 C extrapolation remain assumptions. Accepted constant-pressure results retain their original scope.

**PHYSICAL_VALIDATION = NOT_ESTABLISHED.** No default, source table, constitutive law, Puckworks checkout or production-lock change; no E4/E8 rescue, merge, adoption or successor execution. Issue #165 / PR #166; leave unmerged and stop.
