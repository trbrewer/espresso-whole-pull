# E1 solver capability plan

Plan only; G0 / NO_GOVERNING_PHYSICS_CHANGE. Implementation and runs require owner approval of this plan. This asks whether the saved pressure-peak E1 capability survives the EWP spatial solver. A favourable result supports a bounded demonstration; a shortfall ends this transfer without retuning. This is distinct from the older SCI-MD-010 model also named E1.

## Mechanism and transfer

Python B0c E1 is whole-bed compaction plus delivered-mass evolution with one predicted-delay multiplier:
`d = c(Pearly/bar)^(-n)`, `S = exp(-d/tau)`,
`q = a S P exp(-P/Pstar) / exp(exp(-M/Mc))`, `dM/dt = q`, `M(0)=0`.
Here P is nonnegative raw line pressure in bar, mass is g and flow is g/s. The three fitted hydraulic parameters are `a_g_s_bar`, `Pstar_bar`, `tau_s`; the three fixed, training-fold nuisance inputs are `Mc_fixed_g`, `onset_c_fixed_s`, `onset_n_fixed`. S is applied once inside both flow and mass evolution, not as a delayed opening gate.

Transfer the componentwise medians of the eleven saved RAW PRIMARY / T4 REFIT E1 fold records, at their full stored precision, unchanged. No solver-side refitting, geometry calibration or per-pressure adjustment. The displayed medians are a=3.1943760786055893, Pstar=7.198042583618237, tau=10.000000000000073, Mc=28.796822720157447, c=16.27460753496898, n=0.055467406876812564.

## Solver mapping

Add an opt-in E1 branch in `solver/espressoWholePullFoam/espressoWholePullFoam.C`: dictionary validation, state initialization, the WP02 permeability/mobility update locations, and outlet-flux accumulation. Put its equations in a small new `e1EffectivePermeability.H`; add case preparation and verification support in `scripts/prepare_case.py` and tests. Keep `poroelasticCompaction.H` unchanged and mutually exclusive with E1: its local stress law is a different closure.

Each cell carries the derived E1 permeability multiplier; shared checkpointed state holds M, predicted d and S. Broadcast whole-bed P and M, rather than inventing local swelling or local-pressure compaction. Convert a to SI permeability by `Ka = a*1e-3*mu*H/(rho*A*1e5)`; update M from the globally summed hydraulic outlet mass flux. Keep liquid storage and solute bookkeeping separate.

Retain the existing wetting-front integration and saturation-transition bookkeeping; activate E1 mobility in the saturated branch. Predicted d modifies conductance only and never sets first-drip time. **Measured onset is never an input.** Use B0c's pressure-only stable clock: Pearly is each history's median pressure at 0–2 s. Constant curves use the median of the eleven saved training-fold input interpolations, labelled INTERPOLATED_INPUTS. Raw pressure is an explicit capability forcing at the inlet, without an additional machine-loss correction; it is not a claim of line/bed pressure equivalence.

## Verification before data comparison

The scorecard's E1 replay was checked only at aggregate level; complete these checks before any data comparison.

1. Collapse to the fully saturated, uniform 1D Python setting, with M=0, the same fixed parameters, early-pressure inputs and 100-s clock. At all eleven nominal pressures require endpoint differences within max(0.02 g/s, 5% of Python flow).
2. Preserve existing liquid residual ≤max(1e-9 kg, 1e-8 cumulative inlet water) and solute residual ≤max(1e-10 kg, 1e-8 initial extractable mass), plus boundedness and unchanged off-mode regression checks.
3. Retain time steps 0.020, 0.010 and 0.005 s: coarse/fine differences ≤0.5%, intermediate/fine ≤0.25% for declared primary outputs; first-drip difference ≤1e-8 s. Check endpoint flow and inventories before scoring; keep applicable mesh/MPI checks.

## Demonstration

Use R0 geometry and the existing 100-s endpoint observer, stable-pressure alignment and duplicate exclusion. Run constant raw pressure at 1, 2, 3.5, 4, 5, 6, 7, 8, 9, 11 and 13 bar, then all 56 saved brew pressure histories within those eleven conditions; do not average histories before nonlinear evolution. Preserve the R0 dry-front initialization separately from the saturated 1D verification limit. Sample the constant-pressure solver curve on the 0.05-bar grid from 1 to 13 bar.

## Acceptance

This is a **capability demonstration, not validation**. Retain the scorecard bands:

- Accuracy versus the saved B0c B1: MEETS for TIE/BETTER using the ±0.25 g/s paired band; NEAR for UNRESOLVED with lower endpoint RMSE. Require MEETS or NEAR.
- Slope at ≥9 bar: require MEETS, with a wholly negative interval overlapping [−0.0880, −0.0403] g/s/bar.
- Nominal peak: MEETS if its interval overlaps 5–7 bar; NEAR if it overlaps 4 or 8 bar but not 5–7. Require NEAR or better.

Report all criteria separately, trace RMSE on common time support, percentage change versus B1 and continuous solver peak versus observed 6.1 [5.9, 6.3] bar. Reconstruct B0c B1 from its saved fold coefficients; its accuracy grade is N/A (reference). Use condition-balanced paired whole-brew resampling of fixed predictions; no refitting or reuse of old refit intervals as solver uncertainty. Label zero-width constant-forcing intervals and target exposure explicitly. PHYSICAL_VALIDATION=NOT_ESTABLISHED.

## Delivery, housekeeping and estimates

Target two implementation PRs after this plan: (1) optional closure, pin compatibility and verification; (2) demonstration and capability report. First update `dependencies/puckworks.lock.json` from fc61c4670ec7bf801e40bb391aab16048b8da26b to **ba35a3bf1f832cd651fe98eebd59860849c0e850** and its tree.

Static review identifies lock conflicts in `scripts/{r1_contract_bridge,wp02_contract_bridge,analyze_r1,verify_wp03_evidence_review,validate_sci_md_011,sci_md_011_execute,val_case_001}.py`, and runtime-lock assertions in `tests/{test_reference_case,test_r1_bridge,test_r1_analysis}.py`. Route historical consumers to their original pinned authorities; preserve their results. The Waszkiewicz runtime module and numerical CSV bytes are unchanged across the pin update. A pre-existing environment conflict also remains: EWP's historical NumPy/SciPy pins cannot install Puckworks' declared dependencies; use a separate compatible environment. First-PR CI must enumerate any further breakage; this plan performs no execution audit.

**Estimates (planning allowances, not measurements):** 250–450 changed/new C++ lines, plus adapters/tests. Allow 2–6 minutes per 100-s R0 case on 32 CPU ranks, scaling an existing 30-s full-mesh run of about 30 seconds with contingency. Budget roughly 400 base-case equivalents including 241 constant-pressure points, 56 histories, 1D checks and refinement: 13–40 node-hours, about 430–1,280 core-hours; around 7–20 hours with two concurrent 32-rank cases. Measure one verification case before scheduling the batch. Two implementation PRs; no solver runs in this plan PR.

## Limits and sources

Out of scope: refitting, new mechanisms, restart effects, chemistry/extraction changes and the full Visualizer corpus.

- The 1D-to-axisymmetric difference may move the peak.
- E1's predictive onset law may not carry over cleanly to the wetting front.
- Median transfer loses fold covariance; tau reaches its lower bound.
- Raw-line forcing, hydraulic mass-flow mapping and R0 geometry remain conditional.
- Dependency adoption must not relabel historical evidence.

Inspected code, saved scorecard/stage CSVs and summaries, EWP specification and data guides; no new raw-source audit or runs. Use only attributed Waszkiewicz CC-BY-4.0 aggregates ([Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315)); relevant datasets are `waszkiewicz2025/traces_per_brew` and `equilibrium_windows`. Sources: Puckworks [scorecard][scorecard], [B0c][b0c] and [Python E1][python]; EWP [model specification](../MODEL_SPECIFICATION.md), [numerical tolerances](../NUMERICAL_HARDENING_SPECIFICATION_V0_1_3.md), [balance implementation](../../scripts/postprocess.py) and [runtime precedent](../../validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RESULTS.json).

[scorecard]: https://github.com/trbrewer/puckworks/blob/ba35a3bf1f832cd651fe98eebd59860849c0e850/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md
[b0c]: https://github.com/trbrewer/puckworks/blob/ba35a3bf1f832cd651fe98eebd59860849c0e850/docs/research/PRESSURE_PEAK_STAGE_B0C/RESULT_TABLE.csv
[python]: https://github.com/trbrewer/puckworks/blob/ba35a3bf1f832cd651fe98eebd59860849c0e850/puckworks/analysis/pressure_peak_stage_b0.py
