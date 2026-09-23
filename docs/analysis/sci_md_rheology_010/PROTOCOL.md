# SCI-MD-RHEOLOGY-010 — matched-conductance permeability reversal

Issue #168; G1 / SOURCE_SCENARIO_CHANGE_ONLY. Owner authorization is the task
instruction. Start main cba79537e177938b2607c2979344b13acb56a9f2, after accepted
009 #166 and discovery-only #167. One isolated branch and one unmerged PR.
No production solver, numerical method, constitutive law, default, source table,
production lock or Puckworks tracked change is authorized.

## Question and source roles

Does autonomous native E2 retain hydraulic, CORE outlet allocation and
mass-matched delivery accuracy when permeability contrast reverses at constant
bulk water conductance? Does resolved C delivery change materially at the same
beverage mass? E2 has TWO radial cells per axial station (1,024 base cells),
not two lumped states. C has 64 radial cells per axial station (32,768 base).
Both retain their own communicating pressure/transport solutions, without C-state
forcing, correction, fitting, extra area weights, smoothing or time alignment.

NEW_INFORMATION: this prescribed reversal is not answered by accepted 006–009.
POSITIVE changes the tested spatial scenario envelope and may establish a named
modeled delivery contrast. NEGATIVE restricts E2 to previously qualified cases;
UNRESOLVED names the numerical/support/evidence gap. GRINDER_TO_CUP_LINK:
spatial water allocation and conservative solute delivery. LOWER_COST_ALTERNATIVE:
reuse all 18 accepted 009 C variants, exports and executable, no control reruns.
REPEATED_BLOCKER: not chemistry inventory, E2C identifiability or exhausted
Visualizer transfer. No experimental targets or protected holdouts are scored;
source properties are accepted inputs, contextual experiments are not fitting data.
See SOURCE_USE.md; missing required properties/native reference evidence blocks.
A newly qualified direct experimental pairing that changes the premise stops
before full execution. Optional unavailable context is
KNOWN_EXTERNAL_UNAVAILABLE_HERE, never nonexistent or exhausted.

## Exactly one new scientific configuration

Keep accepted 009 geometry, inventory, source laws, temperature, pressure,
boundaries and numerical formulation. Only inner_permeability_m2 and
outer_permeability_m2 change, apart from external table locator rebinding.
f=(0.0145/0.029)^2=1/4; old ki=3e-15, ko=7.5e-16 m2;
kbar=f*ki+(1-f)*ko=1.3125e-15 m2. With r=1/4 construct
ko=kbar/(f*r+1-f)=(21/13)*1e-15 and ki=r*ko=(21/52)*1e-15 using
Decimal algebra, then serialize doubles. Never swap old numbers.
Q=pi*R²*kbar*DeltaP/(mu*L); constant-mu CORE share changes analytically
from 4/7 to 1/13. Water increments match at the same discrete pressure history.
This known allocation is not the scientific finding. Matching water conductance
prescribes neither solute nor beverage equality. Fixed unequal .25/.75 areas mean
this also changes the weighted permeability distribution and residence times;
it isolates neither radial position nor a unique lateral mechanism.

R=.029 m; L=.009011660896432553 m; interface=.0145 m; porosity=.4;
dry dose=.020 kg; extractable=.0056 kg; capacity=180 kg/m3; rate=.15/s;
diffusivity=1e-9 m2/s; rho=965 kg/m3; T=363.15 K; initially dissolved c=0;
fresh fully saturated static bed; zero-gauge outlet; 0–30 s with no early stop.
TR_LINEAR and SW_WATER_ANCHORED_90C use accepted exact table bytes, including
SW property refinement. Source analysis pin 2058d0e947ee9eb92c52d64f6165b810f1fb4732;
production pin fc61c4670ec7bf801e40bb391aab16048b8da26b. Discovery guide is separate.
UP (s,Pa): (0,300000),(14.5,300000),(15.5,900000),(30,900000).
DOWN: (0,900000),(14.5,900000),(15.5,300000),(30,300000).
Native P(t_end), mu(c_start), pressure-equation face fluxes and Q_native*dt
remain operative. No continuous-pressure-integral replacement of cup water.

## Qualification, freeze and execution

Exactly ten short integrations: for each C64 and E2, constant-mu UP, constant-mu
DOWN, coupled SW UP serial, independent identical repeat, two-rank radial MPI.
32 axial cells, dt=.02 s, end=.2 s, knots [0,.065,.135,.2]. Constant tables
are fixtures only. Check analytical Q, fixed CORE share and discrete water against
the same old/new oracle (no new old control). Inherit all 009 CONTRACT limits,
conservation, bounds, clocks, actual annular geometry, region assignment, final
field aggregation, repeat and MPI checks. Restricted transverse diagnostic is
excluded from scoring, allowances, provenance inference and mechanism claims.
No repair of that diagnostic. All final required fields retained externally.

After unit/short qualification, ONE freeze and ONE genuine independent
pre-scoring audit bind configuration, source/build/runtime, observers, all matrix
slots, support rule, budgets and decisions. Self-authored approval is forbidden;
unavailable independent audit stops full execution. Freeze before full C runs;
all 18 new C must complete and qualify before support seal and any E2 launch.
Reuse/reobserve all 18 old C by exact retained manifests and required field hashes.

Full new annulus-fast matrix: C TR x UP/DOWN x base/time/axial/radial =8;
C SW additionally property =10. E2 TR x UP/DOWN x base/time/axial=6;
E2 SW additionally property=8. Total 32 full +10 short=42 integrations.
Base 512 axial, dt=.02 s, C64/E2; temporal dt=.01; axial 1024;
C radial 128 (E2 stays base); SW property uses accepted refined table.
At most TWO extra identical attempts TOTAL for demonstrable infrastructure
interruption, never numerical/scientific failure or changed inputs. Append-only
ledger distinguishes preparation, every native launch (even startup failures),
integrating failure and completion. Preserve failed invocations. Postprocessing
corrections reuse native evidence, stay in this task and are disclosed.

## One new delivery support per history

For each history include all 18 qualified C terminal B=W+S: nine old core-fast
and nine new annulus-fast, both laws/all refinements. B_star = Decimal
floor_to_1e-9kg[.95*minimum]. Missing/invalid C variants block sealing; they
cannot disappear from the minimum. Seal/hash numerical endpoints after C
qualification and before any E2 launch/score. Same endpoint for both laws,
all refinements, primary and secondary. Never change historical 009 support.
Report every terminal mass and B_star/terminal coverage. E2 shortage makes
affected delivery UNRESOLVED, without shorter support, extrapolation, extension
or favorable crop; independently valid full-time hydraulics/allocation remain.

## Primary: 24 independent decisions

Accepted native observer and independent 50-digit arithmetic. E_Qint =
integral |QE-QC|dt / integral QC dt; E_Qpeak=max |QE-QC|/QC;
D_share_mean_pp=100 integral QC|sE-sC|dt/integral QC dt;
D_share_peak_pp=100 max|sE-sC|. s is always core Q_inner/Q_total.
Hydraulics/allocation use every native interval over 0–30 s.
E_Spath=max|SE(B)-SC(B)|/SC(B_star) over union of native mass breakpoints,
zero origin and endpoint. D_TDS_pp=max absolute fraction TDS difference across
five equal-B fractions. Include first increment; conservative splitting only.
Budgets respectively .01, .02, 1 pp, 2 pp, .01, .10 pp.

For each metric u sums absolute changes in metric under paired temporal,
paired axial, C-only radial with E2 held base, paired SW-property (zero for TR),
and maximum independent 50-digit arithmetic discrepancy across all variants.
No old allowances or E2-C discrepancy itself enters u. Empirical allowances
are neither confidence intervals nor rigorous continuum-error bounds.
Complete valid evidence and u<=.20*budget: PASS iff M+u<budget;
FAIL iff M-u>budget; otherwise UNRESOLVED. Equality, invalid/missing evidence,
nonfinite values or excessive u are UNRESOLVED. Use unrounded numbers.
Any qualified FAIL -> E2_CONDUCTANCE_MATCHED_REVERSAL_INSUFFICIENT;
all 24 PASS -> E2_CONDUCTANCE_MATCHED_REVERSAL_SUFFICIENT_FOR_TESTED_OUTPUTS;
otherwise E2_CONDUCTANCE_MATCHED_REVERSAL_UNRESOLVED. Unresolved siblings never
erase a qualified failure.

## Secondary: eight separate magnitude decisions

Compare NEW annulus-fast C to OLD core-fast C as reference at new B_star;
exact E_Spath and D_TDS_pp definitions, plus signed new-minus-old five-fraction
TDS differences. These are modeled differences, not approximation errors to truth.
u uses paired temporal, axial, BOTH-C radial and applicable SW-property refinements,
plus independent arithmetic. In particular never hold one C fixed for radial.
Thresholds .01 and .10 pp are engineering materiality budgets, not taste limits.
For valid complete evidence and u<=20% threshold: M-u>threshold ->
MATERIAL_MODELED_DELIVERY_CONTRAST; M+u<threshold ->
BELOW_DECLARED_MATERIALITY_BUDGET; otherwise UNRESOLVED. Equality/excessive
allowance/missing evidence unresolved. Report all eight separately. Materiality
supports only its named case/output; all eight below supports a bounded null;
otherwise no universal material/null statement. Never change primary status.

## Decision consequence and stop

Sufficient transfer plus qualified material contrast retains E2 as a candidate
for this additional spatial scenario with a modeled consequence. Any qualified
transfer failure restricts E2 to previously qualified cases without E4/E8 rescue.
Sufficient transfer but all delivery contrasts below budget establishes no
material consequence on tested support and motivates no arbitrary sweep.
Unresolved identifies the specific limitation without expanding the matrix.
A material C contrast neither validates experiment nor guarantees arbitrarily
small relative E2 contrast error. No analytically known share change counts as
solute materiality. Preserve TR dilute continuation/industrial-extract transfer,
SW water anchoring/90 C extrapolation and synthetic-reference limitations.

PHYSICAL_VALIDATION = NOT_ESTABLISHED. No unique lateral mechanism,
arbitrary geometry/permeability/history, whole-shot beyond support, two-state
lumped model, measured speedup or production-readiness claim. No default adoption,
merge, rescue, laboratory action, data acquisition/publication or successor.
Public-safe synthetic summaries/figures and compact receipts only in Git;
restricted tables, native traces/fields, binaries, paths and full logs external.
Ordinary independent exact-head final agent review is separate from protected
GitHub approval and external human review. Stop at one open PR handoff.
