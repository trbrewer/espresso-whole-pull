# SCI-MD-SMRKE-TRANSFER-001 development result

**COMMON_TIME_RESPONSE: TESTED_COMMON_MODELS_INADEQUATE.**
**FINES_COVARIATE_INCREMENT: NO_MATERIAL_GAIN_FOR_TESTED_CORRECTIONS.**

Reject the tested endpoint response forms for the declared adequacy target and do
not add either tested fines correction. This identifies no specific missing
mechanism and authorizes no extra physics or successor analysis. Neither a no-fines
effect nor a purely hydraulic mechanism has been established.

Puckworks implemented and executed the four owner-specified models, following one
exact freeze and the actual independent pre-scoring agent audit. Its numerical
result is authoritative in [Puckworks RESULT.md](https://github.com/trbrewer/puckworks/blob/c65fe431fa4e964a0e2bdb8b79a3c2bb94791378/docs/analysis/sci_md_smrke_transfer_001/RESULT.md).
[HANDOFF.json](HANDOFF.json) binds exact code/source/freeze/audit/prediction/result
hashes, full central arm metrics and support exclusions. EWP consumes this bounded
development finding without importing the candidate into governing physics.

## Supported central results

33 primary plotted markers (12/7/7/7 at 0/1/2/4 g) meet the predeclared unambiguous
rule; 13 estimates are excluded for split/occluded markers. The all-marker
sensitivity uses 46 labeled estimates (20/10/9/7). These are not independently
verified raw shots. Time is machine-displayed seconds; yields retain the source
mass basis. f is nominal replacement grams / 20 g, not total fines or Q100.
Equations, units and source inspection are summarized in [README.md](README.md).

Protocol A trains only at 0 g. Primary training-time range is 9.18–68.07 s;
7/7/6 markers are supported in the 1/2/4 g arms. The 79.52 s 4 g marker is a
separate extrapolation diagnostic. Budgets are per-arm RMSE ≤0.50 pp and
absolute signed mean ≤0.25 pp; these are owner development thresholds.

| Added fines (g) | M0 RMSE / signed mean (pp) | B0 RMSE / signed mean (pp) |
|---|---:|---:|
| 1 | 0.4867 / +0.4136 | 0.4161 / +0.3293 |
| 2 | 0.4906 / +0.2696 | 0.4542 / +0.2327 |
| 4 | 0.5726 / +0.3112 | 0.5221 / +0.2691 |

Neither common model passes every arm. No M1/B1 fit is attempted in A.

Protocol B leaves all markers of one fines level out and uses equal training
intervention weights. Primary supported counts are 11/7/7/6 at held 0/1/2/4 g;
held 0 g also excludes the 9.18 s early marker for time extrapolation.

| Held fines (g) | M0 → M1 RMSE (pp) | B0 → B1 RMSE (pp) |
|---|---:|---:|
| 0 | 0.4133 → 0.4216 | 0.4123 → 0.4212 |
| 1 | 0.2916 → 0.3133 | 0.2833 → 0.2946 |
| 2 | 0.4836 → 0.4966 | 0.4413 → 0.4535 |
| 4 | 0.4652 → 0.5421 | 0.4407 → 0.5052 |
| Equal-arm aggregate | 0.4202 → 0.4518 | 0.3998 → 0.4258 |

Both interior folds worsen. Correction gain is −0.0316 pp (−7.52%) for M and
−0.0260 pp (−6.51%) for B. Holding out 0/4 g extrapolates the intervention input
for correction models independently of time support. B is grouped internal
comparison of public previously inspected data, not a second independent validation.

## Sensitivity and verification

All 18 primary/all-marker coordinate treatments preserve both scientific
verdicts. All-marker central RMSE changes are 0.4158 → 0.4507 pp (M) and
0.3901 → 0.4199 pp (B). Coordinate allowances are grounded in source pixels,
rounding and existing ambiguity notes, with shared shifts for genuinely connected
positions. These are tested digitization sensitivities, not confidence intervals.

All 648 distinct fits converge. No tau bound is hit. B monotonicity constraints
are active in some fits. The maximum error-metric change under the tighter
calculation is 0.00000745 pp, below 0.01 pp, with identical dispositions. Parameter
interpretation remains limited: the held-0-g M0 tau shifts from about 131 s
(primary) to 22 s (all markers). These effective endpoint parameters are not
physical diffusion times; finite search diagnostics do not establish statistical
identifiability. No in-shot derivative, permeability or causal claim is made.

Independent audit reviewed Puckworks `4419c342940be7f9921ebefc169f233a52437729`,
tree `abf4e8c6c04047ec18b588209eaacdba5c0eafb1`, with exact base applicability.
Prediction bundle was committed at `67f329b` before invoking the separate scorer.
Puckworks analysis/result commit: `c65fe431fa4e964a0e2bdb8b79a3c2bb94791378`, tree `df57a459b9b40e4e7adb5a026502da37eee5a974`.
Reproduction uses the Puckworks README commands in a fresh output directory,
Python 3.12.3 / NumPy 2.5.3 / SciPy 1.18.1, OPENBLAS_NUM_THREADS=1.

Puckworks focused tests: 36 PASS, independently repeated; registry gates:
65 PASS plus one acknowledged historical exception; Ruff PASS. EWP source,
static, Python, historical-baseline, shell and boundary check outcomes and live
CI are reported separately in the PR. Scientific outcomes are not inferred from
CI status. Initial pre-score synthetic/audit corrections remain in Puckworks history.

Native integrations/builds=0/0. RHEOLOGY-010/011 and RADIAL-OBS-001 were not rerun.
Production source/defaults and Puckworks lock are unchanged. No S-B reopening,
physical experiment, author contact, merge or successor execution occurred.

PHYSICAL_VALIDATION_OF_EWP=NOT_ESTABLISHED
SMRKE_CROSS_SETUP_S_B=UNCHANGED
PRODUCTION_DEFAULTS_AND_LOCK=UNCHANGED
NO_SUCCESSOR_EXECUTION_AUTHORIZED
