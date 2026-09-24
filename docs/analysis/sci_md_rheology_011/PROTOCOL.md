# SCI-MD-RHEOLOGY-011 — distribution-preserving radial relocation

G2 / GEOMETRY_COMPATIBILITY_NO_GOVERNING_PHYSICS_CHANGE;
change declaration NO_GOVERNING_PHYSICS_CHANGE. Owner authorization is the
SCI-MD-RHEOLOGY-011 task directive. One open/unmerged PR; no default adoption,
merge, successor, fitting, new C++ or changed numerical operator.

Starting main is 63fd95e (010 merged as #169 after the observed cba7953).
The material delta adds 010 tools, results, tests and metadata; native solver,
009 evidence and production interfaces are unchanged. 010 changes both histogram
and placement and remains valid on its own terms. No equivalent 011 exists.

NEW_INFORMATION: resolved delivery under a previously untested relocation of
an unchanged permeability distribution. DECISION_IF_POSITIVE: test autonomous
E2 transfer on the complete declared conditional matrix. DECISION_IF_NEGATIVE:
close the qualified delivery null without E2. DECISION_IF_NULL_OR_BLOCKED:
report unresolved evidence without expanding the campaign. GRINDER_TO_CUP_LINK:
spatial material placement, water allocation and delivered solute.
REPEATED_BLOCKER: this computational comparison does not reopen experimental
inventory identifiability. LOWER_COST_ALTERNATIVE: reuse all 18 accepted 009 C
integrations; algebraic independent-path null needs no P integration.

## Fixed mathematics and geometry

A: R=.029 m, interface R/2=.0145 m; inner area .25 at kH=3e-15 m2,
outer .75 at kL=7.5e-16 m2. B: interface R*sqrt(3/4), computed with
80-digit Decimal arithmetic, converted once to binary64 and serialized by
Python repr (the properties writer retains its established 16 significant digits;
that native serialized value is recorded explicitly). Inner .75 at kL, outer
.25 at kH. kbar=1.3125e-15 m2. Both class areas, bed/pore volumes, uniform
dry mass and initial inventory allocations must match within native geometry
relative tolerance 1e-8 against actual oriented mesh measurements.

Schema is geometry.radial_mesh with exactly type=interface_aligned_two_zone,
inner_cells and outer_cells. Positive integer counts sum to radial_cells;
one azimuthal cell; uniform radial and axial grading, finite positive geometry,
0<interface<R, wedge in (0,5] degrees. Hydraulics supplies the only interface.
Explicit option requires fresh saturated static Darcy and local observe/coupled
viscosity with existing prescribed-pressure restrictions. Legacy rendering and
validation remain unchanged. Two conforming blocks share INTERNAL material faces;
no baffle, disconnected paths, wall, exchange coefficient or validation bypass.

C B base: 48 inner +16 outer, axial 512, dt .02 s. Radial refinement 96+32;
E2 exactly 1+1, axial 512, dt .02. Temporal .01 s; axial 1024; accepted SW
refined property table. Counts are fixed before scores, never optimized.
All other science is accepted 009: L=.009011660896432553 m, porosity .4,
dry dose .020 kg, M0=.0056 kg, c0=0, capacity 180 kg/m3, rate .15/s,
diffusivity 1e-9 m2/s, rho=965 kg/m3, T=363.15 K, fresh saturated bed,
zero-gauge outlet, full 0–30 s. TR_LINEAR and SW_WATER_ANCHORED_90C bytes
including the SW refinement are reused unchanged. UP times [0,14.5,15.5,30],
pressures [300000,300000,900000,900000]; DOWN reverses pressure values.
Beginning-step viscosity, end-step pressure, pressure-equation face fluxes and
native Q*dt water remain operative. No continuous-integral water replacement.

Constant mu: Q=pi R² kbar (Pin-Pout)/(mu L); high-k share 4/7 in both.
INNER share is 4/7 in A, 3/7 in B. Equal-k fixture INNER share .75.
State-dependent trajectories need not preserve these equalities. Independent
non-exchanging autonomous per-area paths give .25 F(kH)+.75 F(kL) under either
placement, an algebraic permutation null only. This leaves P's accepted
insufficiency unchanged. Native exports already carry full-basket extensive
quantities, so no additional area multiplication is permitted. B initial inner/
outer inventory bounds are .75 M0/.25 M0. Expectations come from the scenario,
never the reported native volumes being checked.

## Qualification, review and bounded execution

Exactly 14 short integrations: each C/E2 constant mu UP, constant mu DOWN,
double mu UP, equal kbar UP retaining radial_two_zone, coupled SW UP serial,
independent identical repeat, two-rank MPI. Axial 32, dt .02, end .2,
knots [0,.065,.135,.2]. Constant tables are fixtures only. Manual cell ownership
assigns each entire material zone to its own rank; nonempty ranks and all
material interface processor faces must be verified before integration.

All accepted 009 limits apply unchanged (CONTRACT.json): native/independent
balances <=1e-8 kg, sum absolute correction <=1e-10 kg, concentration
[-1e-10,180+1e-8], positive finite mu, wet mass fraction <=.24; remaining
[-1e-12,M0+1e-10], storage >=-1e-12, regional bounds/closure; flux and reverse
relative <=1e-10, dV discrepancy <=1e-15 m3, dW <=1e-14 kg, actual geometry
relative <=1e-8; analytical flow/share <=1e-6. Repeat/MPI use 009's per-column
normalized maximum <=1e-6, excluding transverse absolute internal flux and
balance residuals, with inherited dimensional floors; repeat absolute <=1e-12.
Complete clocks, exact 15-significant-digit pressure joins and first increments
are mandatory. No shortened support. Legacy render comparisons cover physics,
mesh dictionaries and initial fields at identical locators; metadata separately.

After short qualification freeze code, cases, tables, runtime, observer, matrix,
thresholds, support, branching and allowances. One genuine independent audit
of the exact freeze must PASS before any full integrations. Final exact-head
review checks relevant deltas. No self-authored independent approval.

Full B C: TR two histories x {base,temporal,axial,radial}=8;
SW adds property=10; total 18. Reuse 18 A C without alteration.
Only after all C qualify, support is sealed and contrasts scored, a qualified
MATERIAL decision triggers all 14 E2: TR two histories x {base,temporal,axial}=6,
SW adds property=8. Ceiling 46 integrations (32 without trigger), plus at most
two identical attempts total for demonstrated infrastructure interruption.
No numerical failure rescue, E4/E8, extra grid, duration or parameter sweep.
Append-only ledger separates preparation, solver invocations, integration starts,
completions and failures; retain every failed attempt.

## Support and decisions

Per history all 18 C terminals (nine A, nine B, both laws and all refinements)
enter Bstar=floor_to_1e-9kg(.95 min(Bterminal)); Decimal downward rounding,
exact represented native W/S values retained. Missing/invalid evidence blocks
sealing. Hash before scoring or E2, unchanged thereafter. Use one endpoint per
history for all laws, variants, comparisons. Report every terminal and fraction
scored; E2 shortage makes affected delivery UNRESOLVED without shrinking,
extrapolating or extending. Full-time hydraulic scores remain separate.

Primary C_B versus reference C_A: eight decisions, E_Spath=max over union of
native mass breakpoints plus zero/endpoint |S_B(B)-S_A(B)|/S_A(Bstar), budget
.01; D_TDS_pp=max absolute TDS difference across FIVE equal beverage-mass
fractions, budget .10 pp. Conservative cumulative splitting, never instantaneous
TDS interpolation or endpoint/time-only comparison. Independent 50-digit
arithmetic uses exact represented binary64 native values.

Primary allowances: absolute changes under paired time, paired axial, paired
SW property (zero TR), plus SUM of absolute metric changes from A-only and
B-only radial refinements with the other at base, plus maximum independent
arithmetic discrepancy across all variants. No radial cancellation.
Complete valid evidence and u<=.20 budget required. MATERIAL iff M-u>budget;
BELOW_BUDGET iff M+u<budget; otherwise UNRESOLVED including equality.
At least one MATERIAL triggers all E2; all eight BELOW_BUDGET closes
NO_MATERIAL_ARRANGEMENT_CONTRAST_FOR_TESTED_DELIVERY; otherwise no material
and any unresolved closes ARRANGEMENT_CONTRAST_UNRESOLVED, no full E2.

Conditional autonomous E2_B versus C_B: 24 decisions. Full native intervals
0–30 s: E_Qint=sum(|QE-QC|dt)/sum(QC dt), budget .01;
E_Qpeak=max(|QE-QC|/QC), .02; D_share_mean_pp=100 sum(QC|sE-sC|dt)/sum(QC dt),
1 pp; D_share_peak_pp=100 max|sE-sC|, 2 pp. s is geometric INNER in both.
Delivery uses the primary definitions and budgets referenced to C_B.
Allowances sum paired time/axial/property, C-only radial with E2 base, maximum
independent arithmetic discrepancy. Never interpolate mismatched clocks.
PASS iff M+u<budget; FAIL iff M-u>budget; otherwise UNRESOLVED, with the same
complete-evidence and .20 ceiling. Any qualified FAIL means insufficient;
all 24 PASS sufficient for these outputs/support; otherwise unresolved.
E2_NOT_EXECUTED_CONDITIONAL_GATE is neither failure nor pass.

Allowances are empirical sensitivities, not confidence intervals or continuum
bounds. Flow and correctly mapped high-k allocation are diagnostics only.
PHYSICAL_VALIDATION=NOT_ESTABLISHED. No uniquely identified lateral mechanism,
experimental assay-EY equivalence, fresh espresso property validation, arbitrary
geometry, wetting, production adoption or universal histogram-surrogate claim.
A delivery null is neither a hydraulic null nor exact invariance.
