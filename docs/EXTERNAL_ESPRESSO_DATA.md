# External espresso data — EWP use map

## Maillé held-material source gate (2026-09-24)

[SCI-MD-MAILLE-TRANSFER-001](analysis/sci_md_maille_transfer_001/RESULT.md) audited
`maille2024/materials`, `psd_hybrid`, `phi`, `normalized_curves` and
`equilibrium_concentrations`. All 105 primary table cells are present, but
per-replicate selected-maximum denominator lineage and selection uncertainty
are not recoverable from pooled late-reference summaries. Result:
BLOCKED_SOURCE_CONTRACT; zero fits/folds/predictions. All five model/analyte
decisions remain NOT_ADJUDICATED. [Exact producer receipt](analysis/sci_md_maille_transfer_001/HANDOFF.json)
does not advance the production lock. No blanket corpus-exhaustion, physical
validation, laboratory recommendation or successor authorization follows.

Start with the canonical [Puckworks espresso data guide](https://github.com/trbrewer/puckworks/blob/main/docs/data/ESPRESSO_DATA_GUIDE.md).
It describes the external collection, inspected subsets, source rights and local
resolver commands. Puckworks owns dataset identity/provenance/capabilities/rights;
EWP owns compatibility, consumption history and decision-specific use.

**Current discovery snapshot:** 2026-09-23 UTC (2026-09-22 local evening),
31,503 files / 4,482,119,523 apparent bytes; 39 registered source families found.
Content identity: `f46181ee8c461fab055b73511148dd26888c7c5b3cb1bc908aad6ab9db2bb766`.
Inspected Puckworks base: `2058d0e947ee9eb92c52d64f6165b810f1fb4732`;
original inspected guide candidate: [`57187b8b36d51d6421d89e21a90be96531bbafa2`](https://github.com/trbrewer/puckworks/blob/57187b8b36d51d6421d89e21a90be96531bbafa2/docs/data/ESPRESSO_DATA_GUIDE.md)
(tree `83b6e121afb67573d43bd17467911f38dfd98be8`).
Read the guide for structural coverage, protected exclusions and private lookup.

This discovery pointer is separate from the historical accepted receipt in
[AVAILABLE_DATA_AUTHORITY](../provenance/AVAILABLE_DATA_AUTHORITY.json) and the
production-qualified Puckworks dependency lock. Neither is advanced by this task.
Puckworks PR #265 published the final reviewed guide as squash commit
[`518fb9c480dbcef475789f48f25843238ff8a9d4`](https://github.com/trbrewer/puckworks/blob/518fb9c480dbcef475789f48f25843238ff8a9d4/docs/data/ESPRESSO_DATA_GUIDE.md),
tree `7519f4794b63a04bcfc4be6888e979c96faeee8a`, identical to the final reviewed
candidate `57573ddaf9145f47d7509d3e809d9edc8210e402`. The bounded final corrections
clarify mismatch/exception records and Schulman's structural parse; the corpus
snapshot identity is unchanged. The `main` link is current navigation, not an
immutable scientific reference. Original inspected and final published identities
remain distinct from the production-qualified pin.

This reference update descends from the initial EWP guide candidate
`38e23c008d3e38c479e1e4d7bda6c6a0de198092` (tree
`8d99ce6e11f9c9d00021303c0ec219a69ef40e7b`).

| EWP question | Puckworks dataset/subset | Prior use, current opportunity and limits |
|---|---|---|
| Controlled hydraulic response | `waszkiewicz2025/traces_per_brew`, `waszkiewicz2025/equilibrium_windows` | Already used; conditional reuse for source reconstruction or a genuinely different observer. 56 brews, 11 conditions after known duplicate handling. [Dynamic-hydraulic result](analysis/xsv_waszkiewicz_dynamic_hyd_001/RESULT.md), [SCI-MD-011](analysis/sci_md_011/RESULT.md) and [root diagnosis](analysis/sci_md_012/RESULT.md) retain their negative adoption conclusions. |
| Fraction delivery and input semantics | `pannusch2024/experimental_kinetics`, `schmieder2023/raw_fractions` | Already used; conditionally reusable for source-internal observation operators and baselines. Shared campaign, fractions and cup totals are dependent. [Input-mapping result](analysis/xsv_pannusch_ewp_input_mapping_001/RESULT.md) qualified no primitive for direct EWP substitution; [data fusion](analysis/sci_data_fusion_001/RESULT.md) permits complementary source-conditioned support only. |
| Porosity / structure priors | `wadsworth2026/table1_full`, `vacaguerra2023a/extraction_conditions`, `vacaguerra2023a/dry_porosity_validation` | Already used. [Porosity/permeability result](analysis/ewp_porosity_permeability_prior_001/RESULT.md): two porosity supports, Figure 12 operator-only, no compatible permeability support. Reuse sensitivity evidence; no dry-equals-wet or universal prior. |
| Fluid-property and temperature sensitivity | `g10_liquor_rheology/telisromero2001_tables`, `sobolik2002/rheology` | Already used, conditionally reusable within source domains. Measured transcriptions differ from fitted/computed curves. [RHEOLOGY-008](analysis/sci_md_rheology_008/RESULT.md) qualified E2 among the tested candidates against a computational C reference. Industrial-extract transfer, dilute continuation and temperature extrapolation remain. |
| Operating histories / empirical pressure response | `visualizer/hydraulic_timeseries` | Already used; named boundary/onset/machine-prior decisions exhausted, corpus not generally exhausted. [Private work record](analysis/data_leverage/VISUALIZER_PRIVATE_WORK_RECORD.md) explains the 148 resumed/diagnostic production runs and retained limits. New descriptive questions may remain useful; machine pressure is not verified puck-face pressure. |
| Fines/flow observation operator | `smrke2024/figures` | Held supplementary Fig S1 digitization confirmed. Potentially reusable after a bounded series/condition/clock and pixel-error adapter; no new native logs or independent pressure-boundary validation established. This census does not establish that the modeling question is new. |

For all routes, inspect the [existing-data leverage ledger](analysis/data_leverage/DATA_LEVERAGE_LEDGER.csv),
[available-data policy](strategy/AVAILABLE_DATA_FIRST_POLICY.md), source capabilities
and [claim ceiling](CLAIM_CEILING.md). Identify relevant dataset IDs and state
**FILES_INSPECTED** versus **CATALOG_ONLY**. Missing local access means known external
evidence is unavailable here; repository-only recommendations may proceed
provisionally. It is neither evidence of nonexistence nor a blanket work-stoppage
condition. A browser agent cannot obtain private files merely because this page exists.

The older open [evidence-audit PR #117](https://github.com/trbrewer/espresso-whole-pull/pull/117)
reported Visualizer absent in its checked locations. This scan establishes the
external store is accessible here; the accepted private-work record already
records its subsequent use. Preserve the earlier report as location-specific
history, not a current collection-wide absence claim.

## RHEOLOGY-009 assessment

The initially inspected [PR #166](https://github.com/trbrewer/espresso-whole-pull/pull/166)
at `ef2be8a3293bdcdf7771037edb0502ae4ca76c31` already reports implemented
pressure-history compatibility and all 24 E2 transfer decisions passing against
its source-conditioned computational C reference. It was unmerged at this task's starting EWP base `3960b4a`, then merged independently
as `dd05d3dd8dd8f690941f22e1583acf2026a23955` during this inventory. The guide branch
incorporates that accepted main commit to resolve package-metadata conflicts.
This task neither executed nor selected that scientific work.

This census does **not materially change that task's rationale**. It confirms
existing rheology sources and machine histories, but discovers no qualified
experimental pairing of true puck-inlet pressure, evolving local viscosity and
radial fraction delivery that would replace the computational compatibility/transfer
question. Supplementary digitized flow traces do not close those joins. Existing
Visualizer negative transfer/onset results constrain any experimental interpretation;
they do not establish failure of RHEOLOGY-009's bounded synthetic test. No successor,
calibration, solver run or scientific adjudication is authorized by this guide.

## Delivery and review boundary

DATA-CORPUS-GUIDE-001 is G0 / `NO_GOVERNING_PHYSICS_CHANGE`. The scientific files,
production lock and accepted authority receipts are unchanged. Puckworks is
published first; this EWP update installs current navigation to its merged guide.
The PR closeout records EWP publication separately. No scientific successor is
authorized.
