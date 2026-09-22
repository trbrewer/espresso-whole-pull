# SCI-MD-RHEOLOGY-009

G2 production boundary/coupling compatibility; NO_GOVERNING_PHYSICS_CHANGE,
NO_GOVERNING_EQUATION_CHANGE, PRODUCTION_BOUNDARY_BEHAVIOR_CHANGE. Existing
beginning-state viscosity and native right-endpoint pressure discretization are
preserved; no new numerical integration or constitutive law. The synthetic
scenario delta alone is SOURCE_SCENARIO_CHANGE_ONLY, not the overall task.
Issue #165. Baseline/fetched main 3960b4a9c4b05aa3f3cdec1dade33eb16c485d24,
tree 5b262e92a2d0f7ec5e3051bfa6671f9ac0d07fd8; no intervening main changes.
Clean isolated worktree; owner checkouts preserved. No merge/default adoption,
Puckworks change, retuning, E4/E8 rescue, laboratory action or successor.

NEW_INFORMATION: autonomous native E2 transfer under changing inlet pressure,
not inferable from constant-pressure results. POSITIVE: sufficiency only for
tested outputs/support; NEGATIVE: bounded transfer insufficiency; UNRESOLVED:
identify missing numerical/evidence gates, never tune. GRINDER_TO_CUP_LINK:
water allocation and mass-conditioned aggregate delivery. REPEATED_BLOCKER:
not the chemistry inventory or E2C identifiability lane. LOWER_COST_ALTERNATIVE:
reuse qualified source exports and accepted constant-pressure native references.
Existing available-data preflight and 003 SOURCE_USE/EXPORT apply; source tables,
register/cards and reference receipts are verified by prepare. No broad audit.
Synthetic histories are controlled inputs, not missing measurements.
Analysis Puckworks remains 2058d0e947ee9eb92c52d64f6165b810f1fb4732;
production dependency remains fc61c4670ec7bf801e40bb391aab16048b8da26b.

## Mathematical compatibility

Admit history only with local observe/coupled, static radial_two_zone,
fully saturated fresh zero-start Darcy, fixed rho=965 kg/m3 and T=363.15 K,
existing single aggregate-solute model. Reject bulk, mechanics, wetting,
evolving permeability, flow control, restart and unsupported configurations.
Native parser retains strict finite increasing complete schedules and legacy
scalar/ramp conflicts. Every pressure knot must exceed finite outlet pressure.
No dummy scalar target. Piecewise linear interpolation cannot undershoot a
positive knot minimum. mu_n=mu(c_n/(rho+c_n)); mobility_n=k/mu_n; solve pressure
with P(t_end). Native pressure-equation face flux drives both transport and
water: dV=Q_native dt; dW=rho dV. No U dot Sf or analytical water replacement.
Join native traces.csv time_s to radial end_s exactly in the existing 15-significant-digit trace serialization (reject key collisions), reject missing/duplicate
rows and wrong state clocks; compare applied pressure to independent interpolation.
No output schema change.

## Frozen experiment and support

R=.029 m, L=.009011660896432553 m, interface=.0145 m, porosity=.4,
dose=.020 kg, extractable=.0056 kg, ki=3e-15 m2, ko=7.5e-16 m2,
capacity=180 kg/m3, rate=.15/s, D=1e-9 m2/s. Initially dissolved c=0;
fixed k/porosity, zero-gauge outlet, saturated, 0–30 s, no early termination.
TR_LINEAR and SW_WATER_ANCHORED_90C plus accepted SW refined table, no fitting.
UP knots (seconds,Pa): (0,300000),(14.5,300000),(15.5,900000),(30,900000).
DOWN reverses the pressures. Equal continuous integrals do not imply equal
extraction or discrete endpoint-quadrature water. No alteration after outcomes.
C=64 radial; E2=2 radial, exactly aligned native interface, no extra area weights.
E2 evolves autonomously. Both base 512 axial dt=.02; temporal dt=.01; axial
1024 at dt=.02. C alone radial 128. SW property variant base/refined table.
18 C + 14 E2 primary; 16 legacy/flat-history controls =48 full slots, at most
4 identical infrastructure recovery attempts, never numerical/scientific rescue.
All starts/failures/completions retained. No undeclared profiles or refinements.

Before any E2 history science: complete and qualify all 18 C runs. Separately
for UP/DOWN use all nine C terminal B=W+S; B_star=.95 min(B_terminal), floor to
1e-9 kg with Decimal arithmetic. Seal/hash SUPPORT, same endpoint for both laws
and all refinements. Missing C blocks support. Candidate shortage leaves delivery
unresolved without shortening/extrapolation; retain hydraulic decisions.

## Qualification and decisions

Fourteen short runs at 32 axial, dt=.02, end=.2: each C/E2 constant viscosity
UP/DOWN, doubled viscosity UP, uniform-k UP (eight), then SW UP serial, independent
repeat and two-rank radial MPI (six). Knots [0,.065,.135,.2]. Synthetic tables
only for analytical fixtures. Analytical Q=pi R²(.25ki+.75ko)P/(mu L), shares
4/7 or 1/4; doubled mu halves Q. Water checked against discrete endpoint sum;
continuous integral and discrepancy reported independently. Geometry, final mass
aggregation and native interface exchange verified. Tolerances in CONTRACT.json
are inherited from 006/008 and XSV-PRESSURE-001, never loosened.
Six separately counted affected off-mode regression runs: accepted/new executable
pairs on short saturated radial constant, radial history, and unsaturated legacy.
All numerical trace columns checked, not just final mass. Full compatibility
compares eight new legacy traces with accepted native C/E2 and eight equivalent
flat histories with new legacy. Matched runtime identities recorded.

Q total native flow, s=Qi/Q, W/S native cumulative mass, B=W+S.
Six metrics and budgets use accepted 008 observer: E_Qint .01, E_Qpeak .02,
mean share 1 pp, peak share 2 pp, E_Spath .01, five-fraction max TDS .10 pp.
Hydraulics/allocation use all 0–30 s intervals. Delivery includes zero origin,
first interval and five equal-B fractions to fixed B_star, conservative native
increment splitting; path maximum over union of native mass breakpoints.
No smoothing, shift or instantaneous TDS interpolation. Metric allowances sum
paired temporal/base, paired axial/base, C-only radial/base with E2 fixed,
SW paired property/base, and independent 50-digit arithmetic discrepancy.
No E-versus-C effect counted as uncertainty. Empirical sensitivities only,
not statistical confidence intervals or rigorous continuum bounds.
PASS iff M+u<b; qualified FAIL iff M-u>b; equality/missing/invalid evidence,
straddling or u>.2b => UNRESOLVED. Four separate cases, 24 decisions, all must
PASS for success; a qualified FAIL prevents success despite unresolved siblings.

Run order: unit/short checks; freeze and genuine independent pre-scoring audit;
controls and regressions; C; sealed reference-only support; E2; analysis/figures;
ordinary final exact-head review. Self-review cannot supply audit approval.
Scientific contract changes invalidate affected evidence; no post-result changes.
Raw fields/traces, restricted sources, paths, logs and executables stay external.
Timings and cell counts are descriptive, not benchmark speedups.
TR dilute continuation and industrial-source transfer, SW water anchoring and
90 C extrapolation remain limitations. No arbitrary-profile/geometry/continuum,
wetting, whole-shot-beyond-support, mechanism-identification, experimental or
production-readiness claim. PHYSICAL_VALIDATION: NOT_ESTABLISHED.
