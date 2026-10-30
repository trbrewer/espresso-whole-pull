# E1 solver capability plan

Plan only; G0 / NO_GOVERNING_PHYSICS_CHANGE. Owner approval is required before implementation or runs. Test whether saved PRESSURE-PEAK B0c E1 capability survives the EWP spatial solver; this differs from the older SCI-MD-010 E1.

## Mechanism and transfer

Python B0c E1 is whole-bed compaction plus delivered-mass evolution with one predicted-delay multiplier:
`d = c(Pearly/bar)^(-n)`, `S = exp(-d/tau)`,
`q = a S P exp(-P/Pstar) / exp(exp(-M/Mc))`, `dM/dt = q`, `M(0)=0`.
P is nonnegative raw line pressure (bar), M is g and q is g/s. Fit three hydraulic parameters: a (conductance), Pstar (compaction pressure), tau (time). Fix training-fold nuisance inputs Mc (mass scale), c (onset scale), n (pressure exponent). Apply S once inside flow and mass evolution, never as an opening gate.

Transfer componentwise medians of the eleven saved RAW PRIMARY / T4 REFIT E1 fold records unchanged, at full stored precision. No solver-side refitting, geometry calibration or per-pressure adjustment.

## Solver mapping

Add opt-in E1 to `solver/espressoWholePullFoam/espressoWholePullFoam.C`: dictionary validation, initialization, WP02 permeability/mobility blocks and outlet-flux accumulation. Add `e1EffectivePermeability.H`, case preparation in `scripts/prepare_case.py` and tests. Keep `poroelasticCompaction.H` unchanged and mutually exclusive with E1; its local stress law differs.

Each cell carries the derived E1 multiplier; shared checkpointed state holds M, predicted d and S. Broadcast whole-bed P and M. Convert a to SI permeability by `Ka = a*1e-3*mu*H/(rho*A*1e5)`; advance M from globally summed hydraulic outlet mass flux. Keep liquid storage and solute bookkeeping separate.

Retain wetting-front integration and saturation-transition bookkeeping; activate E1 mobility after saturation. Predicted d modifies conductance, never first-drip time. **Measured onset is never an input.** Use B0c's pressure-only stable clock: Pearly is median pressure at 0–2 s. Constant curves use median saved training-fold input interpolations, labelled INTERPOLATED_INPUTS. Prescribe raw inlet pressure without extra machine-loss correction; line/bed pressure equivalence remains unestablished.

## Hard gates — implementation PR 1

Complete G1, then G2, in implementation PR 1. The scorecard's E1 replay was checked only at aggregate level.

**G1 — 1D-limit reproduction.** Use the fully saturated, uniform 1D Python setting, M=0, unchanged parameters, matching early-pressure inputs and the 100-s clock. At all 11 nominal pressures, reproduce Python E1 endpoint flow within max(0.02 g/s, 5% of Python flow). **If G1 fails: stop and report. Do not tune parameters to make it pass.**

**G2 — mass/liquid balance and time-step refinement.** Use the 100-s dry-front synthetic R0 verification fixture with E1 enabled. Retain liquid residual ≤max(1e-9 kg, 1e-8 cumulative inlet water), solute residual ≤max(1e-10 kg, 1e-8 initial extractable mass), and boundedness checks. At time steps 0.020, 0.010 and 0.005 s, coarse/fine differences must be ≤0.5% and intermediate/fine ≤0.25% for endpoint flow and declared primary inventory outputs; first-drip difference must be ≤1e-8 s. Include an unchanged off-mode control. Retain applicable existing mesh/MPI qualification.

**No demonstration run (constant-pressure sweep or measured histories) may start until G1 and G2 pass in a merged PR.** A G2 failure also blocks demonstration; report it without relaxing tolerances.

## Demonstration

Use R0 geometry/dry-front initialization, the existing 100-s endpoint observer, stable-pressure alignment and duplicate exclusion. After the merged gates:

1. Run the 11 nominal pressures: 1, 2, 3.5, 4, 5, 6, 7, 8, 9, 11 and 13 bar.
2. Add 0.25-bar spacing from 5.0 to 8.0 bar, skipping nominal duplicates: 9 new runs, 20 distinct pressures total.
3. Only if the window's sampled peak lies within 0.25 bar of either end, extend once by 1 bar in that direction at the same spacing. This adds 3 new runs (4 or 9 bar is already nominal); maximum 23 pressures.

Report the continuous solver peak by quadratic interpolation through the highest point and its two neighbours. Require a concave, bracketed vertex; otherwise report unresolved, without extrapolation or further automatic sweeps. Grades use the nominal grid. Keep all 56 measured-history runs in the same 11 conditions; never average histories before evolution.

## Acceptance

This is a **capability demonstration, not validation**. Retain the scorecard bands:

- Accuracy versus the saved B0c B1: MEETS for TIE/BETTER using the ±0.25 g/s paired band; NEAR for UNRESOLVED with lower endpoint RMSE. Require MEETS or NEAR.
- Slope at ≥9 bar: require MEETS, with a wholly negative interval overlapping [−0.0880, −0.0403] g/s/bar.
- Nominal peak: MEETS if its interval overlaps 5–7 bar; NEAR if it overlaps 4 or 8 bar but not 5–7. Require NEAR or better.

Report all criteria separately, trace RMSE on common time support, percentage change versus B1 and continuous solver peak versus observed 6.1 [5.9, 6.3] bar. Reconstruct B0c B1 from its saved fold coefficients; its accuracy grade is N/A (reference). Use condition-balanced paired whole-brew resampling of fixed predictions; no refitting or reuse of old refit intervals as solver uncertainty. Label zero-width constant-forcing intervals and target exposure explicitly. PHYSICAL_VALIDATION=NOT_ESTABLISHED.

## Delivery and housekeeping

Target two implementation PRs after this plan: (1) optional closure, pin compatibility and verification; (2) demonstration and capability report. In implementation PR 1, update `dependencies/puckworks.lock.json` from fc61c4670ec7bf801e40bb391aab16048b8da26b to current Puckworks main, **ba35a3bf1f832cd651fe98eebd59860849c0e850**, and its tree.

Static lock conflicts: `scripts/{r1_contract_bridge,wp02_contract_bridge,analyze_r1,verify_wp03_evidence_review,validate_sci_md_011,sci_md_011_execute,val_case_001}.py` and `tests/{test_reference_case,test_r1_bridge,test_r1_analysis}.py`. Historical consumers retain their original pins/results. Waszkiewicz runtime code and numerical CSVs are unchanged across the update. EWP's historical NumPy/SciPy pins conflict with Puckworks' declared dependencies; use a separate compatible environment. PR 1 CI must list further breakage; no execution audit occurs here.

## Estimates

Planning allowances: 250–450 changed/new C++ lines, plus adapters/tests; 2–6 minutes per 100-s base case at 0.020 s on 32 ranks, based on existing full-mesh timings with contingency.

Schedule 15 verification/control runs: 11 G1, 3 G2 time-step cases and 1 off-mode control. Add 20–23 constant-pressure cases and 56 histories: 76–79 demonstration runs, **91–94 total runs**. Assume applicable mesh/MPI qualification is reusable; PR 1 must identify additional required runs before scheduling.

Weight refinement at 1×, 2× and 4× base runtime; conservatively charge each 1D case as a full base case: **95–98 base-case equivalents**, **3.2–9.8 node-hours (32-core equivalents)**, **101–314 core-hours**. Wall-clock: **3.2–9.8 hours with one 32-rank case at a time**, or **1.6–5.0 hours with two concurrent 32-rank cases** (64 cores), excluding review/merge waits and additional qualification runs.

Hardware: state the machine and rank count actually available before the first verification run; estimates assume 32 ranks.

Measure one verification case before scheduling the batch. Two implementation PRs; no solver runs in this plan PR.

## Limits and sources

Out of scope: refitting, new mechanisms, restart effects, chemistry/extraction changes and the full Visualizer corpus.

- The 1D-to-axisymmetric difference may move the peak.
- E1's predictive onset law may not carry over cleanly to the wetting front.
- Median transfer loses fold covariance; tau reaches its lower bound.
- Raw-line forcing, hydraulic mass-flow mapping and R0 geometry remain conditional.
- Dependency adoption must not relabel historical evidence.

Inspected saved artifacts, code and data guides; no raw-source audit/runs. Use Waszkiewicz CC-BY-4.0 aggregates ([Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315)): `waszkiewicz2025/traces_per_brew` and `equilibrium_windows`. Sources: [scorecard][scorecard], [B0c][b0c], [Python E1][python], [EWP specification](../MODEL_SPECIFICATION.md), [numerical tolerances](../NUMERICAL_HARDENING_SPECIFICATION_V0_1_3.md), [balances](../../scripts/postprocess.py) and [runtime precedent](../../validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json).

[scorecard]: https://github.com/trbrewer/puckworks/blob/ba35a3bf1f832cd651fe98eebd59860849c0e850/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
[b0c]: https://github.com/trbrewer/puckworks/blob/ba35a3bf1f832cd651fe98eebd59860849c0e850/docs/research/PRESSURE_PEAK_STAGE_B0C/RESULT_TABLE.csv
[python]: https://github.com/trbrewer/puckworks/blob/ba35a3bf1f832cd651fe98eebd59860849c0e850/puckworks/analysis/pressure_peak_stage_b0.py
