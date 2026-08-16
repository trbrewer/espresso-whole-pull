# SCI-LC-001A corrected prospective protocol

Status: `PROSPECTIVE_PROTOCOL_CORRECTED_PENDING_SECOND_INDEPENDENT_PRE_EXECUTION_REVIEW`

Task: `SCI-LC-001A-PROTOCOL-CORRECTION-C1`

Change: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`

This document and `SCI_LC_001A_PROTOCOL.json` prospectively freeze a corrected
diagnostic reduced-model study. They do not authorize execution. The accepted
independent review found that the original proportional resistance split made
the lateral operator identically inactive and identified incomplete primitive,
boundary, integration, model-form, comparator, uncertainty, classification,
and adaptive mappings. Those findings control this correction.

RP-D-LC-001b remains closed at `NO_UNAMBIGUOUS_BELOW_CANDIDATE`. Its synthetic
Xi values are numerical context only: not calibration, a real-puck parameter,
or a physical prior.

## Structured human/machine agreement record

This parsed block is tested against the controlling JSON rather than by loose
text matching.

```protocol-summary-json
{
  "classifier_precedence": [
    "AUTHORITY_OR_ARTIFACT_INVALID",
    "NUMERICALLY_UNRESOLVED",
    "UNIFORM_OR_STRUCTURAL_CONTROL",
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
    "comparator_bindings": 1210,
    "controls": 70,
    "dynamic_comparator_bindings": 552,
    "dynamic_comparator_rows": 276,
    "dynamic_rows": 553,
    "initial_row_count": 1280,
    "matrix_sha256": "cad4955a9e54c93ed4d1677a0ab00fcc05f53ede09e624bf572931f247911577",
    "model_form_rows": 0,
    "rows_by_arm": {
      "C0": 70,
      "D1": 96,
      "D2": 168,
      "D3-EQ": 144,
      "D3-LOC": 144,
      "S1": 504,
      "S2": 90,
      "S3": 64
    },
    "scientific_rows": 1210,
    "static_comparator_rows": 86
  },
  "status": "PROSPECTIVE_PROTOCOL_CORRECTED_PENDING_SECOND_INDEPENDENT_PRE_EXECUTION_REVIEW",
  "uncertainty": "u_limit(G)=min(0.02,0.02*abs(G))"
}
```

## Question, hypotheses, and claim ceiling

The controlling question remains: under what combinations of lateral
conductance, axial resistance contrast, heterogeneity scale, machine response,
and resistance-evolution timescale does puck nonuniformity decay, persist, or
amplify?

- H0: normalized inequality persists for uncoupled fixed positive paths.
- H1/H2: passive exchange may equalize or focus depending on topology.
- H3: response depends on circumferential scale.
- H4: machine dynamics are spatially inactive in the linear quasi-steady
  fixed-resistance limit, becoming relevant only with another timescale.
- H5: signed generic resistance feedback can be equalizing or localizing.
- H6: boundaries and reduced-form disagreement are higher-value future 3-D
  targets than broad interiors.

Physical and general whole-solver validation remain `NOT_ESTABLISHED`.
OpenFOAM, Puckworks, experiments, protected scoring, real-puck conductance,
universal parameters, SCI-LC-001B, and production physics are not authorized.
Eventual claims are limited to the exact reduced formulation within frozen
ranges.

## Scales and corrected one-plane network

Use `Delta_p_ref`, `T_shot`, whole-network `G_ref`, and per-sector
`G_A=G_ref/N`:

```text
p_hat=(p-p_o)/Delta_p_ref
tau=t/T_shot
q_hat=q/(G_A Delta_p_ref).
```

For equal areas `a_i=1/N`, deterministic positive `h_i`, and contrast
`chi_R`, choose `a_h=log(chi_R)/(max h-min h)` and define

```text
g_raw_i=exp(-a_h h_i)
g_tilde_i=g_raw_i/sum_j(a_j g_raw_j)
G_i=a_i G_ref g_tilde_i
T_i=1/G_i.
```

Freeze `epsilon_floor=0.05` and

```text
R_floor=epsilon_floor min_i(T_i)
H_i=T_i-2R_floor
R_u_i=R_floor+alpha_place H_i
R_d_i=R_floor+(1-alpha_place)H_i.
```

Placement is exact:

| Placement | `alpha_place` | Meaning |
|---|---:|---|
| `UPSTREAM_LOCALIZED` | 1 | heterogeneous residual upstream |
| `AXIALLY_SELF_SIMILAR` | 1/2 | exact structural null comparator |
| `DOWNSTREAM_LOCALIZED` | 0 | heterogeneous residual downstream |

Because authorized `epsilon_floor<=0.10` and `T_i>=min T`,
`H_i>=min(T)(1-2epsilon)>0`; floors and all resistances are positive.
Algebraically `R_u_i+R_d_i=2R_floor+H_i=T_i`. Conductance matching follows
from `sum_i G_i=G_ref sum_i(a_i g_tilde_i)=G_ref`. Rotation and reflection
permute the same normalized values. At `chi_R=1`, all `T_i=N/G_ref`.

For the reviewed proportional construction `R_u=alpha T`,
`R_d=(1-alpha)T`, the uncoupled node pressure is
`p_i=(1-alpha)p_b+alpha p_o`, independent of `i`; this is the rejected
degeneracy. Under the corrected upstream placement,
`p_i=R_floor(p_b-p_o)/T_i+p_o`; under downstream placement,
`p_i=p_b-R_floor(p_b-p_o)/T_i`. Any heterogeneous `T_i` therefore gives
sector-dependent exchange-plane pressure in both active placements. Positive
lateral conductance then has a nonzero driver unless symmetry makes the
neighbor difference zero. No particular scientific regime is assumed.

At self-similar placement `R_u=R_d=T/2`, every uncoupled pressure is the common
midpoint, so all lateral fluxes remain exactly zero for every Lambda. This is a
bounded C0 family, not a broad scientific sweep. At Lambda=0 the independent
parallel paths are recovered. As Lambda tends to infinity, connected internal
pressures approach a common value while total path and boundary balances remain
finite. Tests cover both limits, active-placement counterexamples, positivity,
conductance matching, invariance, and bounded floor sensitivity
`epsilon={0.02,0.05,0.10}`.

## Lateral operator and storage

Use

```text
L_N p_i=(N/2pi)^2(2p_i-p_i-1-p_i+1)
lambda_N(m)=4(N/2pi)^2 sin^2(pi m/N)
G_edge=Lambda G_A (N/2pi)^2.
```

Thus a fixed mode tends to continuum eigenvalue `m^2` as N increases. Storage
uses the primitive matrix axis

```text
S_h=C_h/(G_A T_shot),       C_h=S_h G_A T_shot
Theta_L,m=S_h/[Lambda lambda_N(m)].
```

Freeze `S_h={0.01,0.03,0.1,0.3,1,3,10,30}`. At Lambda=0 retain finite `S_h`
and record `INFINITE_NO_LATERAL_EQUALIZATION`. `Theta_L,m` is derived per row,
never independently swept or silently used to vary storage.

## Boundaries and machine tuple

Dimensionless outlet pressure is zero. Static basket pressure is one. Dynamic
prescribed pressure is exactly

```text
p_b_hat(tau)=min(tau/0.05,1),   tau in [0,1].
```

The named machine tuple `WP02_002_DIMENSIONLESS_LINEAR_SUPPLY_V1` freezes
`p_o=0`, `p_shut=1`, `q_free=1`, `R_line=0.1`, initial `p_u=0`, `G_ref=1`,
the same ramp, and

```text
Q_supply=q_free ramp(tau) max(1-(p_u-p_o)/(p_shut-p_o),0)
p_b=p_u-R_line Q_puck.
```

The reference load seen upstream is `G_load=G_ref/(1+R_line G_ref)=10/11`;
supply slope plus load is `a_eff=21/11`. Only compliance changes:

```text
C_u=Theta_M T_shot (21/11),
Theta_M={0.03,0.1,0.3,1,3,10}.
```

The row stores the tuple ID and derived `C_u`. Two implementations must agree;
the current protocol test independently reconstructs the existing
`machine_coupling_reference.py` continuous solution.

## Signed resistance evolution

The only dynamic resistance law is
`SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE`:

```text
Theta_R dx_i/dtau=s(F_i-1)-x_i
F_i=[q_d_i/sum_j q_d_j]/a_i
H_i(t)=H_i0 exp(beta x_i)
R_u_i(t)=R_floor+alpha_place H_i(t)
R_d_i(t)=R_floor+(1-alpha_place)H_i(t).
```

Initial `x_i=0`. Floors do not evolve, placement remains fixed, aggregate
conductance is not renormalized, and total conductance may evolve. The allowed
residual multiplier is `[0.25,4]`; leaving it causes
`STOP_RESISTANCE_EVOLUTION_MULTIPLIER_OUT_OF_RANGE_NO_CLIPPING`. Nonpositive
resistance or conductance is a numerical stop. `beta=0` and
`Theta_R=INFINITE_NO_EVOLUTION` are exact fixed limits; `Theta_R=0.03` is the
finite fast-relaxation control. The law is generic and physically unidentified.

## Initial conditions, integration, and sampling

Freeze internal pressures, machine pressure, and feedback states to zero.
Primary Fourier phase is zero; rotation is `i->i+1 mod N`, reflection is
`i->-i mod N`, phase reversal adds pi, and alternate perturbation amplitudes are
0.5 and 1.5 times the frozen base field. Alternates initialize resistance from
that scaled/phase-transformed field and pressure from the same zero state.

Dynamic integration is SciPy `solve_ivp` DOP853. Base settings are
`rtol=1e-8`, `atol=1e-10`, `max_step=0.0025`; refined settings are
`2.5e-9`, `2.5e-11`, `0.00125`. Output is sampled at
`tau_k=k/1000, k=0..1000`. Maximum internal steps are 200,000. Linear and
nonlinear relative residual tolerances are `1e-12` and `1e-10`. Failure is
`NUMERICALLY_UNRESOLVED;NO_CLASSIFICATION`.

## Model-form disposition

The unexecutable `MULTILAYER_SELECTED_CHECK` placeholder and all its rows are
removed. Initial results, if later authorized, are provisional core-model
classifications. Sector checks remain in S3. A separately frozen and reviewed
model-form check is mandatory before any SCI-LC-001B nomination, and a changed
classification remains a transition/disagreement result. No nomination may
rely on unresolved model form.

## Matrix

- C0: analytical, uniform, rotation/reflection, machine, no-evolution, and 54
  bounded self-similar null rows.
- S1: 504 active-placement rows: six heterogeneous contrasts, fourteen Lambda
  levels, three N=8 Fourier modes, and two active placements.
- S2: 90 bounded block/rotation/broadband robustness rows.
- S3: 64 core-only fixed-mode sector, N=8 mode-4 Nyquist-to-N=16 resolved, and
  floor-sensitivity rows, including an exact Lambda=0 comparator for each
  active check and a declared comparison role.
- D1: 96 rows, including a materialized Lambda=0 comparator for every active
  transient family.
- D2: 168 rows, including exact Lambda=0 and matched prescribed comparators for
  every machine tuple.
- D3-EQ/D3-LOC: 144 rows each, including exact Lambda=0 comparators and bindings
  to exact D1 no-evolution rows.

There are 1,280 initial rows, including 70 controls, 1,210 scientific rows,
553 dynamic rows, 276 materialized dynamic Lambda=0 comparator rows, 552
dynamic comparator bindings, 86 static Lambda=0 comparator rows, 1,210 total
comparator bindings, and zero multilayer rows. D4/X1 remain rules, not
matrix rows. Maximum D4 is 4,096, maximum X1 is 1,000, and prospective maximum
is 6,376. The matrix hash is
`cad4955a9e54c93ed4d1677a0ab00fcc05f53ede09e624bf572931f247911577`.

Every row records Lambda and edge coefficient, `S_h` and derived Theta,
floor/placement, `G_ref/G_A`, machine tuple and compliance, integration profile,
all comparator IDs, classifier route, model-form gate, adaptive group, role,
eligibility, canonical ID, and row hash. Inactive fields use
`NOT_APPLICABLE`.

## Observables, comparators, and denominator floors

Primitive histories are pressure, axial/lateral flow, resistance/evolution,
total and supply flow. Derived outputs include flow fractions/focusing,
`H_q=0.5 sum|f_i-a_i|`, area-weighted CV, effective area, seeded resistance,
pressure, and flow mode amplitude/phase, normalized absolute lateral exchange,
signed cancellation, pressure asymmetry, dominance/persistence, conservation,
dissipation, condition, and refinement evidence. Extraction remains selected
and secondary.

Static S1/S2 use exact Lambda=0 static comparators and only

```text
G_static_H=H_q(Lambda)/H_q(0)
G_static_mode=|A_q,m(Lambda)|/|A_q,m(0)|.
```

Dynamic D1-D3 use materialized Lambda=0 rows with identical storage, evolution,
boundary, machine tuple, initial condition, and numerics:

```text
G_coupling_end=H_q(T;Lambda)/H_q(T;0)
G_coupling_int=int H_q(Lambda)dt/int H_q(0)dt.
```

Floors are `H_q=1e-12`, seeded amplitude `1e-12`, total flow `1e-14`, and any
other ratio denominator `1e-12`. Uniform cases receive `STRUCTURAL_IDENTITY`;
Fourier cases use seeded amplitude if H_q is floored; otherwise a floored
scientific comparator is `NUMERICALLY_UNRESOLVED`.

## Numerical uncertainty and classification

For each gain the allowed numerical error is exactly

```text
u_limit(G)=min(0.02,0.02 abs(G)).
```

The conservative absolute estimate is
`u_G=u_integrator+u_sector+u_linear+u_sampling+u_denominator`. Model-form
disagreement is a separate scientific reason, never hidden in this scalar.

Static cases use static metrics; dynamic cases use endpoint and integrated
metrics. Equalization requires both <=0.90, amplification both >=1.10, and
persistence both within `[0.90,1.10]`, always clear after uncertainty and with
required corroboration. One terminal label follows this precedence:

1. authority/artifact invalid;
2. `NUMERICALLY_UNRESOLVED`;
3. uniform/structural control;
4. `INITIAL_CONDITION_DEPENDENT_OR_BISTABLE`;
5. model-form/sector disagreement;
6. metric disagreement;
7. `NEAR_THRESHOLD_TRANSITION`;
8. equalization;
9. amplification;
10. persistence.

All supporting reasons remain attached. Near-threshold and alternate-attractor
results are distinct.

Broad core rows may receive provisional classification. Apparent boundaries,
nomination candidates, steep gradients, and N=8 mode-4 require sector checks;
nomination candidates also require a separately reviewed model-form check.

## Deterministic D4 and X1 materialization

D4 groups every fixed scientific field except Lambda and the alternate initial
variant. Lambda=0 is a comparator and is never log-refined. Positive Lambda is
numeric-ordered. It selects adjacent classification changes, endpoints within
0.01 gain units of either threshold, the two largest absolute gain differences
per `log10 Lambda`, and one deterministic interior per observed regime.
Midpoints are geometric means of strictly positive endpoints. Deduplication is
by canonical parameter identity; generation, group, Lambda, and canonical IDs
resolve ties. At most two rows per interval, three generations, and 4,096 total
are allowed. Global-cap truncation follows the same order. Alternate parents
receive 0.5/1.5 amplitudes and phase reversal; distinct stable states require
separated post-transient observable intervals after numerical uncertainty.

X1 accepts only valid resolved hydraulic regimes. Robust-interior score is
distance from the nearest 0.90/1.10 boundary; boundary score is the inverse
ordering. Ties use uncertainty then case ID. It selects one interior per
observed regime and up to four nearest boundaries, pairs prescribed/machine
only when machine response was material, and caps at 1,000. Absent regimes do
not create replacement rows. Pure selectors are tested on synthetic fixtures
for changes, ties, duplicates, cap exhaustion, Lambda=0, absent regimes, and
boundary selection. They execute no trajectory.

## Verification, budgets, stops, and future nomination

Required future verification covers symmetry, corrected active counterexamples,
self-similar null, Lambda=0, strong coupling, invariance, positive definiteness,
sector scaling, pressure scaling, WP02-002 parity, evolution limits/bounds,
conservation, dissipation, and numerical refinement.

Caps remain 5,000 static/control, 15,000 dynamic, 1,000 extraction, 20,000
adjudicative, and 25,000 absolute. A later separately authorized timing pilot
would use at most 64 cases, 32 processes, one nested thread, target four hours,
review at eight hours, and 16 GiB. No timing pilot occurs here.

Authority, numerical, design, scientific-bounded, boundary-truncation, and
compute stops remain fail-closed. A bounded outcome cannot be rescued by range,
threshold, gain, duration, or complexity changes.

Future nomination is capped at eight hydraulic bases and twelve
prescribed/machine variants. It requires numerical resolution and separately
reviewed model-form corroboration. Any artifact remains
`PROPOSED_SCI_LC_001B_CASES_PENDING_SEPARATE_REVIEW`; none is created here.

Execution remains `NOT_AUTHORIZED`. A second independent read-only exact-head
review is mandatory before any timing pilot, trajectory, classification,
readiness change, or execution adjudication.
