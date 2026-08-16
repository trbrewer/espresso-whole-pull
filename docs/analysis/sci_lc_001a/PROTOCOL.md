# SCI-LC-001A prospective protocol

Status: `PROSPECTIVE_PROTOCOL_PENDING_INDEPENDENT_PRE_EXECUTION_REVIEW`

Task: `SCI-LC-001A-PROTOCOL-AND-MATRIX-FREEZE`

Work class: `PROSPECTIVE_REDUCED_MODEL_PROTOCOL`

Change: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`

This document and `SCI_LC_001A_PROTOCOL.json` prospectively freeze a diagnostic
reduced-model study. They do not authorize execution. RP-D-LC-001b remains
closed at `NO_UNAMBIGUOUS_BELOW_CANDIDATE`; its synthetic Xi is numerical
context only, not a calibration target, real-puck parameter, or physical prior.

## Question and hypotheses

The controlling question is: under what combinations of lateral conductance,
axial resistance contrast, heterogeneity scale, machine response, and
resistance-evolution timescale does puck nonuniformity decay, persist, or
amplify?

- **H0 — uncoupled persistence.** At zero lateral conductance, fixed positive
  sectors are independent parallel paths and normalized inequality persists
  under a common prescribed-pressure multiplier.
- **H1 — passive lateral equalization.** Some coupling, wavelength, and axial
  placements reduce outlet-flow inequality relative to the exact uncoupled
  counterpart.
- **H2 — passive channel focusing.** Some placements route flow toward low
  downstream resistance and increase outlet inequality.
- **H3 — scale dependence.** Short and long circumferential wavelengths need
  not share a transition.
- **H4 — machine-boundary interaction.** A linear quasi-steady fixed-resistance
  network has pressure/flow amplitude dynamics but structurally invariant
  normalized fractions. Machine response becomes spatially active only with
  storage, nonlinearity, or evolving resistance. This identity is tested.
- **H5 — signed resistance feedback.** High-flow resistance gain is an
  equalizing feedback; high-flow resistance loss is a localizing feedback that
  may amplify or become bistable. This is generic and physically unidentified.
- **H6 — formulation disagreement.** Boundaries and disagreements between
  nested reduced formulations are more valuable future 3-D targets than broad
  regime interiors.

Mechanism discrimination remains the bottleneck. Static lateral paths alone
did not reproduce the observed pressure ordering. Dynamic equalization,
persistence, and localization remain open. No unrestricted fitting is allowed.

## Scope, exclusions, and claim ceiling

The model is `REDUCED_DIAGNOSTIC_PHASE_DIAGRAM`, not production OpenFOAM
physics or physical validation. It excludes fines, swelling, poromechanics,
damage, wetting, thermal physics, and identified chemistry. Extraction is a
secondary diagnostic and never changes the hydraulic classification.

The frozen claim boundary is:

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION: NOT_ESTABLISHED
EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
PROTECTED_OR_HOLDOUT_SCORING: NOT_AUTHORIZED
PRODUCTION_OPENFOAM_PHYSICS_CHANGE: NONE
OPENFOAM_EXECUTION_IN_THIS_TASK: NONE
REAL_PUCK_LATERAL_CONDUCTANCE: NOT_MEASURED
UNIVERSAL_LATERAL_COUPLING_PARAMETER: NOT_ESTABLISHED
RP_D_LC_001B_XI_ROLE: SYNTHETIC_NUMERICAL_CONTEXT_ONLY
SCI_LC_001A_ROLE: REDUCED_DIAGNOSTIC_PHASE_DIAGRAM
```

Eventual claims are limited to the exact reduced formulations, numerical
regimes within frozen ranges, dimensionless sensitivity, model-form
disagreement, bounded null outcomes, and candidates pending separate 3-D
review. Actual channeling, real-coffee timescales, universal boundaries,
measured permeability, improved full-solver prediction, taste, and mechanism
validation remain out of scope.

## Core topology, equations, and units

The core is a periodic ring of `N` equal-area sectors (`a_i=1/N`) with basket
pressure `p_b [Pa]`, outlet pressure `p_o [Pa]`, internal pressure `p_i [Pa]`,
upstream/downstream resistance `R_u_i,R_d_i [Pa s m^-3]`, lateral conductance
`G_L [m^3 s^-1 Pa^-1]`, and optional reduced storage `C_h [m^3 Pa^-1]`:

```text
q_u_i = (p_b - p_i) / R_u_i
q_d_i = (p_i - p_o) / R_d_i
j_i+1/2 = G_L_i+1/2 (p_i - p_i+1)
C_h_i dp_i/dt = q_u_i - q_d_i - j_i+1/2 + j_i-1/2
```

Positive `j_i+1/2` leaves node `i`. Periodic summation cancels every edge once
positive and once negative, so lateral exchange is globally zero. Setting
`C_h=0` gives a positive-conductance linear system. Hydraulic dissipation is
the sum of `q^2 R` and `j^2/G`, hence nonnegative.

The scaled ring operator is

```text
L_N p_i = (N/2pi)^2 (2p_i-p_i-1-p_i+1)
lambda_N(m) = 4(N/2pi)^2 sin^2(pi m/N) -> m^2.
```

`Lambda` multiplies this scaled operator relative to characteristic axial
conductance, so its meaning converges with `N`; an unscaled edge conductance is
not an axis. The mode equalization time is
`tau_L,m=C_h/[G_A Lambda lambda_N(m)]` and `Theta_L=tau_L,m/T_shot`.

The nested model uses conservative `p_i,k`, axial `G_z_i,k`, circumferential
`G_theta_i+1/2,k`, and `C_i,k` balances. It is restricted to S3 checks. Under
the frozen collapse mapping (equipotential nodes within each upstream and
downstream group, series-combined axial conductances, summed colocated storage,
and one exchange plane) it must reproduce the core equations exactly.

## Positive conductance-matched heterogeneity

For deterministic field `h_i`, set

```text
a = log(chi_R)/(max(h)-min(h))
g_raw_i = exp(-a h_i)
G_i/G_0 = g_raw_i / sum_j(a_j g_raw_j)
R_i = 1/G_i
chi_R = R_max/R_min.
```

Thus parallel area-weighted conductance equals `G_0`, positivity is exact, and
rotation cannot change the baseline. Uniform `chi_R=1` is a control. Placement
uses strictly positive splits `R_u/R=(0.95,0.50,0.05)` for
`UPSTREAM,DISTRIBUTED,DOWNSTREAM`; `R_d=R-R_u`. The small endpoint offset is a
deliberate positivity-preserving substitute for zero-resistance endpoints.

Primary fields are `cos(2 pi m i/N + phase)`. Robustness uses a half-ring block,
its rotation, and deterministic seed `20260816` with a two-sector correlation
scale. Modes are valid only for `m<=N/2`; physical wavelength and mode identity
are reported separately.

## Boundaries, storage, and resistance evolution

The prescribed boundary is a deterministic dimensionless ramp over the unit
shot horizon. In the static linear model, multiplying applied pressure scales
all flows and leaves fractions unchanged; no redundant pressure-amplitude sweep
is scientific evidence.

The machine boundary reuses WP02-002:

```text
C_u dp_u/dt = Q_supply(p_u,t) - Q_puck
p_b = p_u - R_u Q_puck.
```

Upstream, basket, and outlet pressures; supply and puck flows; and compliance
storage remain distinct. `Theta_M=tau_machine/T_shot`. Local storage is labeled
`REDUCED_HYDRAULIC_STORAGE_DIAGNOSTIC`, not measured compressibility.

Dynamic resistance uses only
`SIGNED_LOCAL_FLOW_TO_RESISTANCE_FEEDBACK_SURROGATE`:

```text
Theta_R dx_i/d(t/T_shot) = s(F_i-1)-x_i
R_i(t)=R_i0 exp(beta x_i),   F_i=(q_d_i/sum q_d)/a_i.
```

`s=+1,0,-1` means equalizing, none, localizing. `beta=0` and
`Theta_R=INFINITE_NO_EVOLUTION` recover fixed resistance. The future executor
must stop, not clip, outside frozen positive resistance bounds. A small finite
`Theta_R` checks the algebraic fast-relaxation limit; zero is never integrated.

## Dimensionless basis

| Group | Definition | Meaning and active arms |
|---|---|---|
| `Lambda` | scaled `G_L/G_A` | lateral/axial coupling; S1–D3 |
| `chi_R` | `R_max/R_min=exp(a Delta h)` | positive contrast; all heterogeneous arms |
| `kappa_h` | mode `m` / inverse normalized wavelength | heterogeneity scale |
| placement | positive resistance split category | location relative to exchange |
| `Theta_L` | `tau_lateral/T_shot` | storage/equalization; D1–D3 |
| `Theta_M` | `tau_machine/T_shot` | machine response; D2 |
| `Theta_R` | `tau_resistance/T_shot` | feedback relaxation; D3 |
| `beta,s` | log-resistance gain and sign | feedback magnitude/direction; D3 |

Absolute pressure is structurally inactive in normalized fixed linear spatial
observables. The unit shot horizon may later map to 30 s only as an EWP design
convention, never a universal duration.

## Staged matrix

Canonical levels are `N={4,8,16}`, `chi_R={1,1.25,1.5,2,4,8,16}`,
`Lambda={0,1e-4,3e-4,1e-3,3e-3,1e-2,3e-2,1e-1,3e-1,1,3,10,30,100}`,
N=8 modes `{1,2,4}`, three placements, `Theta_L={.01,.03,.1,.3,1,3,10,30}`,
`Theta_M={.03,.1,.3,1,3,10}`, `Theta_R={.03,.1,.3,1,3,10,infinity}`,
and `beta={0,.25,.5,1,2}` with nonredundant sign combinations.

- C0 freezes analytical/invariance controls.
- S1 is the complete N=8 Fourier static atlas over six heterogeneous contrasts.
- S2 is a bounded block/rotation/broadband robustness subset.
- S3 is a prospectively selected N and axial-form check, not a broad factorial.
- D1 adds storage to fixed static representatives.
- D2 uses storage-enabled cases plus matched prescribed controls; it tests H4.
- D3-EQ and D3-LOC apply one feedback sign at a time.
- D4 is generated only from frozen adaptive rules after reviewed parent results.
- X1 applies the existing bounded one-solute diagnostic only to selected
  hydraulic representatives. It cannot alter classification.

The generator is the count authority. It currently emits 1,271 initial rows
and zero D4/X1 result-selected rows. D4 is capped at 4,096 and X1 at 1,000, for
a prospective maximum of 6,367. Each row uses explicit `NOT_APPLICABLE`, a
canonical case ID, scientific/control role, eligibility, parent rule, and hash.

## Observables

Primitive histories are `p_b,p_u,p_i,q_u_i,q_d_i,j_edge,R_u_i,R_d_i,x_i`,
`Q_total,Q_supply`. With `f_i=q_d_i/sum(q_d)` and area fraction `a_i`, record
`F_i=f_i/a_i`, extrema, positive flow ratio,
`H_q=0.5 sum|f_i-a_i|`, area-weighted `CV_q`, and
`A_eff=1/sum(f_i^2/a_i)`. Near-zero denominators use a frozen seeded-mode floor.

Fourier cases record complex resistance, pressure, and flow mode amplitude and
phase. Record `sum|j|/Q`, signed lateral cancellation, pressure CV/range/mode,
dominant region, persistence, switches, and angular drift. At `t_ref/T=0.1`:

```text
G_time_end=H_q(T)/H_q(t_ref)
G_time_int=int H_q dt/[H_q(t_ref)(T-t_ref)]
G_coupling_end=H_q(T;Lambda)/H_q(T;0)
G_coupling_int=int H_q(Lambda)dt/int H_q(0)dt
sigma_m=slope(log(max(|A_m|,A_floor))), t/T in [0.2,0.8].
```

Also record node/global/machine residuals, dissipation, condition estimate,
positivity, finiteness, integrator state, and refinement comparisons. Selected
X1 cases report sector extraction fraction/CV/maldistribution, mass shares,
aggregate yield, cup/solute totals, and water/solute conservation; aggregate
mass cannot prove a mechanism.

## Prospective classification

The materiality band is frozen at 10% (`0.90`, `1.10`). Primary-gain numerical
uncertainty must be no more than 0.02 absolute or 2% relative, using the more
conservative applicable test.

- `LATERAL_EQUALIZATION`: both coupling gains <=0.90, corroborating seeded-mode
  attenuation, no alternate amplification, and accepted formulation agreement.
- `HETEROGENEITY_PERSISTS`: both gains in [0.90,1.10], near-zero growth,
  initial-condition consistency, and formulation agreement.
- `HETEROGENEITY_AMPLIFIES`: both gains >=1.10, consistent growth, no denominator
  collapse, valid resistance bounds, and uncertainty clear of threshold.
- `TRANSITION_OR_BISTABLE_REGION`: threshold straddle, metric/model/sector
  disagreement, initial-condition dependence, distinct attractors, refined
  transition, or machine/prescribed divergence. Reason codes are
  `NEAR_MATERIALITY_BOUNDARY`, `METRIC_DISAGREEMENT`,
  `MODEL_FORM_DISAGREEMENT`, `SECTOR_RESOLUTION_DISAGREEMENT`,
  `INITIAL_CONDITION_DEPENDENCE`, `BISTABILITY_EVIDENCE`, and
  `MIXED_COUPLING_AND_EVOLUTION_EFFECT`.

Validity failure is `NUMERICALLY_UNRESOLVED`, not bistability. Uniform and
analytical controls use `UNIFORM_SYMMETRY_CONTROL` or `STRUCTURAL_IDENTITY`.

## Verification and validity

Future implementation must prove uniform symmetry; exact Lambda=0 parallel
paths and radial-reference metrics; strong-coupling equipotential approach;
rotation/reflection invariance; sector convergence at fixed physical mode;
core/multilayer collapse; linear pressure scaling; WP02-002 machine parity;
no-evolution and fast-relaxation limits; passive dissipation; local/global,
lateral, machine, water, and solute conservation. Base/refined timesteps,
sectors, and formulations must satisfy the frozen uncertainty bound. Tolerances
cannot be chosen after results.

## Adaptive rules and budget

Within fixed scale/contrast/placement/formulation, D4 orders parents by
`log10(Lambda)` and selects adjacent classification changes, cases within 10%
of a boundary, the two largest finite differences, and one interior member per
observed regime. It deduplicates canonical identity, inserts log midpoints,
allows at most two new rows per interval and three generations, and never adds
points merely to force a desired regime. X1 selects one robust interior per
observed regime and selected boundaries only.

Caps are 5,000 static/control, 15,000 dynamic, 1,000 extraction, 20,000 total
adjudicative, and 25,000 absolute. A later non-adjudicative timing pilot uses at
most 64 representative cases, 32 worker processes, one nested-library thread,
target <=4 h, review at 8 h, and <=16 GiB. Prediction above any hard limit,
unstable scaling, serialization excess, or need for OpenFOAM stops before sweep.

## Stop rules

- `AUTHORITY_STOP`: head/tree, protocol/matrix hash, claim ceiling, lock,
  generator/artifact, independent-review, competing-protocol, or dirty-checkout
  mismatch.
- `NUMERICAL_STOP`: nonfinite/nonpositive states, balance/dissipation/integrator
  failure, singularity outside a declared limit, invariance/refinement failure,
  artificial bound, or clipping dependence.
- `DESIGN_STOP`: redundant axes, inadequate topology, nonconvergent ring scaling,
  placement confounding, universally inactive machine arm, new chemistry need,
  or budget excess.
- `SCIENTIFIC_BOUNDED_STOP`: no amplification/equalization/bistability,
  persistence only, or structurally inactive machine response within range.
- `COMPUTE_STOP`: time, disk, memory, recurrent workers, or budget mismatch.

An outer-level boundary is open/truncated and cannot be extrapolated. A bounded
result cannot be rescued by extending ranges, complexity, duration, gain, or
thresholds without a new reviewed tranche.

## Future SCI-LC-001B nomination

Only robust equalizing, persistent, and (if present) amplifying interiors; up to
two important-boundary cases; formulation disagreements; and materially
different machine variants may be nominated. Diversity across regime, scale,
placement, coupling, contrast, machine response, and evolution is required.
The cap is eight hydraulic bases and twelve prescribed/machine variants.
Unresolved, redundant, attractive-figure-only, post-hoc adjusted, or
extraction-only cases are excluded. Any artifact is
`PROPOSED_SCI_LC_001B_CASES_PENDING_SEPARATE_REVIEW`, never OpenFOAM authority.

## Outcomes, artifacts, and restart block

Possible outcomes are `SCI_LC_001A_PHASE_DIAGRAM_COMPLETE`,
`SCI_LC_001A_EQUALIZATION_AND_PERSISTENCE_REGIONS_IDENTIFIED`,
`SCI_LC_001A_AMPLIFICATION_REGION_IDENTIFIED`,
`SCI_LC_001A_TRANSITION_OR_BISTABILITY_IDENTIFIED`,
`SCI_LC_001A_NO_AMPLIFICATION_WITHIN_FROZEN_RANGE`,
`SCI_LC_001A_REDUCED_FORMULATIONS_DISAGREE`,
`SCI_LC_001A_PARAMETER_RANGE_TRUNCATED`, `SCI_LC_001A_NUMERICALLY_UNRESOLVED`,
or `SCI_LC_001A_PROTOCOL_OR_AUTHORITY_FAILURE`. Findings may coexist, but a
future run has one terminal disposition and separates mathematical,
verification, reduced observation, 3-D, experiment, and unidentified claims.

Future results require immutable authority, per-case records, canonical hashes,
manifests, provenance, validity, classification, and zero-overwrite resume.
Resume is forbidden on authority, schema, row, hash, dependency, malformed-file,
or validity mismatch. This draft itself has no result schema instance.

Execution is `NOT_STARTED`. Independent read-only pre-execution review of the
question, topology, equations, groups, matrix, observables, thresholds,
validity, adaptivity, budget, stops, nomination, and claims is mandatory before
any simulation or readiness change.
