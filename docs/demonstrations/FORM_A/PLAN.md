# EWP-FORM-A-001 — Form A whole-bed closure

**Transfer and conversion.** Use [D0 saved fits][d0] at PW `dce84b2`: DESCRIPTIVE_ALL
for constants; ordinary HYD-LOCO tuples and fixed-bank Mc for histories, without refits.
Form A is the selected four-parameter primary candidate (accuracy vs B1: NEAR / UNRESOLVED).
Keep E1's raw-line → inlet-gauge convention, `P=max(Praw,0)` bar and P0=0.
For outlet liquid mass M, `H=1-exp[-(P/Pd)^n]`, `R=exp[-exp(-M/Mc)]`;
`k_a=a*1e-3*mu*L/(rho*A*1e5)` and `k=k_a*(Pd/P)*H*exp(-P/Pstar)*R`
recover the imposed q-law. Handle zero P analytically; compaction remains whole-bed.

| Arm | Authorized scope |
|---|---|
| A0 | Saturated-only closure, unchanged R0 wetting; 23 constants and G1 parity. In-sample DESCRIPTIVE_ALL; no native histories. |
| A1 | Same closure during wetting; outlet-mass R remains exp(−1) until outflow. Complete 23 constants and 56 histories unchanged. |
| A2 | Extraction-indexed `R_cell=exp[-exp(-X_cell/Xc)]`; retired after partial execution. Retain every completed/probe/step/superseded run; run none of the 69 held cases; no grade. |

**Compatibility and normalization.** R0 extraction (0.15/s), inventory and transport
are active independently of WP02 permeability. Form A excludes E1 and
`effectivePermeabilityEvolution`; no competing hydraulic branch is active.
X is one minus remaining/initial extractable solid. Xc is A1's bed-mean X at M=Mc:
**0.8294438807 / 0.8422833432 / 0.8524326302** at 6/9/11 bar; use 9 bar without fitting.
Retain uniform-X equivalence, monotonic-X and byte-identical off-path checks.
Record probe observations separately from the algebraic recovery cap (~0.737).

**Pre-run expectation.** Descriptive capacity peaks at **5.998561 bar** (2.103899 g/s),
so A1 approximately ties fastest wetting to the flow-capacity peak. This is near
observed peak flow 6.1 bar but above fastest observed onset at nominal 3.5 bar;
C0's 4.55 bar is a fitted-curve median. This expectation is not a gate.

**Runs.** The pre-campaign 0.0025/0.005-s pairs at 2/6/11 bar and peak neighbors
selected 0.005 s for every arm, without an inventory gate. Constants combine
11 nominal pressures, 5–8 every 0.25 bar and 8.25/8.5/8.75, deduplicated to 23.
Primary completeness is **23+79=102**. Use the same 56 Waszkiewicz histories,
geometry, stable clock and masks as E1; native outputs stay outside Git, with
all execution roles/core-hours reconciled and no runtime caps. No new CFD campaign.

**Reporting.** Reproduce B0c's full operator: beverage cup mass on original
observation timestamps within common native/source support, baseline, mass gradient,
31-sample Savitzky–Golay filter, strict >0.5 g and >0.1 g/s for ≥2 s, interval start.
Never extend terminal mass. NaN on valid evidence is censored at the latest sampled
`t_j` with `T_last-t_j>=2`; use `max(0,c_i-y_i)^2`. Missing/corrupt evidence is
unavailable; state coverage. Grade censored RMSE bounds MISSES only above 4.53 s,
otherwise NOT_SCORED. Front arrival has a separate 100-s censor; old 8.63-s front
RMSE is superseded and ungraded. Use retained E1 traces only, writing under FORM_A.

Keep liquid-ρQ hydraulic scores and report endpoint beverage-flow differences ungraded.
Recompute original, A0-delay and A1-delay Python A on E1's primary/companion masks.
Compare native descriptive A1−A0 and ordinary-fold held-out A1−reduced-A0 hydraulics;
the latter uses authenticated E1/R0 delays, no beverage observer or borrowed solute.
Report both scores and paired differences on identical draws (1,000; seed 20261103).
Reuse [existing bands][bands], individual 1/2/3.5 residuals and 9/11/13 slope regression.
Separate D0 parameter-refit capacity intervals, numerical solver sweep peaks and
nominal peak grades; label resamples “conditional on transferred fits.”

**Files and closeout.** Solver/header, prepare_case, Form A helpers/reporter/tests,
source/QA metadata, PW lock and integration/status docs; NumPy compatibility and
historical publication label. Preserve E1/PW. Publish one-page SUMMARY, CSVs, figures,
manifest and final normalization/qualification records. Recover completed failed-check
records without rerun, clipping or relaxed bounds; retain all hydraulic brews and
quantify concentration excess versus onset beverage mass. Relative bound tolerance
is a follow-up outside this PR; no successor implementation.

[d0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv
[bands]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
