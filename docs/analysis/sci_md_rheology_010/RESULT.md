# SCI-MD-RHEOLOGY-010 result

**E2_CONDUCTANCE_MATCHED_REVERSAL_SUFFICIENT_FOR_TESTED_OUTPUTS**. G1 / SOURCE_SCENARIO_CHANGE_ONLY; implemented and executed without retuning.

Primary: 24 PASS, 0 FAIL, 0 UNRESOLVED. Secondary: 6 qualified material, 0 below declared budget, 2 unresolved.

E2 remains a candidate for this additional tested spatial scenario, with a demonstrated modeled delivery consequence only in the named qualified cases/outputs.

## All 24 primary decisions

Each E metric is a fraction; core-share/TDS metrics use percentage points. Decisions use unrounded values and strict inequalities. Numerical allowances are empirical sensitivities, not confidence intervals or rigorous continuum bounds. Full fresh components are in [METRICS.json](METRICS.json).

| Law/history | Metric | M | u | Budget | Decision |
|---|---|---:|---:|---:|---|
| SW_DOWN | D_TDS_pp | 0.0006862702074 | 7.588117188e-05 | 0.1 | PASS |
| SW_DOWN | D_share_mean_pp | 0.1219101317 | 0.003554345216 | 1 | PASS |
| SW_DOWN | D_share_peak_pp | 0.1939281515 | 0.005935809168 | 2 | PASS |
| SW_DOWN | E_Qint | 0.0002081903444 | 1.848487316e-05 | 0.01 | PASS |
| SW_DOWN | E_Qpeak | 0.0003068003154 | 2.354590568e-05 | 0.02 | PASS |
| SW_DOWN | E_Spath | 6.949807626e-06 | 2.542177035e-06 | 0.01 | PASS |
| SW_UP | D_TDS_pp | 0.00164161188 | 0.0003702215737 | 0.1 | PASS |
| SW_UP | D_share_mean_pp | 0.1334219539 | 0.00434997655 | 1 | PASS |
| SW_UP | D_share_peak_pp | 0.1911409847 | 0.006701221444 | 2 | PASS |
| SW_UP | E_Qint | 0.0002652488098 | 8.181261517e-06 | 0.01 | PASS |
| SW_UP | E_Qpeak | 0.0004508288477 | 2.567989959e-05 | 0.02 | PASS |
| SW_UP | E_Spath | 3.323293284e-05 | 5.784802635e-06 | 0.01 | PASS |
| TR_DOWN | D_TDS_pp | 0.001823692547 | 0.0005435320519 | 0.1 | PASS |
| TR_DOWN | D_share_mean_pp | 0.1274934292 | 0.004586289367 | 1 | PASS |
| TR_DOWN | D_share_peak_pp | 0.1946100725 | 0.007475521456 | 2 | PASS |
| TR_DOWN | E_Qint | 0.0001223598564 | 1.02005383e-05 | 0.01 | PASS |
| TR_DOWN | E_Qpeak | 0.0002479775373 | 2.378205134e-05 | 0.02 | PASS |
| TR_DOWN | E_Spath | 4.815447159e-05 | 9.046551669e-06 | 0.01 | PASS |
| TR_UP | D_TDS_pp | 0.000346654671 | 0.0003511068789 | 0.1 | PASS |
| TR_UP | D_share_mean_pp | 0.1149477185 | 0.005166853658 | 1 | PASS |
| TR_UP | D_share_peak_pp | 0.2053420094 | 0.007716655753 | 2 | PASS |
| TR_UP | E_Qint | 0.0002588342048 | 1.378180635e-05 | 0.01 | PASS |
| TR_UP | E_Qpeak | 0.0005649012746 | 2.635695275e-05 | 0.02 | PASS |
| TR_UP | E_Spath | 7.1327857e-06 | 1.76628919e-06 | 0.01 | PASS |

Primary allowances pair temporal/axial/SW-property refinements, refine C alone radially while E2 stays fixed, and independently recompute 50-digit arithmetic. CORE share always means inner outlet flow/total flow, even with the annulus faster.

## All eight secondary delivery-contrast decisions

NEW annulus-fast C versus OLD core-fast C at the same new B_star; old C supplies path normalization. Magnitudes are modeled differences, not errors against experimental truth. The radial allowance refines BOTH C configurations. Thresholds .01 and .10 pp are declared engineering materiality budgets, not taste limits.

| Law/history | Magnitude | M | u | Threshold | Decision |
|---|---|---:|---:|---:|---|
| SW_DOWN | D_TDS_pp | 2.996186994 | 0.008489871285 | 0.1 | MATERIAL_MODELED_DELIVERY_CONTRAST |
| SW_DOWN | E_Spath | 0.1345459146 | 0.0002579901528 | 0.01 | MATERIAL_MODELED_DELIVERY_CONTRAST |
| SW_UP | D_TDS_pp | 4.729163882 | 0.02003863469 | 0.1 | UNRESOLVED |
| SW_UP | E_Spath | 0.173742158 | 0.0005989287595 | 0.01 | MATERIAL_MODELED_DELIVERY_CONTRAST |
| TR_DOWN | D_TDS_pp | 3.605117227 | 0.01220078672 | 0.1 | MATERIAL_MODELED_DELIVERY_CONTRAST |
| TR_DOWN | E_Spath | 0.1618676263 | 0.0003068914568 | 0.01 | MATERIAL_MODELED_DELIVERY_CONTRAST |
| TR_UP | D_TDS_pp | 4.167558449 | 0.02463748659 | 0.1 | UNRESOLVED |
| TR_UP | E_Spath | 0.1699332992 | 0.0004808140473 | 0.01 | MATERIAL_MODELED_DELIVERY_CONTRAST |

Unresolved secondary outputs: SW_UP D_TDS_pp, TR_UP D_TDS_pp. Their empirical allowances exceed the frozen 20%-of-threshold ceiling (0.02 pp for fraction TDS). Large nominal magnitudes do not override that eligibility requirement. No refinement, threshold or allowance change is made.

| Law/history | Signed fraction TDS: new C minus old C (pp), fractions 1–5 |
|---|---|
| SW_DOWN | +0.020387, +0.407633, +1.722476, +2.996187, +2.957448 |
| SW_UP | +0.011725, +0.072941, +2.167524, +3.984719, +4.729164 |
| TR_DOWN | +0.003670, +0.511231, +2.031209, +2.977957, +3.605117 |
| TR_UP | +0.011966, +0.069277, +2.204349, +4.167558, +4.159345 |

Only qualified material decisions support their named case/output; these secondary results never change primary transfer status. The analytic constant-viscosity 4/7-to-1/13 share change is not evidence for solute materiality. A material C contrast does not prove arbitrarily accurate relative E2 contrast predictions.

## Common reference support and coverage

All 36 C variants qualified: nine old and nine new per history. Before any new E2 full launch, the declared Decimal floor_to_1e-9kg(.95*minimum) rule was sealed. One history-specific endpoint serves both laws, every refinement, and both comparison types. Zero origin/first increment, native mass-breakpoint union and conservative five-fraction splitting are retained. Native Q*dt supplies carrier water.

| History | B_star (kg) | Old C coverage | New C coverage | New E2 coverage |
|---|---:|---:|---:|---:|
| UP | 0.015983191 | 80.088200–91.554776% | 79.628998–94.999994% | 79.649786–95.025698% |
| DOWN | 0.016114389 | 76.867823–90.603383% | 77.805401–94.999998% | 77.813863–95.018662% |

Every terminal mass and individual coverage is in [COVERAGE.json](COVERAGE.json); all traces reach support. The remaining tail is deliberately unscored. Historical 009 support and results are unchanged.

## Execution, qualification and corrections

Exactly 42 native launches: 10 short + 18 new C + 14 new E2; 42 qualified completions; 0 failed native attempts; 0 startup failures; 0 infrastructure retries. All 18 old C traces/manifests/required fields were reused and reobserved read-only. Historical E2 used below is not new evidence.

All inherited 009 native admissibility, pressure/clock, conservation, bounds, geometry, actual permeability/zone assignment and final-field aggregation checks passed. The ten shorts include analytical conductance/core-share/discrete-water, serial repeats and radial-interface MPI; analytical relative errors are below 9.55e-12 (limit 1e-6). No new control, solver build or altered source law was needed.

Preparation initially selected a different zlib after sourcing the generic environment; the wrapper restored receipt-bound solver-library resolution before any native launch. One subsequent MPI preparation failed on a missing decomposition-plugin search path before launching the solver. Its directory/log/event are retained; the auxiliary environment was restored and the two completed shorts reused. No scientific input changed. A test fixture initially requested a binary64 endpoint just outside its summed mass support; its endpoint was corrected before qualification. Static QA required adding the new scientific test to its existing NumPy allowlist. The same scientific freeze received only that G0 hash correction before the one independent audit; original bytes remain externally retained ([QA_CORRECTION.json](QA_CORRECTION.json)). Initial broad QA environment/bookkeeping/live-edit failures and final checks are recorded separately; they are not scientific failures.

## Separate virtual-sectioning diagnostic

[SECTIONING.md](SECTIONING.md) and [SECTIONS.json](SECTIONS.json) report 16 stored 30 s base fields, including explicitly historical old E2. Remaining solid solubles, retained dissolved solute and assumed uniform initial dry mass are kept distinct. Actual mesh-volume overlap splits partial cells at 18 and 25 mm conservatively, without beverage-EY anchoring or invented subcell structure.

The experimental middle and outer cuts share E2’s 14.5–29 mm annulus cell at every axial station. Equal normalized E2 values are a resolution constraint: their contrast is unresolved, even if 010 outlet metrics pass. No initial-region solute provenance or regional outlet-delivery history is inferred from inventory snapshots. Ribes’s 2020 deck and newer Decent summary are one experiment; Pocket Science assay details are not imported into Ribes. McKeon challenges spatial resolution and measurement interpretation, not a numerical target. The wet-puck recovery mapping remains unqualified. No additional native integration was used. The new observer initially rejected native dimensionless `[]` notation; a source-verified parser correction and regression test reused the stored evidence. The original rejected diagnostic output is retained externally (details in SECTIONING.md).

Stored-field values below are percentages of each section’s reconstructed initial dry coffee mass. They are inventory diagnostics, not assay EY or regional delivered EY. C=64 radial cells; E2=2. Each triple is centre / middle / outer.

| Configuration/model/law/history | Solid depletion (%) | Retained dissolved solute (%) |
|---|---:|---:|
| new_C_SW_DOWN | 13.96826 / 19.42939 / 19.41758 | 6.79057 / 4.90579 / 4.91223 |
| new_C_SW_UP | 13.59189 / 18.65303 / 18.64299 | 5.93029 / 3.16730 / 3.17238 |
| new_C_TR_DOWN | 14.99977 / 21.59246 / 21.58435 | 6.42115 / 4.08154 / 4.08561 |
| new_C_TR_UP | 14.36322 / 20.24417 / 20.23490 | 5.54690 / 2.38073 / 2.38400 |
| new_E2_SW_DOWN | 13.94982 / 19.42855 / 19.42855 | 6.78938 / 4.90660 / 4.90660 |
| new_E2_SW_UP | 13.57161 / 18.65340 / 18.65340 | 5.92938 / 3.16824 / 3.16824 |
| new_E2_TR_DOWN | 14.98573 / 21.58884 / 21.58884 | 6.41135 / 4.08443 / 4.08443 |
| new_E2_TR_UP | 14.34672 / 20.24110 / 20.24110 | 5.53267 / 2.38819 / 2.38819 |
| old_C_SW_DOWN | 21.56972 / 13.18575 / 13.19736 | 3.43412 / 7.06068 / 7.05974 |
| old_C_SW_UP | 20.29118 / 12.85470 / 12.86659 | 2.73048 / 6.32166 / 6.32615 |
| old_C_TR_DOWN | 22.28517 / 14.09456 / 14.05540 | 3.06632 / 6.77235 / 6.79201 |
| old_C_TR_UP | 20.97888 / 13.56777 / 13.55092 | 2.47905 / 5.93439 / 5.95419 |
| old_E2_SW_DOWN | 21.49951 / 13.21409 / 13.21409 | 3.43584 / 7.05507 / 7.05507 |
| old_E2_SW_UP | 20.23221 / 12.88226 / 12.88226 | 2.74609 / 6.31330 / 6.31330 |
| old_E2_TR_DOWN | 22.18486 / 14.11881 / 14.11881 | 3.10091 / 6.76196 / 6.76196 |
| old_E2_TR_UP | 20.90346 / 13.59389 / 13.59389 | 2.52054 / 5.92293 / 5.92293 |

Available stored cases: 16; missing or invalid: 0. Exact compartment masses, conservation residuals, partial-cell counts and unavailable outputs are in SECTIONS.json.

## Identities, review and figures

Scientific Puckworks source `2058d0e947ee9eb92c52d64f6165b810f1fb4732`; production dependency `fc61c4670ec7bf801e40bb391aab16048b8da26b`. Actual accepted executable SHA256 `3de93829850829db53927e5a079a855d1c09922f238a3a330f5d01f32f9eb1fb`; runtime receipt `91917bc53ed84777a7c3eaf9838954bdb947041d8ad3dd0e9fd1e137d7052d5c`. [REUSE.json](REUSE.json) binds exact source, build, tables and native references. [ARTIFACT_RECEIPT.json](ARTIFACT_RECEIPT.json) binds external outputs; full logs, paths, fields, restricted tables and binaries stay external.

One independent pre-scoring agent audit PASS: [AUDIT.json](AUDIT.json), corrected freeze `518920beb697fc93ea6279018df709dadf7520e45086be499697bbea9a6a27f9`. Final exact-head agent review, protected GitHub approval, external human review and hosted CI are distinct; actual head/tree and CI snapshot are recorded in the PR handoff. Reproduction: [README.md](README.md).

Figures: [hydraulics/core allocation](hydraulics.svg), [mass-conditioned delivery](delivery.svg), [signed C fraction contrasts](fractions.svg), [support coverage](coverage.svg), [magnitude/allowance versus budget](budgets.svg).

## Claim ceiling and stop

**PHYSICAL_VALIDATION = NOT_ESTABLISHED.** This is a source-conditioned synthetic comparison, not real-puck validation. The reversal changes the area-weighted permeability distribution/residence times as well as radial position. TR dilute continuation and industrial-extract transfer, SW water anchoring and 90 C extrapolation remain caveats. No unique lateral mechanism, arbitrary geometry/permeability/history, whole-shot equivalence beyond support, two-state lumped-model, measured-speedup or production-adoption claim follows. Defaults, solver, dependency lock, Puckworks and historical results are preserved. No merge, rescue matrix, laboratory action or successor; stop at the open PR.
