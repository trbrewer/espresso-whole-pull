# SCI-MD-MASS-DELIVERY-001 research handoff

The reusable absolute-TDS component is implemented and executed. **MASS is adequate
only in primary conditions C02 and C05.** C01 and C06 fail, so the all-four-condition
adequacy and declared practical-competitiveness requirements fail. The competent
boundary-aware empirical profile also passes only C02/C05. No material predictive
gain is established against either empirical or TIME.

| Candidate | Primary balanced R (TDS pp) | Mean absolute B (pp) | Adequate primary conditions |
|---|---:|---:|---:|
| MASS | 1.025939 | 0.271561 | 2/4 |
| TIME linear | 1.119735 | 0.918691 | 1/4 |
| Boundary-aware empirical | 1.032881 | 0.276947 | 2/4 |
| TIME u² sensitivity | 1.032628 | 0.808554 | 2/4 |
| TIME sqrt(u) sensitivity | 1.270214 | 1.036421 | 1/4 |

MASS is 0.006941 pp lower in R than empirical, improving only one of four primary
conditions. Both comparative 0.10 pp margins pass, but adequacy fails; practical
competitiveness is a conjunction, not merely a close error comparison. MASS is
0.093795 pp (8.377%) lower than TIME, failing the 0.10 pp/20%/three-condition
material-gain tests. All scores are balanced by shots within conditions and then
conditions, not pooled rows. Budgets are task working decisions, not measurement
uncertainties or published espresso standards.

Temperature-ramp C03/C04: MASS passes both (R=0.840938, abs B=0.218678 pp); empirical
passes C04 only (0.855580/0.223015). TIME linear, u² and sqrt(u) fail the two-condition
requirement (R/abs B: 0.968559/0.823669, 0.904070/0.731847, 1.072446/0.915628).
Flow-ramp C07 remains unsupported because PRED-E07-R1 fraction 10 exceeds the
training mass domain. All candidates retain it; no complete flow-ramp aggregate is
invented. C08 fails every candidate (MASS 1.506324/0.584843; empirical
1.461720/0.623260; TIME 2.201898/1.726325; u² 2.093910/1.626507; sqrt(u)
2.314059/1.828014). Ramp results do not rescue primary failure.

Source contract: FIT_2021_12 experiments 9/10/11/14/15 at grind 1.7, five conditions,
15 physical shots/90 valid TDS assays; other grinds (30 shots) excluded. Primary
March C01/C02/C05/C06, 12 shots/72 assays. Stress C03/C04 and C07/C08, six shots/36
assays each. No TDS spill exclusions or missing measured prefixes in these cohorts.
Experiment 46 is unused. Ten FIT and eleven March collection masses advance the
source-specific mE_cum; six assayed fractions are 1/2/3/5/7/10. Missing chemistry is
not zero, and assayed-support totals are not measured complete-cup totals.

The MASS model `SCI-MD-MASS-DELIVERY-001/MASS/v1`, schema `mass-delivery/1`, has
c0=0.2827944898059652 kg/kg, kb=68.0383392716077 kg^-1, p=0.8327267294693588,
and mass support [0,0.0635064] kg. TIME adds source-clock support
[0,58.31531651059772] s. Empirical selected nine knots/lambda=0 using FIT-only
LOCO; three unsupported development-fold intervals remain explicit. These
selection scores are not unbiased test scores. All coefficients are new
Pannusch-specific fits; no Grudeva numerical coefficients were transferred.

[HANDOFF.json](HANDOFF.json) identifies the exact Puckworks implementation/model
producer, its tree and file hashes. `scripts/research_mass_delivery.py` requires an
explicit checkout at that revision, verifies hashes/units/domain/model identity,
and loads that file directly. It does not search for another local Puckworks
installation or duplicate its numerical kernel. No production dependency lock
changes. The demonstrated 0.04 kg synthetic stop query predicts 0.003950580467107172
kg dissolved solids conditional on achieving that beverage mass.

One independent exact-freeze pre-score audit approved all 720 intended prediction
records. One scoring pass followed; 715 treatment records have support and five
retain the same unsupported interval. Exactly 192 starts, 8,089 actual residual
calls, zero failures, maximum 109 calls/start (caps 500/2,000). Final supported
integration allowance <9.46e-14 kg versus 1e-9 kg target; decision bounds are stable.
Pre-score integrity/numerical defects were corrected with original evidence
preserved and no extra fitting. Producer focused tests: 38 pass; EWP synthetic
consumer tests: five pass. Full QA, ordinary final review and hosted CI are separate
statuses in SOFTWARE_QA.json and the PR checks. Private per-shot reports retain all
24 shots, all five treatments, every requested metric and support flag; public
producer aggregates contain every condition.

The paired 2,000-replicate condition/shot bootstrap is descriptive: MASS-minus-
empirical R 95% interval [-0.030793,0.015697] pp; MASS-minus-TIME
[-0.570274,0.224568] pp. Four conditions support no strong population or equivalence
claim. Full source-derived summaries retain Pannusch/Schmieder attribution and
CC-BY-NC-3.0 treatment. Raw and restricted row-level outputs stay external.

Separate axes: SOURCE_CONTRACT qualified with declared stress-domain limit;
SOFTWARE_AND_QA implemented/tested; NUMERICAL_QUALIFICATION qualified on supported
intervals; PRIMARY_PREDICTIVE_ADEQUACY condition-limited;
COMPETITIVENESS_VS_BOUNDARY_AWARE_BASELINE fails declared conjunction; MASS_VS_TIME
no material gain; RAMP_STRESS_RESULTS mixed/support-limited; REVIEW_AND_CI separate.

G1 / NO_GOVERNING_PHYSICS_CHANGE. SOURCE_INTERNAL; TARGET_EXPOSED, not newly blind,
independent or prospective validation. PHYSICAL_VALIDATION remains NOT_ESTABLISHED.
No EWP native solver validation, hydraulic/pressure-to-flow capability, initial or
residual inventory identification, c_s0 mapping, absolute-closure resolution,
coffee/roast/campaign cause separation, or coefficient universality is established.
Modeled gap delivery remains prediction. Zero native builds/runs; production
source, defaults and dependencies/puckworks.lock.json unchanged. Both PRs remain
OPEN/UNMERGED; no laboratory operation or automatic successor.
