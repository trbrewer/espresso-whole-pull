# SCI-MD-RHEOLOGY-002 mathematical and compatibility contract

G2; GOVERNING_PHYSICS_CHANGE. Owner authorization SCI-MD-RHEOLOGY-002 controls
this bounded task. Production solver source changes; constant-viscosity defaults
do not. One EWP PR, no merge, default adoption, successor, or laboratory work.

## Authority and scoped availability preflight

Base/main: 14fc4c8a4a94ffa54ffafd5c2c99037c1af680b9, tree
e8c5d5fc59a1bce751fc0ea892365c3dc7e7c941. PR #150 is merged. Its source-integrity,
static-validation and exact-producer-handoff post-merge workflows passed.
Historical failed package discovery was a bare-import collision, corrected in
that accepted predecessor; qualified package imports are used here. Historical
source-root environment failures do not establish a numerical failure.

Reuse predecessor AUTHORITY.json, source audit and primary adapter, including
its measured-loader breakpoints and exact water evaluation. Analysis source is
2058d0e947ee9eb92c52d64f6165b810f1fb4732, tree
a6ffb312473b15be43c1571a893b19873ea47c5a. Relevant source hashes are checked by
the reused qualified source importer. Production Puckworks lock remains
fc61c4670ec7bf801e40bb391aab16048b8da26b. No Puckworks changes.

Available-data-first: accepted industrial-extract measured Newtonian data are
locally available at the exact accepted authority. Its source card, rights,
provenance and predecessor audit remain the source authority. No new source
campaign, experimental target, fitting, or inventory inference is needed.
The new information is native two-way viscosity/transport feedback, which
frozen W concentration fields cannot determine. Positive residuals support
retaining only the experimental option; scale-removable/small effects support
constant viscosity; numerical/domain failures identify a specific limitation.
This advances the integrated transport/hydraulic decision without reopening
the species-inventory, E2C, or Visualizer blockers. The lower-cost frozen-field
screen is already accepted, and its audit is reused rather than repeated.

## Native contract

Supported: fresh start at zero, fixed 363.15 K, rho_water=965 kg/m3, positive
constant prescribed puck-face pressure difference, fully saturated bed,
static uniform or axial-two-layer permeability and porosity, Darcy resistance,
single complete effective aggregate solute. No restart, pressure histories,
prescribed flow, machine coupling, mechanics, evolving permeability, indexed
species, multiphase, variable density/diffusion, or temperature evolution.
Python generation and native startup independently reject incompatible modes.
Synthetic fixture purpose is explicit and separate from scientific cases.

At each interval [t_n,t_n+dt], accepted c^n and inventory^n determine
w^n=c^n/(965+c^n), mu^n=f(w^n), mobility=k/mu^n. Update coefficient boundaries
(including coupled processor patches) before the saturated native pressure
solve. Transport retains darcyFlux=-pressureEquation.flux(); extraction and
transport advance once, then inventory and outlet totals advance once.
No within-step nonlinear solve or saved-W forcing. Existing transport source,
capacity, schemes and clipping are unchanged. Record correction mass; reject
material negative numerical states separately from positive source exceedance.

The optional configuration `aggregate_viscosity` has mode `off` (default),
`observe` (diagnostics only) or `coupled`; enabled modes require an external
`table` and explicit `purpose` (`scientific` or `synthetic`). Off/absent modes
require neither a table nor Puckworks. W and N use observe mode so matched
beginning-of-step continuum diagnostics require no sparse-field interpolation.
Native execution never imports Python or locates Puckworks.

Property representation: linear table in dimensionless wet-basis aggregate
mass fraction, Pa.s, fixed temperature/density, domain [0,0.24]. Include water,
0.10 and every loader concentration breakpoint. At fixed temperature the
accepted bilinear measured interpolator is exactly piecewise linear in w;
below 0.10 the accepted adapter is exactly linear to water. Dense native/Python
checks, anchors and boundary-neighbor checks still verify this equivalence.
Reject malformed, nonfinite, unordered/duplicate, nonpositive, incompatible or
incomplete tables, and out-of-domain evaluations. EXPORT.json binds source
hashes, exporter, compiled evaluator, table and equivalence error. Runtime table
and source data remain external. Scientific source-domain support above 0.10
is measured; below it is an assumption, not new data or physical validation.

Stored dissolved mass is sum(phi*c*V); remaining inventory is sum(I*V), with
full-basket sector scaling 2*pi/sin(wedgeAngle), not 360/degrees. Units are kg,
kg/m3, Pa.s, m3/s and seconds. Native water/outlet accounting uses rho*Q*dt and
Q*c_out*dt. TDS instantaneous = soluteRate/(rho*Q+soluteRate); cumulative =
cupSolute/(cupWater+cupSolute). Existing inlet back diffusion is included.
The whole-run per-step record binds state time, interval bounds, Q and volume,
lagged and accepted c/mu extrema, bounds correction, inventory/storage/outlet
and inlet losses, dilute volume and resistance fractions, and pore Courant.

Scalar-viscosity analytical diagnostics in the supported saturated Darcy path
are replaced by the local resistance diagnostic in coupled mode. Other scalar
viscosity branches (machine, wetting, compaction, inertia) are rejected. In
observe/off mode their existing scalar reference behavior is preserved.

## Exact experiment and calibration

Copy exact uniform_9bar and reversed_3bar objects from predecessor SCENARIOS.json.
Preserve all physical inputs and 0–30 s window; no first-drip or cup-mass stop.
Base: 512 axial x 4 radial, dt=0.02 s. Temporal: dt=0.01 s, same mesh.
Spatial: 1024 axial x 4 radial, dt=0.02 s. Each set has independent native W/C/N
for each condition, at most 18 full runs including failures. A ledger is written
before every attempted full run, and failed directories cannot be overwritten.
Short smoke/analytical/compatibility/MPI fixtures are recorded separately.

W uses the exact predecessor water viscosity. C uses the local primary table.
Within each resolution set, alpha=sum(volume_C_reference)/sum(volume_W_reference),
using reference native volumes only. N uses constant mu_water/alpha, retaining
all other inputs and independently evolving transport. Hold that set's alpha
across both conditions. Q_N/(alpha*Q_W) must agree to 1e-6 relative. Reference
volume matching is calibration, not evidence of comparator sufficiency.

R_cont=sum(mu_i*dz_i/k_i)/A; dz derives from sector cell volumes/full area,
including radial volume weights and exactly one parallel reduction. Record
Q_cont=DeltaP/R_cont on c^n for C and W using the same native table and formula
as the predecessor resistance machinery. This avoids a sampled-field/time-level
mismatch. Check geometry and transverse invariance from native fixtures/fields.
Decompose Q_C_native-Q_W_frozen_cont into Q_C_native-Q_C_cont (operator) plus
Q_C_cont-Q_W_frozen_cont (feedback state difference). No separate attribution
to pressure and layers: both change between the two conditions.

## Prospective metrics and numerical gates

For each condition, compare C/W and C/N with positive denominator flow:
Eint=sum(abs(Q_C-Q_R)*dt)/sum(Q_R*dt); Epeak=max(abs(Q_C-Q_R)/Q_R).
Include every solved interval, including [0,dt]. No initialization zero sample,
sparse trapezoidal integration, early trimming, or changed denominator.
Materiality: Eint>=0.05 OR Epeak>=0.10; hydraulic development only.

Gates frozen before full science:

- Native/Python property relative maximum <=1e-4 (24,011 fixed checks).
- Uniform/layer discrete analytical relative flow error <=1e-6; layered
  continuum discrepancy must decrease with axial refinement.
- Disabled/absent compatibility max absolute numeric-trace difference divided
  by max(1,max(abs(baseline column))) <=1e-10; use accepted executable, not self.
- Constant-multiplier relative flow maximum <=1e-6; repeat absolute <=1e-12;
  MPI max normalized difference <=1e-6 (floor 1e-8; balance separately).
- Water/total-solute balance maximum absolute <=1e-8 kg; report also normalized
  to cumulative inlet water / initial 0.0056 kg inventory. Correction mass sum
  <=1e-10 kg. Accepted c >=-1e-10 kg/m3, c<=180+1e-8 kg/m3; inventory>=-1e-12 kg.
  Native raw negative concentration below -1e-10 fails before existing clipping.
- Q*dt versus native volume max discrepancy <=1e-15 m3; complete contiguous
  30 s coverage and matched W/C/N intervals (time tolerance 1e-8 s).

Per metric and condition, empirical estimate = absolute temporal metric change
+ absolute spatial metric change + quadrature/sampling allowance + maximum
C native-versus-continuum relative discrepancy across sets, normalized to W
(or N for C/N). Target <=0.005 (0.5 percentage points). Report these terms
separately. Primary interval integrals have zero sparse quadrature/sampling
allowance: piecewise-constant flux is represented on its actual full interval;
refinement peak metrics use every interval and preserve extrema. Figures may
thin lines but cannot change metrics. Show alpha variation and its effect on
base C/N metrics separately; it is already included in set-wise refinement
changes and must not be added twice. Spatial refinement changes Courant at
fixed dt; temporal refinement changes it at fixed mesh. These two-level
estimates are neither PDE error bounds nor statistical confidence intervals.

A metric is qualified material if value-estimate reaches its threshold;
qualified below if value+estimate is below it. Any uncertainty that could alter
classification is unresolved. Required positive source-domain failure takes
SOURCE_DOMAIN_LIMITED; implementation defects are separate, not science results.
Otherwise failed numerical gates give NUMERICALLY_UNRESOLVED. Qualified material
C/N in either condition gives COUPLED_STATE_DEPENDENCE_PERSISTS with precedence
over a small absolute label. Below-threshold C/N in both plus material C/W gives
STATIC_SCALE_SUFFICIENT_FOR_HYDRAULICS. Both absolute effects below with no
material residual gives SMALL_COUPLED_EFFECT. Report per-condition outcomes.

No transport-equivalence threshold or fitting. Report outlet water, solute,
modeled beverage, instantaneous/cumulative TDS, remaining/stored inventory,
boundary loss and source-domain occupancy. These are unvalidated model outlet
quantities. Industrial-extract transfer and dilute-extension assumptions remain.

## Freeze and completion

FREEZE.json binds this protocol, solver/helper, maintained generation, exporter,
runner, analysis and tests plus executable/table identities before full science.
Retain amendments and failed fixtures; never replace that original freeze after
scientific results. Run final-candidate full Python suite and ordinary repository
CI. Obtain one independent exact-head G2 review, or report unavailable honestly.
Scientific disposition, execution, tests, review, CI and merge status are separate.
