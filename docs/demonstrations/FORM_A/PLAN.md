# EWP-FORM-A-001 — Form A whole-bed closure

**Transfer.** Use [D0 saved A fits][d0] from PW
`dce84b22b99f114225eabb76f29014a5fc3efe5d` (#409/#410): DESCRIPTIVE_ALL for
constants, ordinary HYD-LOCO-<bar> tuples for held-out histories, each with its
fixed-bank Mc. No refits. Form A is the selected four-parameter primary candidate
(accuracy vs B1: NEAR). Keep E1's raw-line → inlet-gauge convention:
`P=max(Praw,0)` bar, P0=0, M=outlet liquid grams;
`H=1-exp[-(P/Pd)^n]`, `R(M)=exp[-exp(-M/Mc)]`.
With viscosity mu, depth L, density rho and gross area A,
`k_a=a*1e-3*mu*L/(rho*A*1e5)` and
`k=k_a*(Pd/P)*H*exp(-P/Pstar)*R` recover the imposed q-law.
Handle zero P analytically; compaction uses whole-bed inlet pressure, never local stress.

| Arm | Scope |
|---|---|
| A0 | Saturated-only closure, R0 wetting: 23 constants and G1 parity, no histories. Metrics are in-sample DESCRIPTIVE_ALL. |
| A1 | Converted permeability also during wetting; outlet-mass recovery is exp(-1) until outflow. All 56 histories and 23 constants continue unchanged. |
| A2 | Extraction-indexed `R_cell=exp[-exp(-X_cell/Xc)]`, with A1's pressure factor. Closed by owner for design reasons: retain completed cases and the single 9-bar probe; do not run the 69 held cases. |

**Compatibility.** R0 extraction (0.15/s), inventory and transport operate independently
of WP02 permeability. Form A excludes E1 and effectivePermeabilityEvolution;
no competing hydraulic branch is active. X is one minus remaining/initial
extractable solid. Xc is A1's initial-solid-weighted mean X at outlet M=Mc:
**0.829443881 / 0.842283343 / 0.852432630** at 6/9/11 bar; use 9 bar without fitting.
Uniform-X equivalence uses whole-bed mass Mc*X/Xc; actual X–M need not be linear.
Tests cover this equivalence, non-decreasing X and byte-identical disabled outputs.

**Expectation and peaks.** The descriptive capacity maximum is **5.998561 bar**
(2.103899 g/s), predicting fastest A1 wetting near peak flow.
Observed fastest onset is at nominal **3.5 bar**; C0's **4.55 bar is a fitted-curve median**.
Report D0 capacity with its parameter-refit interval separately from finite-time
solver sweep peaks and their step/interpolation qualification; retain the nominal
peak grade. Label resample intervals “conditional on transferred fits.”

**Runs and observers.** The pre-campaign 0.0025/0.005-s pairs at 2/6/11 bar plus
peak neighbors selected **0.005 s** for all new arms, without an inventory gate.
Constants: nominal 1/2/3.5/4/5/6/7/8/9/11/13, 5–8 every 0.25 bar, and
8.25/8.5/8.75, deduplicated. Keep E1 R0 geometry, stable clock and 100-s endpoint.
Apply B0c sustained_onset to native cup mass/flow: >0.5 g and >0.1 g/s for 2 s,
reported at interval start; right-censor non-detections at 100 s. Grade detector
onset; retain sharp-front breakthrough as descriptive. Re-evaluate delayed Python A
with matching tuples on E1's exact onset+2–100-s primary and 5–100-s companion masks.
Use unchanged 1,000 paired condition-balanced whole-brew resamples, seed 20261103,
including A1-minus-A0 differences. The ≥9-bar slope regresses 9/11/13 condition means.
Waszkiewicz (2025), Zenodo 18046315, CC-BY-4.0; all 56 raw hashes match E1.
No runtime caps; record core-hours; native outputs stay outside Git.

**Files and outputs.** Solver header/wiring, prepare_case, form_a verification/run/report
scripts and tests; source/QA metadata and historical guards; PW lock, README,
PUCKWORKS_INTEGRATION and PROJECT_STATE; NumPy trapezoid compatibility and historical
PUBLICATION_AUDIT label. Preserve E1 and PW. Publish one-page SUMMARY, E1-format CSVs
and manifest, endpoint/onset figures and the retained probe. Keep individual 1/2/3.5-bar
residuals visible; put all eleven onset medians in CSV/figure, not the summary table.
Reuse [D0/E1 bands][bands], including C0/D0 onset 3.51/4.53 s and low-bias
0.10/0.20 g/s; no new gates. D0 late windows beyond 100 s stay unscored.

[d0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv
[bands]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
