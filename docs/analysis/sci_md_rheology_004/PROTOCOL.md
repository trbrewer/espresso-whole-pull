# SCI-MD-RHEOLOGY-004: matched-output aggregate-solute delivery

G1 / SOURCE_SCENARIO_CHANGE_ONLY. Owner's task directive authorizes this work,
one issue (#155), branch, unmerged PR, eight full native SW N attempts, focused
checks and independent review. One compact pre-scoring freeze and independent
audit, then normal independent final exact-head review. No G3/holdout claim:
predecessors are exposed computational comparison evidence. No production solver,
transport, source, boundary, viscosity evaluator, default or runtime-lock change;
no Puckworks writes, merge, laboratory work, new source campaign or successor.

## Starting authority and scoped availability

Fetched EWP main is 2542e2ea3925abcb64a881293b6dc8743e3be056, tree
 a793ce73337af557b0fef33eacf8baf3fc2a908c. Live PR #154 is MERGED; all three
head CI checks succeeded. There are no later main changes at startup. Existing
owner checkout is clean on its prior branch and is untouched; this task uses a
clean separate worktree. Analysis Puckworks main and accepted clean detached
analysis checkout are 2058d0e947ee9eb92c52d64f6165b810f1fb4732, tree
a6ffb312473b15be43c1571a893b19873ea47c5a. Runtime lock remains
fc61c4670ec7bf801e40bb391aab16048b8da26b.

Accepted external 002 science (18 W/C/N runs), 003 science (24 C runs, of which
only eight SW C enter this task), 003 tables-qualified, and 002 corrected bin
are available. Explicit machine-local paths and commands are supplied in the
handoff; local absolute paths, fields, logs, binaries and tables stay out of Git.
The reuse receipt verifies configurations, inputs, full intervals and logs;
002 and 003 metric reproduction must equal accepted JSON before freeze. The
004 execution-root digest prevents changing roots to evade the attempt ceiling.
Original science executable 9e28686e567498de6d3f4bd2ba7b8e61872fef7b12f7daee4e2df6846b101139
is distinct from parser-corrected executable
9dea02fc3ba0a2858bd1efda6743c0feefffc5a1f863db3953bfb3d60efb5d43.
Reuse follows the accepted 002 valid-table POST_RESULT_AMENDMENT; no predecessor
freeze is edited and no consumed campaign is invoked. Missing required artifacts
produce a specific partial/dependency result, never a predecessor replay.

New information: mass-coordinate aggregate-solute discrepancies and independently
evolved constant-viscosity SW transport; hydraulic scaling cannot supply missing
concentration/inventory trajectories. Material results retain coupling relevance
to aggregate extraction even at matched output. Below-threshold results deprioritize
further rheology complexity for these aggregate outputs while preserving hydraulic
need and optional coupling. Mixed/unqualified results restrict claims to qualified
laws, scenarios, observables and support and identify unresolved dependencies.
Grinder-to-cup link: distinguish shot timing/throughput from solute at specified
output mass. Lower-cost reuse is exhausted only for the eight missing N trajectories;
this is not a repeated species-inventory blocker or data-exhaustion/lab claim.

## Treatments, calibration and execution

Exactly TR_LINEAR and SW_WATER_ANCHORED_90C; exactly uniform_9bar and reversed_3bar.
Use maintained 002 scenario/execute helpers and accepted 001 physical inputs,
initial state, 90 C, rho=965 kg/m3, inventory .0056 kg, capacity 180 kg/m3,
kinetics .15/s, diffusion 1e-9 m2/s, geometry, porosity and permeability over 0–30 s.
Pressure and layer geometry change together; their separate effects are unidentified.
W is accepted native constant-water-viscosity; C is accepted native coupled;
N is an independently evolved native pressure/transport/inventory solution.

For each law/set, freeze full-precision accepted alpha=reference C volume / reference
W volume at 30 s; mu_N=mu_water/alpha. Only uniform reference hydraulic volume
enters calibration. No transfer, solute, TDS or matched-mass fit, no endpoint refit.
TR reuses 002 W/C/N at base, temporal and spatial. Its accepted exact piecewise-linear
table represents the law exactly on its knots: property term is zero, no invented
property run. SW reuses 003 C at all four sets and matching W (base W for property).
Only new full runs: SW N, two scenarios × four sets, maximum eight INCLUDING failures.
Base 512 axial ×4 radial, dt=.02 s; temporal same mesh dt=.01; spatial 1024×4,
dt=.02; property base mesh/dt and refined observer table with property-specific alpha.
Scientific observe mode's diagnostic table mu is not applied constant hydraulic mu.
Never scale W chemistry or warp its time coordinate to manufacture N.

STARTED is durably appended/fsynced before each full invocation. Exact allowed
identities only; failure remains counted; duplicate/output overwrite/refusal;
no automatic retries or replacements. Completed subsets remain usable with
provisional support. Zero smoke runs planned (at most two separately logged
subsecond environment checks were authorized, but are unnecessary). Accepted
unchanged-source verification is reused, no new native verification campaign.

## Discrete observer and support

Native source initializes cupWaterMass and cupSoluteMass to zero. Each physical
step adds rho*Q*dt and max(outletSoluteRate,0)*dt; aggregate_intervals.csv writes
those cumulative totals. Derive increments by successive differences including
zero origin. Cross-check every water increment against rho*Q*dt to 1e-14 kg.
B=W+S is modeled beverage mass, not validated scale mass, foam or downstream storage.
Within an interval use the same fraction of delta B for W, S and time, or fraction
of delta W on water coordinate. This is the small analysis equivalent of the
native fraction collector's share allocation, not a continuous-PDE exact solution
or mass-stop solver execution. No sparse field interpolation or interpolated TDS.

For each scenario, common B_star (and W_star) is the minimum final native C/N
mass over BOTH selected laws and ALL required numerical sets. Coverage and
qualification are recorded in SUPPORT.json before discrepancy calculations.
Every refinement uses the same support; no result trimming or limiting-law removal.
Incomplete required sets produce explicitly provisional support and cannot receive
a complete-task disposition. Verify W covers support before C/W context.
Use [0,endpoint], including the first physical interval. Piecewise-linear S,W,t
on B and S,B,t on W, evaluated at union of arm-native breakpoints. No 36/40 g
extrapolation. Time-coordinate 30 s outputs are reported separately. Water-coordinate
predictions are conditional on specified throughput; beverage-coordinate predictions
are conditional on specified modeled beverage mass. Zero-mass TDS is undefined/null.

## Metrics, thresholds and empirical qualification

C/N primary, C/W secondary. E_end=abs(S_C(end)-S_N(end))/S_N(end).
E_path=max(abs(S_C(x)-S_N(x)))/S_N(end). Preserve signed terminal grams.
Exactly five equal coordinate fractions; fraction TDS=delta S/delta B;
report fraction/cumulative TDS and max absolute fraction discrepancy in percentage
points. On B this is the primary TDS metric; W fraction diagnostics remain secondary.
Report endpoint times, signed difference and ratio. No pooling coordinates.

Engineering thresholds: E_path .05 (5% of comparator terminal solute), maximum
fraction-TDS difference .5 percentage points. Not taste thresholds or experimental
confidence limits. E_end is contained by E_path. Correlated metrics are not
independent confirmations. For each primary metric u=sum absolute temporal,
spatial, property changes from base on SAME support. Set-specific alpha already
includes its refinement effect; do not add it twice. TR property term zero.
Arithmetic error is separately measured against long-double evaluation on identical
breakpoints and conservatively added to u; no manufactured exact-zero claim.
Float identity/splitting tests allow 1e-14 kg (and inherited time tolerance 1e-10 s);
negative mass increments are rejected rather than clipped.

Targets: u<=.005 for E_path and <=.05 percentage points for fraction TDS. Material
only if value-u reaches threshold; below only if value+u is strictly below;
failed targets or straddling metrics unresolved. A comparison is MATERIAL if
either metric qualifies material, BELOW THRESHOLDS if both qualify below,
otherwise UNRESOLVED. Required qualification failure prevents overall completeness.
No extra refinements, relaxed thresholds, hydraulic-error allowance as chemistry
bound, or continuum comparison. Two-level estimates are empirical, not rigorous
PDE bounds or confidence intervals. Native N flow must equal alpha*matching W
within 1e-6 relative; this qualifies hydraulics only.

Inherited gates every record: complete finite contiguous 0–30 s physical intervals;
volume=Q*dt within 1e-15 m3; water/solute balance <=1e-8 kg, total absolute correction
<=1e-10 kg; c>=-1e-10 and c<=180+1e-8 kg/m3; w<=.24; remaining inventory
>=-1e-12 and <=.0056+1e-10 kg; stored dissolved mass >=-1e-12 kg. No state extrapolation.

Overall priority: any missing source/execution/support/numerical qualification =>
PARTIALLY_QUALIFIED_OR_UNRESOLVED, preserving individual findings; else all below =>
MASS_MATCHED_AGGREGATE_DELIVERY_BELOW_THRESHOLDS; all material =>
MASS_MATCHED_AGGREGATE_DELIVERY_MATERIAL; remaining complete mixture =>
LAW_OR_SCENARIO_DEPENDENT. Report disagreements with water-coordinate diagnostics.
Retain established hydraulic classifications; do not reopen that decision.

TR dilute continuation is assumed. SW is a water-anchored alternative shape with
90 C temperature extrapolation and shared Weisser lineage. Both transfer industrial/
reconstituted extract to fresh espresso without qualification; neither is a new
independent espresso dataset. Below thresholds does not establish pressure-flow
accuracy, residence-time fields, species extraction, whole-shot transfer, universal
transport equivalence or exact time rescaling. No physical validation, taste,
calibrated species inventory, constitutive-law universality or default adoption.

## Pre-scoring reconciliation

The inherited preparation commit fbe6992 contained the draft freeze and no 004
science attempts or audit. Owner authorized takeover of its unfinished edits.
Before any scoring or native attempt, the single freeze was reconciled with
independent audit findings: retain admissible subsets and actual ledger counts,
require matching W for N hydraulic qualification, and retain long-double
fraction arithmetic through metric evaluation. Fourteen focused tests pass.
Thresholds, laws, scenarios, alpha values and execution budget did not change.
The original preparation state remains in Git history; no predecessor record
or consumed campaign was changed. The independent exact-commit audit binds
the final pre-scoring freeze used for all eight attempts.
