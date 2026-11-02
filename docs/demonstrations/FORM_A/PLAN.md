# EWP-FORM-A-001 — Form A whole-bed closure

Owner approved Phase 1 with the changes below. Base EWP: `569f357`.

**Transfer and conversion.** Use A's saved `point_replay` rows in [D0][d0]
at PW `dce84b22b99f114225eabb76f29014a5fc3efe5d` or later main (#409/#410):
`DESCRIPTIVE_ALL` for sweeps; matching ordinary `HYD-LOCO-<bar>` and its fixed
C2 T2-F `Mc_fixed_g` for held-out histories. No refitting or fold averaging.
With E1's raw-line → inlet-gauge convention, `P=max(Praw,0)` bar, `P0=0`,
`M` = cumulative outlet liquid mass in g, `H=1-exp[-(P/Pd)^n]`,
`R(M)=exp[-exp(-M/Mc)]`. E1's Darcy conversion is
`k_a=a*1e-3*mu*L/(rho*A*1e5)`, `k=k_a*(Pd/P)*H*exp(-P/Pstar)*R`;
`L` is full depth and `A` gross area. Thus `q=a*Pd*H*exp(-P/Pstar)*R`,
`dM/dt=q`; handle zero pressure analytically. Compaction uses whole-bed inlet
pressure, never local stress.

| Arm | Mechanism and question |
|---|---|
| A0 | Form A after saturation only; R0 wetting. Check Python parity; run only the 23 constants and G1-style 1D test. |
| A1 | Same converted permeability during wetting. R uses outlet mass only: `R=exp(-1)` until first outflow. Does first drip slow at high pressure? Report fastest wetting separately from peak flow, including a null. |
| A2, exploratory | Keep A1's pressure factor; use `R_cell=exp[-exp(-X_cell/Xc)]`, `X_cell=1-remainingExtractable/initialExtractableDensity`. Does depth-varying extraction move the peak, improve 1/2/3.5-bar endpoints or reshape traces? |

**Compatibility and Xc.** Source inspection confirms R0's extraction rate
(0.15/s), solid inventory and conservative solute transport remain active
without WP02's dissolution-indexed permeability. Form A excludes
`effectivePermeabilityEvolution` and E1; it reads the existing inventory, so
no conflict or extraction-path fix is needed. Set Xc once to the initial-solid-
mass-weighted bed-mean X when A1 DESCRIPTIVE_ALL at 9 bar reaches outlet mass
Mc; report the same definition at 6/9/11 bar as three numbers, without fitting
flow. Test non-decreasing cell X and uniform-X reduction to the whole-bed law
at equivalent mass `M=Mc*X/Xc` (this does not assume the actual X–M trajectory
is linear). During wetting use the wetted column's series resistance.

**Pre-run expectation.** Solving `dC_A/dP=0` using the saved descriptive
parameters gives **5.998561 bar**, capacity **2.103899 g/s**. Since sharp-front
wetting time at R(0) scales as `1/C_A`, A1 should wet fastest near 6.00 bar,
close to the observed 6.1-bar flow peak but above fastest wetting near 4.5 bar.
This predicts little separation of the two pressures; continue regardless.

**Files and checks.** Add `solver/espressoWholePullFoam/formAWholeBedClosure.H`,
wire `espressoWholePullFoam.C` and `scripts/prepare_case.py`, and add
`scripts/form_a_verification.py`, `scripts/form_a_demonstration.py`,
`tests/test_form_a*.py`. Check A0/Python parity and byte-identical disabled
outputs against main; retain E1 code/results. Update the source manifest and
lock compatibility helper; bump `dependencies/puckworks.lock.json` to current
PW main. Update `README.md`, `docs/PUCKWORKS_INTEGRATION.md`,
`docs/PROJECT_STATE.md` (E1/FORM_A status lines); replace `np.trapz` in
`tools/sci_md_rheology_001/analysis.py`; mark `PUBLICATION_AUDIT.md` historical
v0.1.4. PW stays read-only.

**Runs.** Before the main campaign, pair 0.0025/0.005 s at 2/6/11 bar and
repeat peak-bracketing neighbors; report endpoint, peak and first-drip changes,
then choose one step for every arm, without a leftover-inventory gate.
A1/A2 each run 56 histories plus 23 constants: nominal
1/2/3.5/4/5/6/7/8/9/11/13, 5–8 every 0.25 bar, and 8.25/8.5/8.75, deduplicated.
Authenticate the existing Waszkiewicz `traces_per_brew`/`equilibrium_windows`
(56 distinct brews; [Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315),
CC-BY-4.0); planning inspected saved evidence/code, not raw files afresh.
Keep E1's R0 geometry, stable-pressure clock, 100-s endpoint and masks
(onset+2–100 s primary; 5–100 s secondary), and 1,000 paired condition-balanced
whole-brew resamples, seed 20261103. No runtime caps; record core-hours and
native-output identities outside Git.

**Grades and outputs.** Reuse [scorecard][bands] accuracy (B1 ±0.25 g/s),
nominal-peak, slope ≥9 bar and resolved-trend bands, plus C0/D0 onset
(3.51/4.53 s) and absolute low-bias (0.10/0.20 g/s): MEETS/NEAR/MISSES, no new
gates. Compare B1 on identical masks. Under `docs/demonstrations/FORM_A/`, retain
E1-format `GRADES.csv`, `ENDPOINTS.csv`, `FIRST_DRIP_BY_PRESSURE.csv`,
`RUN_MANIFEST.json`; a one-page numbers-first `SUMMARY.md` with E1/A0/A1/A2 rows
(endpoint/trace RMSE versus B1, continuous peak [95%, explicit uncertainty
source], slope, individual low-pressure residuals, first-drip medians versus
observed, fastest-wetting/peak-flow pressures, Xc sensitivity); 2–3 physical
sentences per arm; and endpoint (observed/Python A/A0/A1/A2) and first-drip
(observed/E1/A1/A2) figures. Label E1 transferred-median reference and A0
constant-only; never call a fold range a confidence interval. Standard status
tags appear only in SUMMARY's single header line. No fines, channeling,
thermal physics, restart ratchet or new data.

[d0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv
[bands]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
