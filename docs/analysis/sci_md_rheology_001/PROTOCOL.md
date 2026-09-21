# SCI-MD-RHEOLOGY-001 frozen contract

G1; SOURCE_SCENARIO_CHANGE_ONLY. No production-governing-physics change.
Owner task SCI-MD-RHEOLOGY-001 authorizes this bounded implementation, audit,
computation and one unmerged EWP PR. No protected comparison or holdout is used.
The independent pre-result audit must pass against FREEZE.json before solver
invocation or scientific analysis. Synthetic unit tests are not scientific results.

## Authority and novelty preflight

EWP base ac49fe939f9e7fb38ba4eabc95d65e2fa47ee666, tree
a7bbbc2963bdf89c183892749797c4530c713dc3 (origin/main, clean).
The original EWP checkout was clean on research/sci-md-011-high-pressure-poroelastic-closure,
78cbd59c751393cddfe539e4c69e43a224329bca, tree
b23347e33c67576b786922762eae168bf06b28fa; it is untouched.
Analysis Puckworks: detached clean local clone of 2058d0e947ee9eb92c52d64f6165b810f1fb4732,
tree a6ffb312473b15be43c1571a893b19873ea47c5a; source checkout main was clean.
The EWP runtime lock remains fc61c4670ec7bf801e40bb391aab16048b8da26b.

Reviewed current instructions, available-data policy/register/MANIFEST, Telis-Romero
card and provenance, G10 implementation/tests, EWP ledger/opportunity matrix,
SCI-MD-010/011/012 results, and the enduring private Visualizer record. G10 used
LOCAL Cameron concentration profiles, uniform-permeability depth averaging,
90 C, four grind/pressure/dose/yield conditions and a dilute-to-water extension.
Its recorded primary integrated suppression was approximately 2.75% or less;
its doubled-excess test permits up to 8%, with a comment reporting about 5.3%.
Those are prior recorded results, not reruns here. Its density iteration and
concentrated-cell clipping cannot be transferred to this EWP adapter.

New information: EWP aggregate-solute mass accounting, static layer resistance
weighting and residual error after ONE reference-only constant factor. Neither
G10's sampled Cameron fields nor SCI-MD-010/011/012 nor the Visualizer work bound
this metric over this EWP matrix. The EWP capacity cap alone permits mass fractions
up to 180/(965+180), above the dilute edge: it is not an analytical small-effect
bound. No NO_NEW_INFORMATION disposition is justified by those bounds.
This does not reopen their hydraulic/chemistry/Visualizer decisions.

Decision consequence: small or scale-removable effects retain constant viscosity;
robust residual effects warrant only a proposed smallest coupled test; unsupported
transfer is reported explicitly. This tests whether another hydraulic state law
merits development toward integrated extraction. It does not address the repeated
species-inventory blocker and requests no new data or laboratory work.

## Source and concentration contract

Use only authoritative Puckworks data.telisromero_eta_measured(T_K,Xw_pct), whose
output is Pa.s (1 mPa.s = 0.001 Pa.s), with explicit domain checks before calling
its internally clamping implementation. T_K = T_C + 273.15. Newtonian measured box:
295–365 K and 76–90 percent water, i.e. 10–24% wet-basis solids; interior evaluations
are bilinear interpolation. Below 10% solids, linearly extend from the measured
90% water edge to pure water, exactly the G10 modelling assumption on the EWP
mass basis. Above 24%, reject, including the unsupported 24–36% gap and power-law
regime; do not use K as Newtonian viscosity. No silent clipping.

EWP source initializes dissolvedConcentration=0, remainingExtractable uniformly
from dryDose*initialFraction/fullMeshVolume. Retained dissolved mass is
porosity*saturation*c*V, retained water is rho_water*porosity*saturation*V.
Outlet solute rate is Q*c; instantaneous TDS = soluteRate/(rho_water*Q+soluteRate),
cumulative TDS = cupSolute/(cupWater+cupSolute). Therefore w=c/(rho_water+c).
Only the single_effective_solute_first_order_with_capacity_ceiling model is eligible;
indexed species are rejected, even though their sum uses the same field name.
This is an accounting convention, not thermodynamic volume consistency.
Keep rho_water=965 kg/m3 from R0; change neither density accounting nor physics.
Use existing Pannusch water_viscosity(363.15 K) consistently in inputs and analysis.

Primary: measured interpolation plus explicitly labelled dilute extension.
Stress: mu_water + 2*(mu_primary-mu_water), a modelling stress assumption, NOT
an independent dataset, confidence interval or established uncertainty bound.
Source is one industrial soluble-coffee extract batch, not fresh espresso liquor;
composition and pressure transfer remain unqualified. Dilute results inform
computational priority only. Source tables, article, rheograms and raw data are
not copied into EWP. Compact derived hydraulic summaries only are redistributed.

## Exact matrix and reduction

SCENARIOS.json is the exact machine-readable six-case input authority. Uniform,
verified axial layers, and reversed layers, each at prescribed puck-face 3 and
9 bar; zero outlet gauge pressure, fixed 90 C. No machine interpretation.
R0 geometry (58 mm diameter, 0.009011660896432553 m depth), 20 g dry dose,
porosity 0.4, total soluble inventory 0.0056 kg, rate 0.15/s, capacity 180 kg/m3,
diffusivity 1e-9 m2/s. No fit. Initial saturation 1, front at bed end, c=0.
Static Darcy, no mechanics, inertia, radial heterogeneity or density feedback.

The existing fixture has equal-length layers k=7.5e-16 and 3e-15 m2; uniform
k=L/sum(L_i/k_i)=1.2e-15 m2. Reverse length AND permeability assignments.
These are synthetic scenario inputs, not inferred wet-puck properties.
Use maintained prepare_case.py, blockMesh and OpenFOAM postProcess cell-centre/
volume exporters, then unchanged espressoWholePullFoam. Six distinct executions;
no concentration-field reuse. Raw case inputs/logs/fields/build stay outside Git.

Primary mesh 512 axial x 4 radial x 1 azimuthal cells, uniform grading, 5-degree
straight-sided wedge; dt=0.02 s; output every 0.1 s through exactly 30 s.
No cup-mass stopping (target metadata set out of reach at 100 kg). Initial t=0
state is exactly c=0 and water resistance, not a first-drip alignment.
Only positive-flow 0–30 s is analyzed; initial hydraulic output is checked using
actual solved trace rows. ASCII double precision fields.

Group actual cell x centres, verify transverse concentration/permeability/porosity/
saturation invariance and radial/axial velocity ratio <=1e-7; derive dz from actual
cell volumes. Full-area conversion uses existing 2*pi/sin(wedgeAngle), not 360/angle.
Check centres, sum(dz)=L and full area pi*r^2; nonuniform thickness is supported.
Require static k, porosity=0.4, saturation=1. Verify every EWP outlet-flow trace row
against the maintained discrete_layered_pressure_reference to relative 1e-6.
Separately require continuum Q0 versus actual flow discrepancy <=0.1%. Include
that observed discrepancy conservatively in BOTH reported metric uncertainties.
EWP's unchanged arithmetic face mobility has an analytically known interface bias;
512/1024 axial cells reduce it without changing any interpolation or equation.
Failure of either hydraulic gate blocks scientific classification.

R_mu=sum(mu_i*dz_i/k_i)/A [Pa.s/m3]; Q_mu=DeltaP/R_mu [m3/s].
R0=mu_water*sum(dz_i/k_i)/A; Q0=DeltaP/R0. Each variant gets one alpha =
trapz(Q_mu_uniform_9bar,t)/trapz(Q0_uniform_9bar,t), fixed for ALL times and cases.
Q_null=alpha*Q0. Report absolute and residual E_integrated=trapz(abs(Q-Qref))/trapz(Qref)
and E_peak=max(abs(Q-Qref)/Qref). No signed cancellation or per-case scaling.

Report alpha, R histories, concentration and resistance-weighted mean viscosity
ranges, measured/dilute cell occupancy AND fractions of total hydraulic resistance,
upstream resistance contribution, and reversed-minus-original layer errors.
Pure-water t=0 has no source-transfer contribution; subsequent dilute cells are
explicitly flagged. Q_mu uses frozen concentration fields; its integral is NOT a
predicted cup mass, extraction yield or first-drip shift.

## Decision and numerical gates

Material if integrated >=5% OR peak >=10% for this owner-selected screen.
Categories: NO_NEW_INFORMATION (preflight only); SMALL_WITHIN_TESTED_ENVELOPE;
STATIC_SCALE_SUFFICIENT; STATE_DEPENDENT_EFFECT; SOURCE_OR_MAPPING_LIMITED.
SOURCE_OR_MAPPING_LIMITED is reserved for preflight/domain rejection or an
unresolved aggregate mapping, and for any claim of physical espresso qualification
(which this task explicitly excludes). Dilute occupancy alone does not trigger it:
the owner explicitly authorizes this extension for computational prioritization.
Domain rejection blocks computation and is reported manually with the exact input;
no post-result data-dependent support threshold is selected.
Classify primary and stress separately. Stress-only materiality is stress-dependent.
Measured/dilute support qualifies every conclusion; no physical validation.

At most six primary and six additional solver invocations (failures count).
Separate temporal (dt=.01, sampling=.05) and spatial (1024 axial, same dt/sampling)
refinements on uniform_9bar and layered_3bar: four invocations. Up to two more on
the scenario with largest primary-or-stress residual threshold-normalized metric
max(Eint/.05,Epeak/.10), if it is neither representative. Ties sorted by scenario ID.
Recompute reference alpha when refining reference; assess its propagated metric
change across ALL primary cases; retain reference-alpha propagation in uncertainty.
For each metric use a conservative empirical numerical estimate: maximum temporal
change + maximum spatial change + maximum 0.1-versus-0.2 s decimation change,
over checked cases and alpha propagation, PLUS the largest observed continuum/discrete
water-flow discrepancy. Sampling allowance is the larger of .1-versus-.2 and
.05-versus-.1 s changes in the refined runs. Report E_peak changes at .05 vs .1 s explicitly.
This is a resolution estimate, not a statistical confidence interval or rigorous
PDE error bound. Require <0.5 percentage points for each error metric. A threshold
within this estimate is unresolved. No extra sweeps if budget or uncertainty fails.

## Reproduction

After independent PASS receipt binds FREEZE.json:

```sh
python3 -m unittest tests.test_sci_md_rheology_001 -v
python3 scripts/run_sci_md_rheology_001.py --runs "$RUNS" --audit "$AUDIT" --executable "$EXE"
python3 scripts/sci_md_rheology_001.py analyze --puckworks "$PUCKWORKS" --runs "$RUNS" --output "$OUTPUT" --audit "$AUDIT"
# For each declared representative, separately:
python3 scripts/run_sci_md_rheology_001.py --runs "$RUNS" --audit "$AUDIT" --executable "$EXE" --case uniform_9bar --refine temporal
python3 scripts/run_sci_md_rheology_001.py --runs "$RUNS" --audit "$AUDIT" --executable "$EXE" --case uniform_9bar --refine spatial
```

Source the installed Foundation OpenFOAM 12 environment first. Build unchanged
solver into a task-local FOAM_USER_APPBIN with wmake if executable identity cannot
be tied to this source. Record source/build/executable hashes before invocation.
Run the same two refinement commands for layered_3bar and, if required, the selected
largest residual case. The initial analyze command writes PRIMARY_SCREEN.json only;
it is preliminary, with no classification. Then apply all numerical gates:

```sh
python3 scripts/report_sci_md_rheology_001.py --puckworks "$PUCKWORKS" --runs "$RUNS" --output "$OUTPUT" --audit "$AUDIT"
```

This writes final METRICS.json/CSV, NUMERICAL.json, histories and figures. Only
compact reduced outputs may go into the task's docs directory; raw products
remain external. AUTHORITY.json freezes executable/build/source/environment and
the per-artifact rights review at the analysis pin; MANIFEST.json is the final
execution/output inventory. The audit checks frozen source identities as well as
file hashes. No new solver run or scientific score occurred before this amendment. Keep raw output paths explicit and outside Git.
If audit or environment is unavailable, report IMPLEMENTED_NOT_EXECUTED separately
from scientific status NOT_ADJUDICATED. No successor or merge is authorized.

## Pre-result audit amendment

Independent AI review identified that the initial 64-cell continuum-versus-discrete
1e-6 comparison was unsatisfiable for the layered inputs. The remedy retains the
owner's continuum integral as the scientific response, adds the existing exact
discrete comparator as a solver check and reduces the known mesh interface bias.
No production scheme or default changes. All changes preceded scientific execution.
The same review's reproduction, support-status, sampling and provenance findings
are addressed above; there is no new governance stage or successor.
