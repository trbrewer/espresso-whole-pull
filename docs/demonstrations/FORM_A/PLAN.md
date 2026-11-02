# EWP-FORM-A-001 — Form A whole-bed closure

Phase 0 adds only this plan and its required source-manifest entry. Stop for
owner approval before implementation, dependency changes, housekeeping or
campaigns. EWP starts from `569f357`.

**Transfer.** Read PW at `dce84b22b99f114225eabb76f29014a5fc3efe5d`
(main, including #409/#410). Use A's saved `point_replay` rows in
[D0 RESULT_TABLE.csv][d0]: `DESCRIPTIVE_ALL` for descriptive sweeps and each
ordinary `HYD-LOCO-<bar>` for that condition's held-out histories, including its
fixed `Mc_fixed_g` from the C2 T2-F bank. No refitting or fold averaging.

**Permeability.** With E1's raw-line → inlet-gauge convention, use
`P=max(Praw,0)` in bar, `P0=0`, outlet liquid mass `M` in g, and
`H=1-exp[-(P/Pd)^n]`, `R(Y)=exp[-exp(-Y/Mc)]`.
For viscosity `mu`, full depth `L`, density `rho` and gross area `A`, E1's
conversion gives `k_a=a*1e-3*mu*L/(rho*A*1e5)` and
`k=k_a*(Pd/P)*H*exp(-P/Pstar)*R(Y)`.
The `Pd/P` factor cancels Darcy's pressure factor, recovering
`q=a*Pd*H*exp(-P/Pstar)*R(M)`, `dM/dt=q`. Use the analytic zero-pressure limit.
Compaction always uses whole-bed inlet pressure; never local stress.

| Arm | Change and physical question |
|---|---|
| A0, lumped | Apply form A only after saturation, retaining R0 wetting. Does the uniform solver reproduce Python A? |
| A1, wetting | Also use the same converted permeability at the wetting front, with `R(0)=exp(-1)` until outflow. Does high-pressure first drip become slower? Report fastest-wetting pressure separately from peak-flow pressure, including a tied-peak/null result against observed approximately 4.5/6.1 bar. |
| A2, exploratory | Keep A1's whole-bed pressure factor; use `R(m_cell)`. Accumulate liquid throughput from cell wetting onward per pore volume, rescaled so uniform throughflow with equal initial memory reproduces `R(M)`. Does depth-dependent washout move the peak, improve 1/2/3.5-bar endpoints or reshape traces? Increasing permeability with throughput respects Stage A's constraint. |

**Files after approval.** Add
`solver/espressoWholePullFoam/formAWholeBedClosure.H`; wire the opt-in dictionary,
wetting and cell state in `espressoWholePullFoam.C` and `scripts/prepare_case.py`.
Add `scripts/form_a_verification.py`, `scripts/form_a_demonstration.py` and
`tests/test_form_a*.py`, following E1's G1 check. Check A0/Python parity, uniform
A2/global memory and byte-identical disabled behavior against main. Preserve E1
code/results. Update the source manifest as needed. Bump
`dependencies/puckworks.lock.json` to current PW main (at least the SHA above);
update `README.md`, `docs/PUCKWORKS_INTEGRATION.md`, `docs/PROJECT_STATE.md`;
add E1/FORM_A status lines, replace `np.trapz` in
`tools/sci_md_rheology_001/analysis.py`, and label `PUBLICATION_AUDIT.md` historical
v0.1.4. PW stays read-only.

**Runs.** Per arm: 56 E1 histories plus 23 constants: nominal
1/2/3.5/4/5/6/7/8/9/11/13 bar, 5–8 every 0.25 bar, and 8.25/8.5/8.75
(deduplicated). Pair 0.0025/0.005 s at 2/6/11 bar; repeat peak-bracketing neighbors
at both steps to measure peak-pressure movement. Report endpoint, peak and
first-drip changes and explain the chosen step; no leftover-inventory gate.
Keep E1's R0 geometry, stable-pressure clock, 100-s endpoint, observers/masks
(primary onset+2–100 s; secondary 5–100 s), and 1,000 paired condition-balanced
whole-brew resamples, seed 20261103. No runtime caps; record core-hours and
external native-output identities. This plan inspected saved evidence/code,
not raw files; authenticate `waszkiewicz2025/traces_per_brew` and
`equilibrium_windows` before execution: Waszkiewicz et al. (2025),
[Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0.

**Grading and report.** Reuse [D0/E1 scorecard bands][bands]: B1 accuracy
(±0.25 g/s tie), nominal peak (5–7/4-or-8 bar), slope ≥9 bar, resolved late
trends; C0/D0 onset RMSE (3.51/4.53 s) and absolute low-bias (0.10/0.20 g/s).
Use MEETS/NEAR/MISSES, without new thresholds or PASS/FAIL gates. Compare B1 on
identical masks; continuous peaks are descriptive, with 95% intervals whose
uncertainty source is explicit, never a fold range relabelled as confidence.
Keep all outputs under `docs/demonstrations/FORM_A/`: one-page, numbers-first
`SUMMARY.md` (E1/A0/A1/A2 rows, E1 labelled transferred-median reference;
endpoint/trace RMSE versus B1, peak [95%], slope,
individual 1/2/3.5-bar residuals, first-drip medians versus observed, fastest
wetting versus peak flow; 2–3 physical-interpretation sentences per arm), two
figures (endpoint: observed/Python A/A0/A1/A2; first drip: observed/E1/A1/A2), and
E1-format `GRADES.csv`, `ENDPOINTS.csv`, `FIRST_DRIP_BY_PRESSURE.csv`,
`RUN_MANIFEST.json`. Standard status tags appear only in SUMMARY's single header
line. No fines, channeling, thermal physics, restart ratchet or new data.

[d0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv
[bands]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
