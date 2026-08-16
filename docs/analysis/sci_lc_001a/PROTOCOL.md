# SCI-LC-001A Stage-A prospective protocol and executor — E1

Task: `SCI-LC-001A-E1-PREEXECUTION-PATCHES-AND-STAGE-A-EXECUTOR-IMPLEMENTATION-2026-08-16`

Status: `STAGE_A_EXECUTOR_E1_IMPLEMENTED_PENDING_BOUNDED_INDEPENDENT_REVIEW`

Change declaration: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`. Execution is not
authorized. This package defines a reduced diagnostic model; it does not change
OpenFOAM, run Puckworks, establish physical validation, or report a scientific
trajectory or classification.

```protocol-summary-json
{
  "classifier_precedence": [
    "AUTHORITY_OR_ARTIFACT_INVALID",
    "ANALYTICAL_STRUCTURAL_IDENTITY",
    "NUMERICALLY_UNRESOLVED",
    "INITIAL_CONDITION_DEPENDENT_OR_BISTABLE",
    "MODEL_FORM_OR_SECTOR_RESOLUTION_DISAGREEMENT",
    "METRIC_DISAGREEMENT",
    "NEAR_THRESHOLD_TRANSITION",
    "LATERAL_EQUALIZATION",
    "HETEROGENEITY_AMPLIFIES",
    "HETEROGENEITY_PERSISTS"
  ],
  "epsilon_floor": "0.05",
  "matrix_summary": {
    "active_scientific_rows": 848,
    "comparator_bindings": 848,
    "controls": 432,
    "dynamic_comparator_bindings": 276,
    "dynamic_comparator_rows": 276,
    "dynamic_rows": 553,
    "initial_row_count": 1280,
    "matrix_sha256": "4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717",
    "model_form_rows": 0,
    "rows_by_arm": {"C0": 70, "D1": 96, "D2": 168, "D3-EQ": 144, "D3-LOC": 144, "S1": 504, "S2": 90, "S3": 64},
    "scientific_rows": 848,
    "static_comparator_rows": 86,
    "structural_comparator_rows": 362
  },
  "stage_a_hard_maximum": 1280,
  "status": "STAGE_A_EXECUTOR_E1_IMPLEMENTED_PENDING_BOUNDED_INDEPENDENT_REVIEW",
  "uncertainty": "u_limit(G)=min(0.02,0.02*abs(G))"
}
```

## Question, hypotheses, and claim boundary

The question is: under what combinations of lateral conductance, axial
resistance contrast, heterogeneity scale, machine response, and
resistance-evolution timescale does puck nonuniformity decay, persist, or
amplify? H0–H6 respectively cover uncoupled persistence, passive equalization,
passive focusing, scale dependence, machine structural invariance in the fixed
linear quasi-steady limit, signed generic resistance feedback, and use of
reduced-form disagreement to prioritize later three-dimensional checks.

`PHYSICAL_VALIDATION`, `GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION`, measured
real-puck lateral conductance, and a universal coupling parameter remain
`NOT_ESTABLISHED`. `RP-D-LC-001b` Xi is synthetic numerical context only. No
SCI-LC-001B nomination or OpenFOAM execution is authorized.

## Static topology and nondimensionalization

For equal sector areas `a_i=1/N`, `p_hat=(p-p_o)/Delta_p_ref`,
`tau=t/T_shot`, `q_hat=q/(G_A Delta_p_ref)`, `G_ref=1`, and
`G_A=G_ref/N`. With periodic indexing:

```text
q_u_i=(p_b-p_i)/R_u_i
q_d_i=(p_i-p_o)/R_d_i
j_i+1/2=G_edge(p_i-p_i+1)
C_h_i dp_i/dt=q_u_i-q_d_i-j_i+1/2+j_i-1/2
```

`g_raw_i=exp(-a_h h_i)`,
`g_tilde_i=g_raw_i/sum_j(a_j g_raw_j)`, `G_i=a_i G_ref g_tilde_i`,
and `T_i=1/G_i`. Thus `sum_i G_i=G_ref`; `a_h=log(chi_R)/span(h)`
gives `max(T_i)/min(T_i)=chi_R`. A span at or below `1e-14` admits only
`chi_R=1` and fixes `a_h=0`; any non-unit requested contrast is rejected.

With `epsilon_floor=0.05`, `R_floor=epsilon_floor min_i(T_i)` and
`H_i=T_i-2R_floor>0`. The exact placements are:

```text
R_u_i=R_floor+alpha_place H_i
R_d_i=R_floor+(1-alpha_place)H_i
UPSTREAM_LOCALIZED alpha=1
AXIALLY_SELF_SIMILAR alpha=1/2
DOWNSTREAM_LOCALIZED alpha=0
```

Hence `R_u_i+R_d_i=T_i` exactly. At alpha=1/2 the exchange-plane pressure is
`(p_b+p_o)/2` for every sector and lateral flux is exactly zero: this is an
analytical structural control. At alpha 0 or 1, heterogeneous `T_i` gives
sector-dependent uncoupled internal pressures and therefore a nonzero lateral
driver when Lambda is positive. No outcome is prescribed by that capability.

The scaled ring operator and edge conductance are

```text
L_N p_i=(N/(2*pi))^2(2p_i-p_i-1-p_i+1)
lambda_N(m)=4(N/(2*pi))^2 sin^2(pi*m/N)
G_edge=Lambda G_A (N/(2*pi))^2.
```

At Lambda zero the independent parallel paths are recovered. At strong
coupling the internal pressures approach their common conservative limit.
Rotation/reflection permutes vectors and preserves scalar observables.

## Closed boundary contract

Every row instantiates exactly one of these modes. Machine-readable authority
assigns every serialized field exactly one of `REQUIRED`, `PROHIBITED`,
`DERIVED`, `NOT_APPLICABLE`, or `PROVENANCE_ONLY`; the validator enforces the
full table and derived `C_h` and `C_u` identities. The table is constructed
from explicit, exhaustive per-mode partitions: unassigned fields and fallback
provenance are both forbidden and counted as zero. No execution-affecting
field may be provenance-only.

- `PRESCRIBED_STATIC`: unknown `p_i`; `p_o_hat=0` and constant `p_b_hat`
  are prescribed; conservative node balances are algebraic. Storage and all
  machine primitives are prohibited.
- `PRESCRIBED_DYNAMIC_RAMP`: unknown `p_i(tau)`; `p_o_hat=0` and
  `p_b_hat=min(tau/0.05,1)` are prescribed; storage ODEs apply with
  `p_i(0)=0`. Machine primitives are prohibited.
- `MACHINE_COUPLED`: unknown `p_i(tau),p_u(tau),p_b(tau)`;
  `C_u dp_u/dt=Q_supply-Q_puck`, `p_b=p_u-R_line Q_puck`,
  `p_i(0)=p_u(0)=0`. The WP02-002 tuple fixes `p_o=0`, `p_shut=1`,
  `q_free=1`, `R_line=0.1`, `G_ref=1`, and the linear ramped supply law.
  The row must supply `Theta_M` and `C_u=Theta_M T_shot(21/11)` and must not
  prescribe basket pressure.

For dynamic rows `S_h=C_h/(G_A T_shot)`, so `C_h=S_h G_A T_shot` and
`Theta_L,m=S_h/(Lambda lambda_N(m))`; at Lambda zero it is
`INFINITE_NO_LATERAL_EQUALIZATION` while `S_h` remains finite.

## Zero-flow startup and resistance evolution

The signed surrogate is

```text
Theta_R dx_i/dtau=s(F_i-1)-x_i
F_i=(q_d_i/sum_j q_d_j)/a_i
H_i(t)=H_i0 exp(beta x_i), x_i(0)=0.
```

The conversion is frozen, not inferred from wording: `EQUALIZING -> s=+1.0`,
`LOCALIZING -> s=-1.0`, and `NONE -> s=0.0`. For `F_i>1`, positive `s`
increases `x_i`, `H_i`, and total local resistance and suppresses the initially
high-flow sector; negative `s` decreases them and reinforces it. Placement
changes the split, not the sign of total-resistance response. Active finite
evolution requires the first two labels; exact no-evolution requires `NONE`,
`beta=0`, and the no-evolution timescale semantics.

At the zero-pressure start, a common prescribed or machine forcing has a
common leading time coefficient. Expanding the storage balance one-sided gives
`p_i proportional to (G_u_i/C_h_i)` and therefore

```text
F_i(0+)=N(G_u_i G_d_i/C_h_i)/sum_j(G_u_j G_d_j/C_h_j).
```

Machine compliance changes only the common time coefficient and cancels from
the normalized limit; lateral exchange enters at higher order. This exact
mode-common dynamic limit is used at `tau=0`. Sector flow is scaled by
`G_A Delta_p_ref`, while the branch uses
`Q_hat_total=Q_total/(G_ref Delta_p_ref)=(1/N)sum_i(q_hat_i)`. Authoritative
calls carry flows in a tagged `SectorFlowVector`. Accepted scales are
`SECTOR_SCALED_DIMENSIONLESS` and `DIMENSIONAL_SECTOR_FLOW`; dimensional input
requires positive `G_ref` and `Delta_p_ref`. `WHOLE_NETWORK_SCALED_PER_SECTOR`,
untagged vectors, and unknown scales are rejected. For
`|Q_hat_total|<=1e-14` it may be
used only through `tau<=1e-6`. A mandatory companion changes only both branch
thresholds by the frozen factor 10 (`1e-15` flow and `1e-7` time), and
`u_startup(G)=|G_base-G_refined|` enters uncertainty once. The branch uses
`<=` at both thresholds. Missing, stopped, capped, or nonfinite companions are
`NUMERICALLY_UNRESOLVED` and cannot classify.
Zero flow later is a numerical stop. Nonfinite flow and negative flow beyond
the threshold stop. A zero sector flow with positive total flow gives `F_i=0`.
The prescribed-static mode starts from its algebraic `p_b_hat=1` solution and
has no zero-flow branch.

Only `H_i` evolves; floors and placement do not. Scientific admissibility is
the closed interval `0.25 <= H_i/H_i0 <= 4`. An outward crossing terminates as
`STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUTWARD_CROSSING_NO_CLIPPING`; exact
contact with inward or zero derivative continues. At an exact boundary an
outward derivative stops immediately. The exact root state may be reconstructed
diagnostically, but may not classify. There is no clipping or aggregate
renormalization. `beta=0` and `Theta_R=INFINITE_NO_EVOLUTION` are exact fixed
controls.

Contact uses relative tolerance zero and frozen absolute tolerances: multiplier
boundary `1e-12`, multiplier derivative `1e-14`, and located-root value
`1e-10`. Context is `INITIAL_STATE`, `ACCEPTED_STEP`, or `LOCATED_EVENT_ROOT`.
A located root names its boundary and reconstructs within the root tolerance.
The helper computes `dm/dt=beta*m*dx/dt`; callers cannot supply an outward flag.

## Integration, events, residuals, and sampling

Dynamic execution is prospectively bound to
`scipy.integrate.solve_ivp(method="DOP853")`, base
`rtol=1e-8, atol=1e-10, max_step=0.0025`, refined
`rtol=2.5e-9, atol=2.5e-11, max_step=0.00125`, over `tau in [0,1]`.
The reporting grid is `tau_k=k/1000`; uncertainty reconstruction additionally
uses 2,001 points from the same accepted dense output.

The sole operation cap is 200,000 RHS evaluations. The counter increments
before every RHS call, including rejected trials; at `nfev>=200000` the next
evaluation is refused. Partial output is diagnostic and scientifically
inadmissible.

Per-sector outward-crossing events are `exp(beta*x_i)-0.25` and
`4-exp(beta*x_i)`, each direction -1. Dense output locates roots to `1e-10`
tau, independently of reporting samples. Earliest time wins; ties choose lower
before upper, then ascending sector index. Tangential and inward contact do not stop. A
located event in an accepted step precedes a later cap; a cap precedes an event
that would require an unevaluated RHS. Nonfinite event functions stop. No
stopped or capped trajectory reaches classification.

Stage A uses no nonlinear fixed-point solve: `STAGE_A_NONLINEAR_FIXED_POINT_SOLVE=NOT_USED`.
Linear residuals use `r=A p-b`,
`s_i=max(|b_i|,sum_j |A_ij||p_j|,1e-14)`, and
`max_i |r_i|/s_i <=1e-12`. Equality passes. Nonfinite values fail. No retry is allowed and all
failure routing precedes scientific classification.

BASE uses the sole authoritative `solve_dense_binary64(A,b)`: IEEE-754 binary64
dense Gaussian elimination with scaled partial pivoting. Initial row scale is
`max_j |A_ij|`; selection maximizes `|A_rk|/row_scale_r`, ties use the lowest
original canonical row index, and ratio `<=64*epsilon_binary64` fails. BASE
must pass the scaled residual above. Caller-provided BASE state is prohibited.

`LINEAR_REFINED` internally obtains BASE `p0` using that same solver, then computes
`r0=A p0-b`, solve `A delta_p=-r0` exactly once, and set `p1=p0+delta_p`.
The corrected residual must be finite, no larger than the BASE residual, and
`<=1e-12`. Static gains use independently corrected active/comparator states;
dynamic `LINEAR_REFINED` is a complete companion trajectory applying this
single correction at every algebraic solve. Failure makes the gain unresolved.

## Observables, uncertainty, and classification

Hydraulic observables include sector flows and pressures, `H_q`, area-weighted
`CV_q`, effective area, seeded-mode amplitudes, absolute/net lateral exchange,
pressure asymmetry, dissipation, conservation, endpoint/integrated matched
gains, growth rate, and persistence. Floors are `H_q=1e-12`, seeded amplitude
`1e-12`, total dimensionless flow `1e-14`, and generic ratio denominator
`1e-12`. A denominator at or below its floor is unavailable, not silently
floored into a gain; an exact analytical control uses its identity path.

Ordinary gains are immutable `GainRecord` values built only from a validated
canonical active case. Construction resolves the exact Lambda-zero structural
comparator, requires an explicit numerator and denominator, applies
`abs(denominator)<=floor` as an unresolved gate, and records both. There is no
denominator default; structural controls use a distinct evaluation path.
Uncertainty applicability starts from a canonical case ID and validates role,
boundary mode, metric, profile, and comparator before deriving components.

For gain `G`, all uncertainty terms are nonnegative absolute gain units:

```text
u_integrator=|G_base-G_refined|
u_sector=|G_N-G_Nref| for frozen sector-refinement predicates (otherwise explicit N/A)
u_linear=|G_BASE-G_LINEAR_REFINED|
u_sampling=|G_1001-G_2001| from one accepted dense output
u_startup=|G_base_thresholds-G_refined_thresholds|
u_G=sum of applicable terms
u_limit(G)=min(0.02,0.02|G|)
```

`NOT_APPLICABLE` contributes zero only where an exact predicate says the
component does not apply; required N/A, missing, negative, nonfinite, or unknown
sentinels are artifact-invalid, while `UNAVAILABLE` is unresolved. Sector
companions map `N=4->8` and `N=8->16`; the explicit mode-4 Nyquist diagnostic
maps `N=8->16`, with all non-resolution primitives identical. Unavailable required components, stopped trajectories, nonfinite metrics, and
floor-dominated denominators are `NUMERICALLY_UNRESOLVED`. The limit is a 2%
relative tolerance capped at 0.02 gain units. At `G=0` it is zero; exact nulls
are handled analytically before this numerical gate, while a nonstructural
zero with nonzero uncertainty is unresolved. Equality `u_G<=u_limit` passes.
Model-form disagreement is a separate transition reason, not scalar error.
Denominator residual error is included exactly once in `u_linear`; denominator
floor contact is a validity gate and is not an additive uncertainty component.
Applicability is derived from validated rows and the enumerated metric kind,
never supplied by a caller. A numeric value for an inapplicable component is
artifact-invalid; an applicable `NOT_APPLICABLE` is artifact-invalid; applicable
`UNAVAILABLE` is unresolved.

## Numerical execution graph

Dynamic rows have exactly `BASE`, `INTEGRATOR_REFINED`, `STARTUP_REFINED`, and
`LINEAR_REFINED`; static rows have exactly `BASE` and `LINEAR_REFINED`. No
combined profile exists. Thus 553 dynamic rows permit at most 2,212 trajectory
invocations and 727 static rows permit at most 1,454 solves: 3,666 total solver
cases. Keys are cached uniquely by `(case_id,numerical_profile)`. Sampling
reconstructs 1,001 and 2,001 points from the same BASE dense output and adds no
trajectory. Sector refinement reuses existing BASE rows and adds no case; all
13 four-case bundles are complete. There are no hidden initial-condition runs,
automatic retries, profile substitutions, or tolerance relaxations.

Analytical identities are predicates—not caller assertions: Lambda zero,
self-similar placement, or uniform unit-contrast symmetry. They are recorded
as `ANALYTICAL_STRUCTURAL_IDENTITY` before numerical admissibility. Their
numerical controls still execute; an implementation failure is recorded in a
separate numerical-status field and cannot erase the theorem. Such controls
may be comparators but may never be nominated.

Remaining precedence is numerical failure, alternate-attractor dependence,
model/sector disagreement, metric disagreement, threshold-straddling,
equalization (`end,int<=0.90`), amplification (`end,int>=1.10`), then
persistence. Static cases use only matched static `H_q` and seeded-mode gains;
dynamic cases use endpoint and integrated gains against exact matched dynamic
Lambda-zero rows.

## Matrix and comparator reconciliation

The one canonical generator emits CSV and JSON. Stage A contains 1,280 rows:
C0 70, S1 504, S2 90, S3 64, D1 96, D2 168, D3-EQ 144, and D3-LOC 144.
There are 848 `ACTIVE_SCIENTIFIC_CASE` rows, 362
`STRUCTURAL_COMPARATOR` rows, and 70 `BOUNDED_STRUCTURAL_CONTROL` rows.

Every positive-Lambda active row binds one exact Lambda-zero comparator with
all other scientific primitives equal. Comparator rows have no comparator ID,
are executed controls, are not regime-classified, may serve multiple active
rows, and are counted as controls rather than scientific rows. D2 machine rows
also bind an exact prescribed-dynamic partner; D3 rows bind exact no-evolution
controls. No comparator self-reference is allowed. There are no multilayer,
D4, or X1 rows.

The matrix SHA-256 is
`4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717`.
The Stage-A hard maximum and prospective maximum are both exactly 1,280.

## Staged deferral and future work

`D4_STATUS=DEFERRED_NOT_AUTHORIZED_STAGE_A` and
`X1_STATUS=DEFERRED_NOT_AUTHORIZED_STAGE_A`. Direct helper invocation fails
closed. Stage A cannot generate adaptive rows or nominate SCI-LC-001B.

D4 still requires canonical row materialization, exact comparator and alternate
initial-condition binding, duplicate reconciliation, atomic cap semantics,
tests, independent review, and explicit authorization. X1 still requires
complete eligibility, atomic prescribed/machine pairs and cap handling,
admissible Stage-A evidence, tests, independent review, and explicit
authorization. Existing or retired helpers cannot be used informally.

## Stops, budget, artifacts, and restart

Authority/hash/review mismatch is an authority stop. Nonfinite/nonpositive
states, conservation/dissipation failure, residual or event failure, operation
cap, and failed refinement are numerical stops. Redundancy, inadequate
topology, and budget excess are design stops. Frozen bounded scientific stops
remain valid outcomes. An outer-level boundary is open/truncated and cannot be
extrapolated.

Stage A is below the static, dynamic, extraction, memory, and wall-time ceilings
recorded machine-readably. This correction authorizes neither the <=64-case
timing pilot nor execution. A later executor must bind exact source, protocol,
matrix, environment, authority, immutable per-case records, manifests, and
restart matching. Partial/stopped outputs are never adjudicative.

The package now requires another independent read-only exact-head review and
separate owner adjudication before any timing or scientific execution.
