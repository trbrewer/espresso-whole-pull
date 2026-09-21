# SCI-MD-RHEOLOGY-003: viscosity-law robustness

G1; SOURCE_SCENARIO_CHANGE_ONLY under the owner's SCI-MD-RHEOLOGY-003 directive.
The live minimum necessary governance standard classifies selection of scientific
inputs through an unchanged production interface as G1. One branch, issue and PR;
no merge, production/default/runtime-lock change, laboratory action or successor.
Implementation/QA, execution, science, independent review, hosted CI and merge
are separate statuses. Prior 001/002 results are known comparison evidence,
not an unseen holdout. There is no physical or fresh-espresso validation claim.

## Preflight and scientific decision

Fetched main is d40e0e64316d57dd4b685089daf07e3a13a11974, tree
ebf8c0b78fda04f182ddae52968eab6002dbf768, exactly the accepted PR #152 integration;
there are no later changes. Existing owner work remains untouched. Analysis
Puckworks is an isolated clean detached checkout at
2058d0e947ee9eb92c52d64f6165b810f1fb4732, tree
a6ffb312473b15be43c1571a893b19873ea47c5a. Runtime lock remains
fc61c4670ec7bf801e40bb391aab16048b8da26b.

New information: direct native coupled trajectories under declared constitutive
shape changes cannot be inferred from the prior fixed-law runs. Positive outcome
closes this finite robustness question and retains optional coupling only for
separately authorized development. A below-threshold alternative preserves explicit
law dependence. Unqualified branches limit the conclusion. This constrains the
transport/hydraulic part of grinder-to-cup development without reopening inventory,
E2C or Visualizer questions. Lower-cost reuse supplies W and TR_LINEAR. No repeated
species-inventory blocker or new data collection is implicated.

Scoped availability: accepted TR loader and water adapter, Sobolik card, README
provenance, Eq5 computed CSV and Fig3 Weisser digitization are available. Existing
001 source-use authority is reused and SOURCE_USE.json extends it. No whole-corpus
intake. Accepted 002 W/C/N artifacts exist; REUSE.json binds their hashes and exact
metric reproduction. The original full-run executable and accepted parser-corrected
executable have different hashes. The documented POST_RESULT_AMENDMENT permits
valid-table reuse; we use the corrected executable for new runs and preserve the
original identity for historical runs. Foundation OpenFOAM 12 is available.

## Frozen laws and source interpretation

Exactly TR_LINEAR, TR_DELAYED, TR_EARLY, SW_WATER_ANCHORED_90C; no parameter search,
ranking or post-result selection. T=363.15 K (90 C), rho_water=965 kg/m3. Water
viscosity is the accepted adapter's full-precision result. Native w=c/(965+c),
where c is aggregate dissolved mass per pore-water volume. No outlet-TDS proxy,
water percentage substitution, bulk-volume basis or density closure.

TR_LINEAR is exactly the accepted measured interpolation over [0.10,0.24], with
linear continuation from water below .10. It is reused, never replaced by the
published TR regression. For x=w/.10 below .10, DELAYED uses x^2 and EARLY uses
2x-x^2 in mu=mu_water+(mu_10-mu_water)*shape. Both preserve the measured segment
exactly and share endpoints. Positivity and monotonicity are checked, not assumed.
These are deliberate continuation stresses, not confidence limits, measurements,
or bounds on every plausible law. TR measured source is industrial extract.

Sobolik Eq5 is exp(-12.96-9.43*w+8.12*w*w+(1789+4382*w)/(T_C+273.15)) Pa.s.
It is a fit to Weisser, with recorded source range w=0–.5 and about 0–80 C.
The tested law is mu_water*f(w,90)/f(0,90). Mandatory interpretation:
**alternative source-derived concentration shape; water-anchored model adaptation,
not the literal published absolute law; temperature extrapolation to 90 C;
industrial/reconstituted-coffee material transfer; not independent espresso
validation.** Water normalization is fixed before EWP output and has no flow fit.
Eq5 and Fig3 digitization are one lineage, not two confirmations. Equation-generated
CSV values are not new measurements. Eq4 and other viscosity/density conversions
are excluded. EXPORT.json reports raw water value and normalization factor.

All laws reject native states outside [0,.24]; no clipping/domain expansion.
The native w<.10 diagnostic threshold remains unchanged. For SW, temperature
extrapolation labels apply across the curve. A dilute resistance fraction is not
a universal measured-support fraction. Historical observe-mode viscosities are
diagnostic table viscosities, not necessarily the applied hydraulic viscosity.

## Property qualification

Base knots every .001 on [0,.24]; refined every .0005, plus 0,.10,.24 and all
accepted TR breakpoints, deterministically deduplicated/sorted. B/C preserve the
measured segment. Tables use the unchanged native header/parser and remain external.
Dense fixed grid: 240001 uniformly spaced points plus knots and +/-1e-12 boundary
neighbours inside the domain. Check continuous law versus table <=1e-4 relative,
native versus Python table <=1e-12, endpoints/extrema, positivity, monotonicity,
and exact TR measured-segment preservation. Monotonicity allows only 1e-14 relative
floating-roundoff noise at duplicate-neighbour roundtrips (the first property
qualification flagged a 1.63e-18 Pa.s subtraction at a nearly duplicate point;
its retained output was not a scientific run). The actual native c-to-w roundtrip
is included. Bind source, exporter, law, evaluator and table hashes.

Eq5 reproduction is separately in its original recorded 0–80 C domain: all 486
CSV rows within 5e-9+1e-15 Pa.s, justified by half of the CSV's 1e-8 decimal
rounding unit plus floating arithmetic. The adapted 90 C evaluation is separately
labelled extrapolation. Property error is not a rigorous coupled-output bound;
property refinement supplies the separate empirical output term.

## Scenarios, invariant and bounded matrix

Use exactly 001 SCENARIOS.json uniform_9bar and reversed_3bar and 002 scenario()
without physical changes. Initial state, 0.0056 kg inventory, rate .15/s, capacity
180 kg/m3, diffusion 1e-9 m2/s, geometry, porosity, permeability and boundaries
remain identical. Full interval 0–30 s includes the first physical interval.
Base: 512 axial x 4 radial, dt=.02; temporal: same mesh, dt=.01; spatial: 1024 x 4,
dt=.02; property: base mesh/dt with refined table. Three new laws x two conditions
x four sets = 24 full attempts maximum, including failures. Only new coupled C
runs evolve their own concentration/inventory. No frozen-field forcing.

Reuse 002 W/C/N base/temporal/spatial by accepted manifest, preserving amendments.
Recompute baseline metrics exactly against committed METRICS.json. Property set
uses base W and base TR comparator. For each new law and set,
alpha=sum(C_uniform native volume)/sum(W_uniform native volume). Transfer never
enters calibration; alpha is held for both conditions. Q_N=alpha*Q_W,
mu_N=mu_water/alpha. Reference volume equality is calibration only. Algebraic N
has **hydraulics only**: no concentration, inventory, solute, TDS or old N chemistry.

Code invariant: static saturated Darcy hydraulicMobility=permeability/constant_mu;
only aggregateCoupled changes it using concentration. Constant-mu observe mode
leaves this coefficient unchanged. The linear pressure operator and pressure
matrix flux therefore scale uniformly. Accepted 002 multiplier evidence is reused.
Exactly four short checks (base/spatial x both conditions) use 2*mu_water,
0–.2 s, dt=.02, comparing all ten intervals to .5*matching accepted W;
max relative discrepancy <=1e-6. These are separate from the 24-run ledger.
Failed invariant/reuse does not authorize a native N campaign or predecessor replay.

FREEZE.json binds laws/scenarios/receipts/code/settings and executable/tables.
Independent pre-scoring PASS bound to this exact freeze is required by runner.
No full run until short invariant checks pass. Ledger STARTED is appended/fsynced
before each invocation, failed attempts remain counted and directories preserved;
no overwriting/retry. Roots are explicit CLI arguments, external to Git. No pilot
sweep, changed production interface, or extra scientific runs are authorized.

## Metrics and gates

E_int=sum(abs(Q_C-Q_R)*dt)/sum(Q_R*dt); E_peak=max(abs(Q_C-Q_R)/Q_R).
R is matching W or set-specific algebraic N. Reject missing/duplicated/noncontiguous/
mismatched/nonfinite intervals or nonpositive flow/denominator/dt. Thresholds .05
integrated, .10 peak. Also report matched C_new/C_TR_LINEAR flow errors with TR
as denominator; these quantify effect spread, never source accuracy or ranking.

Each new-law metric empirical estimate is absolute temporal change + absolute
spatial change + absolute property-table change + maximum across sets of
abs(Q_native-Q_cont)/Q_W (divided by minimum set alpha for C/N), inheriting 002's
operator allowance. Recalibrate alpha in every set. Separately report alpha-only
propagation on base data; never add it again. Exact discrete integration has zero
sampling/quadrature error; continuous-time error is assessed by timestep change.
These are empirical estimates, not confidence intervals or rigorous PDE bounds.
Total <=.005. Material only if E-u>=threshold; below only if E+u<threshold;
otherwise unresolved. Comparison material if either metric is qualified material,
below if both below, otherwise unresolved. Any required numerical/source gate
failure prevents a global robustness label.

Inherited gates on every run: max water/solute balance <=1e-8 kg; correction mass
sum <=1e-10 kg; accepted c>=-1e-10 and c<=180+1e-8 kg/m3; remaining inventory
>=-1e-12 kg; native volume versus Q*dt <=1e-15 m3. Native raw-negative rejection
remains unchanged. Source-domain failures and numerical-state failures are distinct.
Record actual C water/solute/beverage, stored/remaining mass, inlet loss, TDS,
local c/w/mu extrema, Courant, dilute volume and resistance fractions as secondary
unvalidated model outputs only.

All four laws qualified material C/N in both conditions gives
ROBUST_ACROSS_TESTED_VISCOSITY_LAWS. If baseline material but an alternative is
qualified below in a condition, SOURCE_OR_CONTINUATION_SENSITIVE identifies that
contrast. Any unqualified required branch gives SOURCE_DOMAIN_OR_NUMERICAL_UNRESOLVED,
retaining completed results. Per-condition small effect/static sufficiency remain
visible. TR continuation sensitivity and SW source-shape sensitivity are separate;
none is measured uncertainty, universal robustness or fresh-espresso validation.

## Reproduction and handoff

See README.md for implemented CLI commands and external artifact requirements.
Full science stays out of ordinary CI. Unit tests, repository checks, independent
pre-scoring audit, final result review and hosted CI are reported separately.
No merge, default adoption, laboratory action or automatic successor.
