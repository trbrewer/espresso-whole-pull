# SCI-MD-RHEOLOGY-011 result

**NO_MATERIAL_ARRANGEMENT_CONTRAST_FOR_TESTED_DELIVERY.** All eight resolved-model arrangement contrasts are BELOW_BUDGET after the frozen empirical numerical allowances. Full conditional E2 was not triggered: **E2_NOT_EXECUTED_CONDITIONAL_GATE**, neither a pass nor a failure. PHYSICAL_VALIDATION remains **NOT_ESTABLISHED**.

Relocating the unchanged 25% high-k / 75% low-k distribution from a fast core to a fast outer annulus did not produce a qualified material delivery contrast for these laws, pressure histories, outputs and mass supports. This completes the bounded question. It establishes neither exact invariance nor a hydraulic null, and does not establish autonomous E2 transfer to B. No successor, default adoption or merge is authorized.

## Eight independent decisions

A is the reference; B is the comparison. E_Spath is dimensionless and D_TDS_pp is in percentage points. Displayed rounding does not enter decisions. Complete unrounded variants, all allowance components and independent 50-digit arithmetic discrepancies are in [PRIMARY.json](PRIMARY.json) and [METRICS.json](METRICS.json).

| Law / history | Metric | M | u | Budget | Decision |
|---|---|---:|---:|---:|---|
| TR_LINEAR / UP | E_Spath | 0.0007450922383 | 0.0005249603152 | 0.01 | BELOW_BUDGET |
| TR_LINEAR / UP | D_TDS_pp | 0.04282843717 | 0.01785706662 | 0.1 | BELOW_BUDGET |
| TR_LINEAR / DOWN | E_Spath | 0.00139804403 | 0.0004362080604 | 0.01 | BELOW_BUDGET |
| TR_LINEAR / DOWN | D_TDS_pp | 0.04593626083 | 0.007759893809 | 0.1 | BELOW_BUDGET |
| SW_WATER_ANCHORED_90C / UP | E_Spath | 0.0004182519856 | 0.0004607719189 | 0.01 | BELOW_BUDGET |
| SW_WATER_ANCHORED_90C / UP | D_TDS_pp | 0.0226592414 | 0.01974173585 | 0.1 | BELOW_BUDGET |
| SW_WATER_ANCHORED_90C / DOWN | E_Spath | 0.0007535108242 | 0.0005675822663 | 0.01 | BELOW_BUDGET |
| SW_WATER_ANCHORED_90C / DOWN | D_TDS_pp | 0.02693178606 | 0.01732635153 | 0.1 | BELOW_BUDGET |

Each decision satisfies u <= 20% of budget and M+u < budget. The closest allowance ceiling is SW UP fraction TDS: u=0.01974173584764325 pp versus a 0.02 pp ceiling; it qualifies without rounding. Radial allowances separately refine A and B and add the absolute changes, preventing cancellation. Temporal and axial refinements are paired; SW property refinement is paired and TR property contribution is zero. These allowances describe numerical sensitivity, not confidence intervals or rigorous continuum-error bounds.

## Sealed support and tails

UP: **0.016584641 kg**; DOWN: **0.016895013 kg**. Each endpoint uses all 18 terminal C masses for its history (nine A and nine B), with Decimal downward rounding of 95% of the minimum. [SUPPORT.json](SUPPORT.json) retains exact terminal values and trace hashes; [SUPPORT_RECEIPT.json](SUPPORT_RECEIPT.json) seals them before PRIMARY_SCORED in the append-only ledger. An independent 80-digit floor calculation agrees.

Across all 36 C traces, the scored fraction is 80.582384633%–94.999999149%; unscored terminal tails are 0.00087287653198–0.00407112380141 kg. [Every terminal, fraction and tail](COVERAGE.md) is reported, with machine-readable [coverage](COVERAGE.json). Historical 009 supports are unchanged. No support was cropped or extended after scoring. Zero and the first native increment are retained; native Q*dt water is used throughout.

## Geometry compatibility and distribution preservation

G2 / GEOMETRY_COMPATIBILITY_NO_GOVERNING_PHYSICS_CHANGE; NO_GOVERNING_PHYSICS_CHANGE. The explicit supported interface_aligned_two_zone option renders conforming radial blocks sharing an INTERNAL material interface. Shared validation covers rendering and viscosity compatibility; legacy rendering remains unchanged. Native governing equations, constitutive laws, temporal coupling, spatial operators and executable are unchanged.

B interface R*sqrt(3/4) was computed at 80-digit Decimal precision and serialized as **0.02511473670974872 m**; the defining expression and exact Decimal value are in [GEOMETRY_CONTRACT.json](GEOMETRY_CONTRACT.json). C uses 48/16 radial cells (96/32 refined); short E2 uses one cell per zone. Measured mesh geometry and native traces independently satisfy the frozen 1e-8 relative geometry tolerance, connectivity and boundary checks. Full-basket scaling and actual permeability assignments pass.

| Class, identical in A and B | Area fraction | Bed volume (m³) | Pore volume (m³) | Dry mass (kg) | Initial inventory (kg) |
|---|---:|---:|---:|---:|---:|
| High k = 3e-15 m² | 0.25 | 5.95238095238e-6 | 2.38095238095e-6 | 0.005 | 0.0014 |
| Low k = 7.5e-16 m² | 0.75 | 1.78571428571e-5 | 7.14285714286e-6 | 0.015 | 0.0042 |

Both mean permeabilities are 1.3125e-15 m². B INNER is the slow material and holds 75% of initial inventory; its fast class is OUTER. Native regional exports are already full-basket quantities. The independent non-exchanging path permutation null is unit-tested algebra, 0.25 F(kH)+0.75 F(kL), without any new P integration or revision to P's earlier insufficiency result.

[Compatibility](COMPATIBILITY.json) covers 43 legacy render scenarios and identical interpretation of all 18 A traces by the historical and geometry-aware adapters. [Generated legacy comparisons](LEGACY_GENERATED.json) additionally compare all 24 physical files in each of five representative prepared cases byte-for-byte at identical locators; differences are confined to provenance/environment and manifest metadata. Historical observers remain unchanged.

## Qualification, counts and identities

Exactly **32 new integrations** completed and qualified: **14 short + 18 full C + 0 full E2**, matching the authorized no-trigger total. There were **zero preparation failures, zero native startup/integration failures, zero pending attempts and zero retries**. No extra native matrix was run. All 18 accepted A/C integrations were reused read-only after verifying 1,949 actual local files, including traces, configurations, tables, fields, executable and runtime receipts. [RUNS.json](RUNS.json) preserves every preparation, invocation, integration-start and completion event with the append-only external ledger hash. [ARTIFACT_RECEIPT.json](ARTIFACT_RECEIPT.json) binds new evidence; bulky native evidence and restricted sources remain external.

All 14 planned short checks pass. Worst analytical flow/share relative discrepancy is approximately 1.70e-12. Identical serial repeats have zero normalized discrepancy; MPI maxima are 1.4044e-11 (C) and 2.0588e-11 (E2), below inherited limits. MPI places the actual material interface across two nonempty processor owners with the expected interface faces. Constant, doubled-viscosity, equal-k, endpoint-pressure quadrature and native accounting checks pass. The equal-k INNER share is 0.75. [SHORT_CHECKS.json](SHORT_CHECKS.json), [SHORT_QUALIFICATION.json](SHORT_QUALIFICATION.json) and [REFERENCE_QUALIFICATION.json](REFERENCE_QUALIFICATION.json) retain checks of geometry, bounds, inventories, conservation, positivity, clocks, fields and source domains.

- Current-main base: 63fd95e (010 #169 was already merged when fetched); accepted 009 merge: dd05d3dd8dd8f690941f22e1583acf2026a23955. 010 was not cherry-picked or altered.
- Scientific Puckworks pin: 2058d0e947ee9eb92c52d64f6165b810f1fb4732; read-only guide head: 518fb9c480dbcef475789f48f25843238ff8a9d4.
- Production Puckworks lock remains fc61c4670ec7bf801e40bb391aab16048b8da26b.
- Accepted executable SHA256: 3de93829850829db53927e5a079a855d1c09922f238a3a330f5d01f32f9eb1fb.
- Runtime receipt SHA256: 91917bc53ed84777a7c3eaf9838954bdb947041d8ad3dd0e9fd1e137d7052d5c.
- Exact reuse/table/source identities: [REUSE.json](REUSE.json). Scope and executed-data roles: [SOURCE_USE.md](SOURCE_USE.md), [SOURCE_CHECK.json](SOURCE_CHECK.json). Accepted viscosity sources and available Ribes/PocketScience evidence were checked directly; contextual assays were not calibration targets. No newly qualified direct pairing superseded this question. Unavailable private files are not declared nonexistent or exhausted.

## Software, review and checks

Software compatibility is qualified separately from the delivery null. The genuine [original independent pre-scoring audit](PRE_SCORING_AUDIT.json) passed before every full C start. [AUDIT.json](AUDIT.json) records the bounded independent addendum after two software corrections: restoring legacy empty viscosity-off configuration acceptance and making short-receipt reproduction automatic. All 46 new-case physics renderings remained identical; scientific inputs, observers, thresholds and native evidence were unchanged. [POST_C_QA_CORRECTION.json](POST_C_QA_CORRECTION.json) explicitly records the correction after 18 C completions and before support sealing/scoring. No full integration was rerun.

The corrected complete local Python suite passed **1,586 tests, 7 skipped**, with no failures/errors. Initial local/hosted QA failures and their corrections are disclosed in [QA.json](QA.json); they were software/metadata/environment check failures, not native integration failures. Final exact-head independent review and hosted CI are separately reported on [PR #171](https://github.com/trbrewer/espresso-whole-pull/pull/171), linked to [issue #170](https://github.com/trbrewer/espresso-whole-pull/issues/170). The PR remains OPEN/UNMERGED. Exact live branch/head/tree come from Git and the final review receipt rather than a self-referential committed head claim.

## Figures and reproduction

- [Permeability layouts and area fractions](layouts.svg)
- [Pressure, flow, INNER and correctly mapped high-k allocation](hydraulics.svg)
- [Cumulative solute versus beverage mass](delivery.svg)
- [Five equal-mass fraction TDS](fractions.svg)
- [Primary metric and allowance versus budget](primary_budgets.svg)

[DIAGNOSTICS.json](DIAGNOSTICS.json) reports native base flow/allocation diagnostics without adding primary decision thresholds. No conditional E2 result plot is produced because full E2 was not executed. Use the [frozen protocol](PROTOCOL.md), [contract](CONTRACT.json), [freeze](FREEZE.json) and [reproduction commands](README.md).

The narrow implication is that this unchanged permeability histogram admits no material arrangement contrast in the two tested delivery measures on the sealed supports. Resolution sensitivity, especially radial fraction-TDS sensitivity, remains relevant. The result does not identify a unique lateral mechanism or establish arbitrary-geometry equivalence, wetting applicability, fresh-espresso property validation, assay-EY equivalence, production adoption, or a universal claim about histogram-only surrogates. PHYSICAL_VALIDATION remains NOT_ESTABLISHED. Stop after this task.
