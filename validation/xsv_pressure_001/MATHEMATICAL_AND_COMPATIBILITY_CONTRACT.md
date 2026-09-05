# XSV-PRESSURE-001 frozen mathematical and compatibility contract

G2; NO_GOVERNING_PHYSICS_CHANGE; NO_GOVERNING_EQUATION_CHANGE;
NEW_PRODUCTION_BOUNDARY_INPUT_MODE; PRODUCTION_BOUNDARY_BEHAVIOR_CHANGE.
Owner authority: XSV-PRESSURE-001-G2-OWNER-AUTHORIZE-NATIVE-PIECEWISE-LINEAR-PRESCRIBED-PRESSURE-HISTORY-NO-GOVERNING-EQUATION-CHANGE-PRODUCTION-BOUNDARY-BEHAVIOR-CHANGE-2026-09-04.

Legacy prescribedPressure keeps mandatory targetInletPressure and pressureRampTime,
P(t)=targetInletPressure*clamp(t/pressureRampTime,0,1), including existing
zero/near-zero ramp behavior. Existing cases remain valid unchanged. Its history
dictionary is prohibited. Prescribed flow and lumped machine compliance retain
all existing contracts and equations.

New prescribedPressureHistory requires prescribedPressureBoundary with exactly
scheduleType piecewiseLinear, timesS and pressuresPa. Arrays have equal lengths
of at least two. Times are finite, strictly increasing solver seconds. Pressures
are finite nonnegative inlet gauge Pa. Equal consecutive pressures, rises, holds,
falls and zero tails are allowed. Full solver interval coverage is mandatory.
Missing/malformed inputs fail closed. Scalar target/ramp fields in history mode,
or a history dictionary in legacy mode, fail XSV_PRESSURE_001_CONTRACT_CONFLICT.
No sorting, deduplication, extrapolation, hidden endpoint extension, unit
reinterpretation, gain, offset, filtering, smoothing, negative clipping or CSV
parsing is allowed. Endpoint tolerance is solely for numerical endpoint equality.

P(t) is linear between adjacent points. The patch assignment, trace and logs
use this same evaluated value. I(a,b;Pf)=integral_a^b max(P(t)-Pf,0)dt splits
at every intersected knot. For each clipped segment with endpoint excess x,y
and duration d: both nonpositive gives zero; both nonnegative gives d*(x+y)/2;
opposite signs split at exact threshold crossing and integrate the positive
triangle. Endpoint equality yields no negative area. Results must be finite
and nonnegative, including intervals spanning multiple knots.

For finite required integral R>=0, crossing returns the earliest t in [a,b]
with I(a,t;Pf)=R. R=0 returns a. Locate the segment by exact cumulative
integration, then use 96 deterministic bisections against exact segment area for a strictly interior positive-area request,
returning the final bracket midpoint. When the request equals cumulative full-segment positive area, return the analytically located first positive-support endpoint, including a falling threshold crossing before a zero-area plateau. Unreachable requests fail with
XSV_PRESSURE_001_CROSSING_UNREACHABLE. No endpoint pressure approximation or
crossing outside the interval is permitted.

Maximum boundary pressure is max(pressuresPa), including interior knots,
used by compaction/domain checks wherever legacy pressure uses its target.
Lumped machine retains its shutoff maximum. Governing Darcy/Forchheimer,
wetting storage, species/extraction, compaction, permeability evolution,
geometry, cup accumulation and fraction collection equations are unchanged.

Function tolerances: pressure and maximum 1e-6 Pa; integral max(1e-6 Pa*s,
1e-12 relative); crossing 1e-10 s. Structured repeat output is byte identical.
Legacy constant (900000 Pa, zero ramp) and ramp (900000 Pa, 5 s) equivalence:
pressure 1e-6 Pa, first drip 1e-8 s, front 1e-10 m, integrated/flow relative
1e-8 with absolute floor 1e-14 SI, normalized final-field Linf 1e-8.
Synthetic schedule: (0,0),(3,300000),(8,900000),(18,900000),(25,600000),
(30,0),(33,0). Timestep base .02 s, refined .01 s; same 32x16 mesh.
First drip difference <=max(base dt,.10 s), cup mass relative <=.01,
cumulative mass curve NRMSE <=.02; exact common-time pressure.
Serial/MPI four ranks: integrated relative 1e-8 (1e-14 SI absolute floor),
first drip 1e-8 s, normalized final fields 1e-8. Every production run requires
completion, finite bounded fields and existing conservation acceptance.
Compaction uses a below-critical interior maximum accepted and at-critical
interior maximum rejected despite a final zero. All 20 user-specified invalid
contracts must fail nonzero with stable task tokens. Required existing modes
are rerun against the same baseline configuration and binary bindings.

Contract changes after production qualification starts require a recorded
reason, new hashes, invalidation of affected evidence and affected reruns.
PLAY-003 remains paused until separate exact-head review and owner merge.

Normalization clarification before rerun: final-field Linf differences use max(1 SI unit, both final field Linf magnitudes) as denominator; uniform fields are expanded to the mesh cell count. Absolute differences are retained. This prevents zero-tail roundoff from setting the normalization scale. The 1e-8 acceptance threshold is unchanged. Prior affected reductions are invalidated in QUALIFICATION_CORRECTIONS.json.
