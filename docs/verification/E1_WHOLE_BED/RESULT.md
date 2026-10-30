# E1 implementation verification

G2 governance class / GOVERNING_PHYSICS_CHANGE, opt-in only. The current
refinement correction changes no solver equation, parameter or tolerance.
G1 and the owner-approved finer G2 meet their numerical limits locally;
owner review and a merged implementation PR remain required before demonstration.
This is numerical verification, not physical validation. PHYSICAL_VALIDATION=NOT_ESTABLISHED.

## Scope and identities

The merged plan is EWP main `0aac9b875f5dd9b3e415c821a1f9aa7e8250611b` (#217).
The solver source is unchanged from implementation commit `a96cc7e`.
Candidate executable SHA256: `a137622b5ac8f91f6d1ef85a97e04845f85ef7213e6c4dd936beb26a60096fdf`.
Main executable SHA256: `3de93829850829db53927e5a079a855d1c09922f238a3a330f5d01f32f9eb1fb`.
Puckworks source authority is `ba35a3bf1f832cd651fe98eebd59860849c0e850`.
OpenFOAM Foundation 12; AMD Threadripper 3990X, 64 physical cores / 128 logical
CPUs, 251 GiB RAM; 32 MPI ranks for G2 and one rank for the 1D G1 cases.
Private hostname, native fields, meshes, logs and complete case evidence remain outside Git.

Use inlet-boundary gauge pressure as the explicit equivalent of Python raw
line pressure. Compute one whole-bed multiplier uniformly across cells; M is
cumulative outlet liquid mass. No local-stress substitution, observed-onset
input, fitting, default change or chemistry change is made.

## G1: 1D limit

All 11 pressures reproduce the pinned Python endpoint within max(0.02 g/s, 5%).
R0 geometry, 64 axial cells and one radial cell, saturated initial state, 100 s,
0.020-s time step. Full precision is in [G1.csv](G1.csv).

| Pressure (bar) | Python (g/s) | Solver (g/s) | Absolute difference (g/s) | Gate |
|---|---|---|---|---|
| 1.0 | 0.376000906 | 0.375952853 | 4.80526118e-05 | PASS |
| 2.0 | 0.897868737 | 0.897783571 | 8.51668222e-05 | PASS |
| 3.5 | 1.466505828 | 1.466460716 | 4.51114005e-05 | PASS |
| 4.0 | 1.597415404 | 1.597380077 | 3.53272321e-05 | PASS |
| 5.0 | 1.777388450 | 1.777364163 | 2.42875253e-05 | PASS |
| 6.0 | 1.890673382 | 1.890654545 | 1.88364999e-05 | PASS |
| 7.0 | 1.959411083 | 1.959395030 | 1.60530875e-05 | PASS |
| 8.0 | 1.967344564 | 1.967328808 | 1.57556224e-05 | PASS |
| 9.0 | 1.946206480 | 1.946189921 | 1.65588578e-05 | PASS |
| 11.0 | 1.821918350 | 1.821896339 | 2.20111104e-05 | PASS |
| 13.0 | 1.643900120 | 1.643867926 | 3.21935122e-05 | PASS |

| Python E1 term | Active in the G1 solver setting |
|---|---|
| P=max(Praw,0), conductance aP | Yes: inlet gauge pressure drives Darcy flow |
| Whole-bed exp(-P/Pstar) | Yes: uniform effective permeability |
| Predictive d=c(Pearly/bar)^(-n) | Yes: fixed saved c,n and training-only early-pressure inputs |
| S=exp(-d/tau) | Yes: once through permeability and mass evolution, never an opening gate |
| R=exp(exp(-M/Mc)) | Yes: saved Mc, evolving outlet liquid mass |
| dM/dt=q, M(0)=0 | Yes: zero only at initialization; all final checkpoints have M>0 |

Each final checkpoint has d>0, 0<S<1, R>1 and M matching cumulative cup water
in grams to checkpoint write precision. Full saturation removes only front
propagation; it does not disable onset, swelling or delivered-mass resistance.

## G2: original triple and off-mode diagnosis

Same 100-s dry-front R0 fixture, 256 × 512 cells, 9-bar forcing with a 3-s
start-up ramp. The original 0.020/0.010/0.005-s E1-on failure is retained below.
All entries are relative percent differences against 0.005 s, except first-drip
differences in seconds. Coarse/fine limit: 0.5%; middle/fine: 0.25%.
The original E1-off triple is descriptive and ungraded.

| Quantity | ON coarse/fine | ON middle/fine | OFF coarse/fine | OFF middle/fine |
|---|---|---|---|---|
| Outlet flow | 0.0010709296 | 0.0004867467 | 0 | 0 |
| Cup water | 0.016307115 | 0.0097993037 | 0.0052474157 | 0.0052474157 |
| Cup solute | 8.3212092e-06 | 2.2215987e-06 | 5.8662535e-06 | 1.8437601e-06 |
| Cup beverage | 0.015714122 | 0.0094430621 | 0.0050401768 | 0.0050403354 |
| Stored water | 0 | 0 | 0 | 0 |
| Remaining extractable mass | 0.99295253 **FAIL** | 0.30425369 **FAIL** | 1.2214602 | 0.388651 |
| Dissolved-in-puck mass | 0.79560787 **FAIL** | 0.23182265 | 0.96417236 | 0.29194805 |
| Inlet backdiffusion | 0.010092029 | 0.0042274538 | 6.4494434e-07 | 1.9540504e-07 |
| First-drip difference (s) | 0 | 0 | 0 | 0 |

Observed order uses the signed formula
`p=log2((f_0.020-f_0.010)/(f_0.010-f_0.005))`, without an absolute-value rescue.

| Quantity | Original ON order | Original OFF order | Finer ON order | Finer OFF order |
|---|---|---|---|---|
| Remaining extractable mass | 1.178599 | 1.099511 | 0.813599 | 0.890395 |
| Dissolved-in-puck mass | 1.282124 | 1.203231 | 0.712047 | 0.789224 |

The extraction refinement error is **pre-existing**: the E1-off relative errors
are about as large as the E1-on errors, and both show roughly first-order
convergence. The endpoint remaining/dissolved inventories are small (full values
are retained in [G2_ENDPOINTS.csv](G2_ENDPOINTS.csv)); this does not change the limits.

At default dt=0.020 s, **all 417 numerical files are byte-identical**
between main and E1 off: traces plus final fields on all 32 ranks. No missing or
different files. Baseline and candidate were built from their corresponding
source; logs and wall times are not numerical-output comparisons.

## G2: owner-approved finer triple

Time steps are 0.005/0.0025/0.00125 s. All quantities meet the unchanged limits
in both modes. The original 0.005-s runs are reused with identical executable,
configuration and outputs. Differences below are relative percentages against
0.00125 s, except first drip (seconds).

| Quantity | ON coarse/fine | ON middle/fine | OFF coarse/fine | OFF middle/fine |
|---|---|---|---|---|
| Outlet flow | 0.00031611082 | 7.2890251e-05 | 0 | 0 |
| Cup water | 0.0057127934 | 0.00081341715 | 0.0026236388 | 1.7530501e-10 |
| Cup solute | 1.8707389e-06 | 5.6649771e-07 | 1.4216386e-06 | 1.8052212e-07 |
| Cup beverage | 0.0055051024 | 0.00078383412 | 0.0025200843 | 7.2899691e-09 |
| Stored water | 0 | 0 | 0 | 0 |
| Remaining extractable mass | 0.23872086 | 0.086568643 | 0.29925327 | 0.1048656 |
| Dissolved-in-puck mass | 0.18671192 | 0.070774446 | 0.23050761 | 0.084492458 |
| Inlet backdiffusion | 0.0028839929 | 0.0007545128 | 1.5103247e-07 | 5.2403096e-08 |
| First-drip difference (s) | 1.9539925e-14 | 1.9539925e-14 | 1.9539925e-14 | 1.9539925e-14 |

First-drip tolerance is 1e-8 s for off mode and max(0.005 s, 0.1% of fine-step
time) for E1 on. Liquid residual must be at most max(1e-9 kg, 1e-8 cumulative
inlet water); solute residual at most max(1e-10 kg, 1e-8 initial extractable
mass). All cases satisfy those limits, boundedness and monotonicity.
All first-drip times round to 4.7116961852319 s.

| Case | dt (s) | Wall (s) | Max liquid residual (kg) | Max solute residual (kg) | Balance/bounds |
|---|---|---|---|---|---|
| g2-base | 0.02 | 24.574 | 1.66533e-15 | 1.05063e-13 | PASS |
| g2-mid | 0.01 | 46.608 | 1.13798e-15 | 1.14416e-13 | PASS |
| g2-fine | 0.005 | 92.392 | 1.58207e-15 | 3.69346e-13 | PASS |
| off-baseline | 0.02 | 22.309 | 3.84415e-15 | 2.64962e-13 | PASS |
| off-candidate | 0.02 | 21.852 | 3.84415e-15 | 2.64962e-13 | PASS |
| off-mid | 0.01 | 41.751 | 3.80251e-15 | 1.99204e-13 | PASS |
| off-fine | 0.005 | 83.708 | 3.74006e-15 | 7.12284e-15 | PASS |
| on-finer-mid | 0.0025 | 174.608 | 1.15186e-15 | 1.13403e-11 | PASS |
| on-finer-fine | 0.00125 | 342.722 | 1.67921e-15 | 9.45608e-13 | PASS |
| off-finer-mid | 0.0025 | 164.327 | 3.15858e-14 | 1.76204e-11 | PASS |
| off-finer-fine | 0.00125 | 319.756 | 3.20577e-14 | 6.45412e-13 | PASS |
| concurrent-a | 0.0025 | 300.816 | 1.15186e-15 | 1.13403e-11 | PASS |
| concurrent-b | 0.0025 | 288.861 | 1.15186e-15 | 1.13403e-11 | PASS |

Full precision, tolerances and original dispositions are in
[G2_REFINEMENT.csv](G2_REFINEMENT.csv) and [G2_ENDPOINTS.csv](G2_ENDPOINTS.csv).
The existing uniform-Darcy mesh/MPI qualification is reused provisionally:
the closure adds no spatial heterogeneity or nonlinear pressure solve. This
PR adds the 1D reproduction, full-mesh time refinement and 32-rank off control;
it makes no claim of a new independent mesh/MPI campaign.

## Demonstration setting and cost

Record **0.0025 s** as the demonstration time step, conditional on owner review
and merge of implementation PR 1. The measured base fixture is verification,
not a constant-pressure demonstration case or a measured-history run.

Measured E1-on wall time at **0.0025 s, 32 ranks: 174.608205 s (2.910 minutes)**.
Two simultaneous copies of that exact fixture, each with 32 ranks pinned to
disjoint physical cores, took 300.816497 and
288.861099 s. Pair completion was 300.816584 s;
the measured slowdown is **72.28%** relative to
the isolated case. Launch skew was 0.000087 s.
Both traces are byte-identical to the isolated run. This measured result replaces
the provisional no-contention assumption and 10–30% slowdown allowance.

For 76–79 demonstration cases (20–23 constant-pressure cases plus 56 histories):
one 32-rank case at a time takes **3.686–3.832 hours**; two concurrent
32-rank cases on 64 cores take **3.175–3.307 hours** (38–39 pairs,
plus one isolated case for an odd total). Serial scheduling consumes
**3.686–3.832 node-hours in 32-core equivalents**, or
**117.96–122.61 core-hours**; concurrent scheduling consumes
**6.224–6.437 such node-hours**, or
**199.18–205.97 core-hours**. These are solver-wall extrapolations,
including solver field output but excluding mesh preparation and review waits.
The concurrency measurement is one pair; measured histories may require more
pressure iterations. No demonstration batch has been scheduled or run.

There are 24 completed native verification/control runs: 11 G1, 11 G2/control
cases (including the separate main executable baseline), and two concurrent
timing copies. Reused 0.005-s cases are counted once. The implementation adds
122 C++ lines (69 solver, 53 header).

## Compatibility and reproduction

The runtime pin advances from fc61c46 to ba35a3bf. Five historical consumers
(`r1_contract_bridge`, `wp02_contract_bridge`, `analyze_r1`, `val_case_001`,
`verify_wp03_evidence_review`) otherwise conflate current runtime authority with
their frozen source. A narrowly checked historical-lock projection retains
their exact old commit/tree; two current-runtime test assertions now use the
new identity. SCI-MD-011 already uses its own historical source and needs no
change. No historical numerical result is rewritten. The newer Puckworks
numerical dependencies use a separate environment from EWP's pinned CI stack.
The new verification entrypoints have executable modes and an explicit
numerical dependency allowlist entry; source manifest and package QA are synced.

The first complete Python suite ran 1704 tests, with four failures and 21 skips.
All four tests pass on main `0aac9b8`: category (a), caused by this branch.

| Test | Traceback summary and cause | Minimal correction |
|---|---|---|
| `test_sci_md_003_atlas.Tests.test_runtime_lock_and_no_solver_diff` | AssertionError: live lock hash `9ecfe284…` != historical `52b15cee…`; runtime pin adoption | Read the atlas result's lock at its historical commit; keep the original hash and exact full fc61c46 commit assertion |
| `test_sci_md_004_stage_a.StageA.test_allowed_paths_and_immutable_runtime_lock` | AssertionError: live lock bytes != frozen lock bytes; runtime pin adoption | Read the already bound Stage A historical lock; assert its exact full fc61c46 commit |
| `test_sci_md_rheology_001_imports.RheologyImportTests.test_original_audit_and_amended_hashes` | `"solver source changed" does not match "runtime lock changed"`; the pin guard now fires first | Isolate the solver-source guard with the recorded historical lock hash; the separate runtime-lock rejection test remains unchanged |
| `test_xsv_pressure_001.PressureHistory.test_validator` | `active rheology source differs from frozen contract solver/espressoWholePullFoam/espressoWholePullFoam.C`; E1 extends historical source | Verify the exact E1 implementation source and adopted lock, then check the historical source/lock at the merged plan base against unchanged historical hashes; mutation tests reject unrecognized edits |

The two historical-pin tests never read the live runtime lock. They assert
`fc61c4670ec7bf801e40bb391aab16048b8da26b` exactly. The separate test
`test_e1_whole_bed.E1Tests.test_runtime_and_historical_authorities_are_distinct`
asserts the live lock's exact full commit `ba35a3bf1f832cd651fe98eebd59860849c0e850`
and tree. No historical result, numerical datum or tolerance changes.

Reproduce with `scripts/e1_verification.py`: `g1`, then `g2-base` and
`g2-refine` (the retained initial failure), separate `off-baseline` and
`off-candidate` with their respective executables, then `off-diagnostic`,
`finer-on`, `finer-off`. Keep `--work` outside Git, supply the exact pinned
Puckworks checkout, and use 32 ranks for G2. The later phases require the saved
off-mode byte-identity result. Do not overwrite attempts or change tolerances.
For the concurrent measurement, prepare two copies of the 0.0025-s E1-on G2
fixture, then launch together with 32 ranks each and Open MPI rankfiles mapping
ranks to disjoint physical cores 0–31 and 32–63. Check actual rank affinities
before timing. Measure each native solver and the pair completion separately;
perform balance/boundedness checks after both native runs complete.

Saved parameter and early-pressure aggregates were inspected directly in
Puckworks B0c RESULT_TABLE.csv and ONSET.csv, not inferred from catalog metadata.
Attribution: Waszkiewicz et al. (2025), [Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315),
CC-BY-4.0; only saved parameter/pressure aggregates are consumed. No brew data
or GPL source is copied. External native evidence retains full local provenance.
