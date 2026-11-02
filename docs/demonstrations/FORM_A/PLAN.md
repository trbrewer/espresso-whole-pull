# EWP-FORM-A-001 — Form A whole-bed closure

**Transfer and conversion.** Use [D0 saved A fits][d0] from PW
`dce84b22b99f114225eabb76f29014a5fc3efe5d` (#409/#410): `DESCRIPTIVE_ALL` for
constants; ordinary `HYD-LOCO-<bar>` for histories, with each fold's fixed-bank
`Mc_fixed_g`. No refits or averaging. Keep E1's raw-line → inlet-gauge convention:
`P=max(Praw,0)` bar, `P0=0`, `M` = outlet liquid grams;
`H=1-exp[-(P/Pd)^n]`, `R(M)=exp[-exp(-M/Mc)]`.
For viscosity mu, depth L, density rho and gross area A,
`k_a=a*1e-3*mu*L/(rho*A*1e5)` and
`k=k_a*(Pd/P)*H*exp(-P/Pstar)*R` recover
`q=a*Pd*H*exp(-P/Pstar)*R`, `dM/dt=q`. Handle zero P analytically;
compaction always uses whole-bed inlet pressure, never local stress.

| Arm | Mechanism and question |
|---|---|
| A0 | After-saturation form A; R0 wetting. Run 23 constants and G1-style Python parity; no histories. |
| A1 | Apply converted permeability during wetting. R uses outlet mass only: `R=exp(-1)` until first outflow. Does high-pressure first drip slow? Compare fastest wetting with peak flow. |
| A2, exploratory | Keep A1's pressure factor; use `R_cell=exp[-exp(-X_cell/Xc)]`, where `X_cell=1-remainingExtractable/initialExtractableDensity`. Use wetted-column series resistance during filling. Does depth-varying extraction alter the peak, 1/2/3.5-bar endpoints or traces? |

**Compatibility and Xc.** R0 extraction (0.15/s), inventory and transport are
independent of WP02 permeability. Form A excludes `effectivePermeabilityEvolution`
and E1: no conflict/fix. Xc is the initial-solid-weighted bed-mean X at outlet
`M=Mc` in A1 DESCRIPTIVE_ALL at 9 bar; report the same definition at 6/9/11 bar,
without fitting. Test non-decreasing cell X, uniform-X equivalence at whole-bed
mass `Mc*X/Xc` (actual X–M need not be linear), and byte-identical disabled outputs.

**Pre-run expectation.** The descriptive fit gives `argmax C_A=5.998561 bar`
(capacity 2.103899 g/s), predicting fastest wetting near 6.00 bar versus observed
peak flow 6.1 bar and [C0's onset-fit minimum][c0] 4.55 bar (observed nominal
minimum: 3.5 bar). Little pressure separation is expected; continue regardless.

**Files.** Add `solver/espressoWholePullFoam/formAWholeBedClosure.H`; wire
`espressoWholePullFoam.C` and `scripts/prepare_case.py`; add
`scripts/form_a_{verification,demonstration,report}.py` and `tests/test_form_a*.py`.
Update source manifest, QA metadata, historical-hash guards and script allowlist;
`dependencies/puckworks.lock.json`, `README.md`, `docs/PUCKWORKS_INTEGRATION.md`,
`docs/PROJECT_STATE.md` (one E1/FORM_A status line each).
Replace `np.trapz` in `tools/sci_md_rheology_001/analysis.py`; label
`PUBLICATION_AUDIT.md` historical v0.1.4. Preserve E1 code/results; PW stays read-only.

**Runs.** Before campaigns, pair 0.0025/0.005 s at 2/6/11 bar and peak-bracketing
neighbors; report endpoint, peak and first-drip changes, then choose one step
for all arms without an inventory gate. A2 uses a 1e−14 pressure solve for local continuity; existing bounds stay unchanged. A1/A2 each run 56 histories plus
23 constants: nominal 1/2/3.5/4/5/6/7/8/9/11/13, 5–8 every 0.25 bar, and
8.25/8.5/8.75, deduplicated. Reuse E1 R0 geometry, stable clock, 100-s endpoint,
onset+2–100-s primary and 5–100-s secondary masks, and 1,000 paired,
condition-balanced whole-brew resamples (seed 20261103). Waszkiewicz et al.
(2025), [Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0:
Raw hashes match E1.
No runtime caps; record core-hours; native outputs stay outside Git.

**Grades and outputs.** Reuse [D0/E1 bands][bands] for B1 accuracy, nominal peak
and slope ≥9 bar; C0/D0 onset 3.51/4.53 s and absolute low-bias 0.10/0.20 g/s.
No new gates. D0 late windows beyond native 100-s support remain unscored.
Publish the requested E1-format CSVs/manifest, both figures and one-page,
numbers-first `SUMMARY.md` in `docs/demonstrations/FORM_A/`: E1/A0/A1/A2 rows,
requested metrics, explicit uncertainty and 2–3 physical sentences per arm,
including nulls. Label A0 descriptive and E1 transferred-median; keep status
tags to SUMMARY's single header.

[d0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv
[bands]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
[c0]: https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_C0/SUMMARY.md
