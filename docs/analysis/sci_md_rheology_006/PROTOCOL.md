# SCI-MD-RHEOLOGY-006 frozen contract

G2 / GOVERNING_PHYSICS_CHANGE. SOURCE_CONDITIONED_SYNTHETIC_MODEL_DEVELOPMENT;
PHYSICAL_VALIDATION: NOT_ESTABLISHED. Owner authorization is this task's scope.
Accepted predecessor: GitHub PR #158, merged by trbrewer at 2026-09-22T16:48:37Z,
merge db705b644bbc2c3f719690448657e845f2a8f65b on freshly fetched main.
No equivalent issue/PR found at startup. Separate worktree preserves other work.
One issue/PR; no merge, adoption, fitting, lock change, laboratory work or successor.

## Selection, sources and comparator

NEW_INFORMATION: native r–z redistribution under the existing local law.
POSITIVE: retain spatial viscosity resolution for tested spatial observables.
NEGATIVE: do not prioritize further radial rheology complexity on this evidence;
001–005 findings remain unchanged. NULL/BLOCKED: numerical/source/execution limits
are neither scientific rejection nor physical validation. GRINDER_TO_CUP: regional
water allocation affects transport and depletion histories; modeled cup delivery
is context without an established cup benefit. LOWER_COST_ALTERNATIVE: scalar
invariance supplies the comparator without a fitted closure or scalar-run matrix.

For positive spatially uniform mu_s(t), fixed isotropic k(x), incompressible Darcy,
constant inlet/outlet pressures and impermeable sides,
div[(k/mu_s)grad p]=0 implies div[k grad p]=0. Pressure pattern is invariant and
all fluxes scale together. Axially invariant radial zones therefore have
s0=A_i k_i/(A_i k_i+A_o k_o)=4/7. This covers autonomous bulk-state and total-Q
oracle scalar histories. No oracle implementation, fitting or replay occurs.
The theorem excludes changing/spatially modified k, extra forcing and altered
boundaries, and says nothing about whole-cup chemistry equivalence.

Reuse accepted 003 SOURCE_USE/EXPORT and 005 PROPERTY/FREEZE, law evaluators and
runtime tables by SHA256. Puckworks analysis commit
2058d0e947ee9eb92c52d64f6165b810f1fb4732, tree
a6ffb312473b15be43c1571a893b19873ea47c5a was confirmed read-only in the actual
checkout. Production lock fc61c4670ec7bf801e40bb391aab16048b8da26b is distinct.
Available-data preflight uses the existing authority/register and accepted external
001–005 evidence directories; no general corpus search or new source acquisition.
TR below .10 wet mass fraction is continuation. SW is a water-anchored source-shape
adaptation with 90 C extrapolation; industrial/reconstituted-coffee transfer to
espresso is unqualified. Dilute occupancy is pore volume, not measured coverage.
Source payloads, tables, executable, native fields and logs remain external.

## Native and output contract

Extend only observe/coupled to static radial_two_zone; bulkCoupled stays uniform/
axial. Beginning-step w=c/(965+c), mu=f(w), mobility=k/mu precede native pressure
and conservative transport/extraction/inventory advancement. Preserve transverse
exchange. No independent-tube replacement or imposed split. Other accepted
unsupported combinations remain rejected in Python and direct native startup.

Radial aggregate modes omit aggregate_intervals.csv. Instead emit
aggregate_radial_intervals_v1.csv every interval, with explicit column units,
start/state/end times, signed conservative native outlet zone/total flow and
reverse magnitudes, Qdt volume, cup water/solute, global storage/inventory/balances,
regional inventory and outlet solute rate, c/mu extrema, dilute pore occupancy,
zone geometry and full-dimensional outgoing-face-flux pore Courant. Courant is
dt*sum(max(outward face flux,0))/(phi*V), including processor faces. Zone sums are
globally reduced once then scaled by 2*pi/sin(wedge angle). Legacy uniform/axial
outputs stay unchanged. Series resistance and its dilute fraction are inapplicable;
shared radial-coupled analytical flow/error fields are NaN (not an oracle).
Regional depletion describes initial-region inventory; outlet solute does not
identify initial-region provenance because transverse exchange remains active.

## Fixed matrix and gates

R=.029 m, interface=.0145 m; k_i=3e-15 and k_o=7.5e-16 m2, inner area .25.
Synthetic arrangement fixed before runs, not a measured coffee prior. Four coupled
cases: TR_LINEAR and SW_WATER_ANCHORED_90C, each at 3 and 9 bar. Common accepted
values: L=.009011660896432553 m, phi=.4, dose=.020 kg, extractable fraction=.28
(total .0056 kg), rate=.15/s, capacity=180 kg/m3, D=1e-9 m2/s, rho=965 kg/m3,
T=363.15 K. Saturated, c=0, uniform inventory per bed volume, fixed k/phi,
zero ramp, accepted pressure nodes/walls. Entire 0–30 s; no target termination.
Base 512x64 dt=.02; temporal same mesh dt=.01; axial 1024x64 dt=.02;
radial 512x128 dt=.02; SW property base with accepted refined table. Interface
aligns on every mesh. Base fields every 5 s; others only final. No scoring from
snapshots. 18 science + 4 original-settings uniform_9bar/reversed_3bar C controls
=22 full runs. At most four documented correction/recovery full attempts, total
26; no outcome-driven refinement or parameter/window adjustment. Failed attempts
are retained. Freeze hashes source/executable/tables/scenarios before full runs.

Predeclared short fixtures, all 0–.2 s dt=.02: three declared meshes each at
water viscosity, double viscosity and uniform-k (9); base constant-table coupled
and absent against observe water fixture (2); accepted and candidate axial bulkCoupled
32x2 (2); deterministic nonuniform-mobility/solute serial, exact repeat and radial
MPI decomposition 32x8 (3). Total 16 native short runs; at most four implementation
correction repeats of those same slots (20 ceiling). The transverse fixture starts c=0; its nonuniform mobility develops deterministically
through native transport. No special initial field or restart mechanism is added. Native rejection starts
bounded to 16 plus at most four correction repeats; Python/observer unit tests
cover unsupported, malformed, domain, nonpositive-k, misalignment, empty zones,
zero-flow and nonfinite input. No pilot sweep.

Water/solute residual <=1e-8 kg; absolute correction sum <=1e-10 kg;
c>=-1e-10 and <=180+1e-8 kg/m3, w<=.24; remaining>=-1e-12 and <=.0056+1e-10 kg;
storage>=-1e-12 kg; Qdt-volume <=1e-15 m3; water increment-rho Qdt <=1e-14 kg.
Contiguous intervals/start-state agreement and final support tolerance 1e-9 s;
interval dt agreement 1e-12 s. Finite positive Q mandatory, no area fallback.
abs(Qi+Qo-Q)/Q<=1e-10; reverse/Q<=1e-10. Areas/volumes relative <=1e-8.
Analytical Q/share relative <=1e-6. Baseline all-column maximum absolute error
normalized by max(1,max(abs(reference))) <=1e-10 (inherited convention).
MPI normalized by max(1e-8,max(abs(reference))) <=1e-6; separate balance gates.
Exact-repeat absolute <=1e-12. Preserve stricter applicable inherited tests.

## Scoring frozen before execution

D_mean_pp=100 sum(abs(Qi-s0 Q)dt)/sum(Q dt), budget 1 pp.
D_peak_pp=100 max(abs(Qi/Q-s0)), budget 2 pp. Complete support, no dropped rows,
interpolation, start shift or tail crop. Report signed cumulative share shift
100(sum(Qi dt)/sum(Q dt)-s0) and direction; absolute metrics remain primary.
Each base-centered allowance u is the sum of absolute temporal/base, axial/base,
radial/base, SW property/base differences, arithmetic and scalar-fixture terms.
TR property term is zero: accepted piecewise-linear law/table representation is
exact (including every breakpoint and continuation). Arithmetic term is maximum
float64 versus independent longdouble reduction difference across the case's
runs. Each fixture term is 100 times the worst absolute native/analytical inner
share error over all applicable scalar fixtures, for both metrics. No 005 series
operator allowance. These are empirical sensitivities, not rigorous PDE bounds
or confidence intervals. Qualification requires all validity gates and
u<=.20*budget. Material iff D-u>budget; below iff D+u<budget; otherwise unresolved.
Both metrics must qualify for full case adjudication; qualified case material if
either is material, below only if both below. Law robustness at a pressure requires
both laws' same qualified conclusion, not independent experimental confirmation.

Secondary Q, modeled water/solute/beverage, cup aggregate TDS, regional remaining
inventory and limited fields are contextual. No taste, channel initiation,
instability, real-puck viscosity or chemical advantage over an unexecuted scalar.
Spatially modified permeability can mimic mobility; experimental identification
of viscosity separately from permeability is not established.
One independent exact-head G2 review after evidence, plus supported local/hosted
checks. No protected holdout or inherited extra pre-scoring review gate. If no
independent reviewer is available, stop READY_FOR_INDEPENDENT_REVIEW.
