# EWP-FORM-A-001 — Form A whole-bed closure

Owner approved Phase 1. Base EWP: `569f357`.

**Transfer/conversion.** Use A's [D0 saved fits][d0] at PW
`dce84b22b99f114225eabb76f29014a5fc3efe5d` or later main (#409/#410):
`DESCRIPTIVE_ALL` for constants; ordinary `HYD-LOCO-<bar>` for held-out
histories, each with its fixed C2 T2-F `Mc_fixed_g`. No refits/averaging.
E1's raw-line → inlet-gauge convention gives `P=max(Praw,0)` bar, `P0=0`,
`M` = cumulative outlet liquid grams, `H=1-exp[-(P/Pd)^n]`,
`R(M)=exp[-exp(-M/Mc)]`. For viscosity mu, full depth L, density rho and gross
area A: `k_a=a*1e-3*mu*L/(rho*A*1e5)`,
`k=k_a*(Pd/P)*H*exp(-P/Pstar)*R`, recovering
`q=a*Pd*H*exp(-P/Pstar)*R`, `dM/dt=q`. Handle zero pressure analytically;
compaction always uses whole-bed inlet pressure, never local stress.

| Arm | Mechanism and question |
|---|---|
| A0 | After-saturation form A, R0 wetting. Check Python parity; only 23 constants plus G1-style 1D test, no histories. |
| A1 | Apply the same converted permeability during wetting. R uses outlet mass only: `R=exp(-1)` until first outflow. Does high-pressure first drip slow? Report fastest wetting separately from peak flow, including null results. |
| A2, exploratory | Keep A1's pressure factor; `R_cell=exp[-exp(-X_cell/Xc)]`, `X_cell=1-remainingExtractable/initialExtractableDensity`. Can depth-varying extraction move the peak, improve 1/2/3.5-bar endpoints or reshape traces? Use wetted-column series resistance during filling. |

**Compatibility/Xc.** Source inspection confirms R0 extraction (0.15/s),
inventory and solute transport operate independently of WP02 permeability.
Form A excludes `effectivePermeabilityEvolution` and E1 while reading existing
inventory; no conflict/fix is needed. Xc is the initial-solid-mass-weighted
bed-mean X at outlet `M=Mc` in A1 DESCRIPTIVE_ALL at 9 bar; report the same
quantity at 6/9/11 bar as three numbers. No flow fitting. Test non-decreasing
cell X and uniform-X equivalence to whole-bed recovery at equivalent mass
`Mc*X/Xc`; actual X–M need not be linear.

**Pre-run expectation.** The saved descriptive parameters give
`argmax C_A = 5.998561 bar` (capacity 2.103899 g/s), so `t_wet ∝ 1/C_A` predicts
fastest wetting near 6.00 bar, close to observed peak flow at 6.1 bar but above
fastest wetting near 4.5 bar. Little pressure separation is expected; continue
regardless.

**Files/checks.** Add `solver/espressoWholePullFoam/formAWholeBedClosure.H`;
wire `espressoWholePullFoam.C`, `scripts/prepare_case.py`; add
`scripts/form_a_verification.py`, `scripts/form_a_demonstration.py`, `scripts/form_a_report.py`,
`tests/test_form_a*.py`. Check A0/Python parity and byte-identical disabled
outputs against main; preserve E1 code/results. Update source manifest,
lock/historical-hash compatibility, QA metadata, scientific-script allowlist, `dependencies/puckworks.lock.json` to current
PW main, `README.md`, `docs/PUCKWORKS_INTEGRATION.md`, `docs/PROJECT_STATE.md`
(E1/FORM_A status lines); replace `np.trapz` in
`tools/sci_md_rheology_001/analysis.py`; mark `PUBLICATION_AUDIT.md` historical
v0.1.4. PW stays read-only.

**Runs.** Before campaigns, pair 0.0025/0.005 s at 2/6/11 bar and peak-bracketing
neighbors; report endpoint, peak and first-drip changes, then justify one step
for every arm, without an inventory gate. A1/A2 each run 56 histories plus
23 constants: nominal 1/2/3.5/4/5/6/7/8/9/11/13, 5–8 every 0.25 bar, and
8.25/8.5/8.75, deduplicated. Authenticate Waszkiewicz
`traces_per_brew`/`equilibrium_windows`: 56 distinct brews,
[Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0;
saved evidence/code inspected; all 56 raw-file hashes match E1. Keep E1 R0 geometry,
stable clock, 100-s endpoint, masks (onset+2–100 s primary; 5–100 s secondary),
1,000 paired condition-balanced whole-brew resamples, seed 20261103.
No runtime caps; record core-hours; native outputs stay outside Git.

**Grades/outputs.** Reuse [scorecard][bands] B1 accuracy, nominal peak,
slope ≥9 bar and resolved trends; C0/D0 onset (3.51/4.53 s) and absolute
low-bias (0.10/0.20 g/s). MEETS/NEAR/MISSES, no new gates; identical B1 masks.
Under `docs/demonstrations/FORM_A/`: E1-format `GRADES.csv`, `ENDPOINTS.csv`,
`FIRST_DRIP_BY_PRESSURE.csv`, `RUN_MANIFEST.json`; one-page numbers-first
`SUMMARY.md`, E1/A0/A1/A2 rows (endpoint/trace RMSE versus B1, continuous peak
[95%, explicit uncertainty source], slope, individual low-pressure residuals,
first-drip medians versus observed, wetting/flow peak pressures, Xc sensitivity);
2–3 physical sentences per arm; endpoint (observed/Python A/A0/A1/A2) and
first-drip (observed/E1/A1/A2) figures. Label E1 transferred-median reference,
A0 constant-only; fold ranges are not confidence intervals. Standard status
tags appear only in SUMMARY's single header line. No fines, channeling,
thermal physics, restart ratchet or new data.

[d0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv
[bands]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
