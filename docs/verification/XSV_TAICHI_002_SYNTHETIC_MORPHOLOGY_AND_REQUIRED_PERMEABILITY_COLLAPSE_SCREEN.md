# XSV-TAICHI-002 synthetic morphology and required permeability-collapse screen

## Identity and prospective status

- Authorization: `XSV-TAICHI-002-SYNTHETIC-MORPHOLOGY-COLLAPSE-SCREEN-2026-08-05`
- Profile: `EWP_XSV_TAICHI_002_SYNTHETIC_MORPHOLOGY_COLLAPSE_SCREEN_STAGE_V1`
- Issue: [#60](https://github.com/trbrewer/espresso-whole-pull/issues/60)
- Branch: `verification/xsv-taichi-002-synthetic-morphology-collapse-screen`
- Pull request: `BOOTSTRAP_PENDING`
- Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`
- Evidence: `SIMULATED_SYNTHETIC_REFERENCE` plus an existing governed discrepancy target
- Status: `G0_PROTOCOL_FREEZE_PENDING_EXACT_HEAD_CI`

This is a task-specific, nonreusable human-owner authorization. It permits the
prospectively gated work below, but no OpenFOAM execution, dependency or solver
change, fitting, protected scoring, physical-validation claim, merge, or next
stage. No morphology or retained numerical result may exist before G0 passes.

## Scientific question and evidence role

Can controlled synthetic pore-morphology changes reduce gross-area saturated
permeability, with associated flow-localization changes, by an amount comparable
to the apparent conductance or permeability collapse required by the already
governed adverse multipressure behavior?

The 5/9/11-bar records are an existing discrepancy target, not new independent
validation. A positive synthetic result preserves plausibility without
identifying a real mechanism. A negative result weakens only the exact static
families screened here.

## Locked predecessor and dependency

XSV-TAICHI-001 is merged at `40588d62ee03a31057f75adab1df8a9c609a10d6`
with scientific closure parity established for its exact synthetic fixtures and
the typed package-provenance limitation retained. The Puckworks runtime remains
detached and read-only at commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`. Required source hashes are:

| File | SHA-256 |
|---|---|
| `lb_reference.py` | `9a60371d7777d3d91fe7df2ea529db498268f12b08ab6c461ec511190a0a989f` |
| `lb_taichi.py` | `c0c52eaae0d6f5753eac3b41501db6645251efe56812c152b83ad2a521d9663f` |
| `pack_generator.py` | `864416314c889793684fef0a143cab48f99056b72f715adf1a522298c7d9512b` |

## Quantity contract

`solid == 1`, `fluid == 0`, and

```text
phi_gross = N_fluid/N_total
q_box_lu = sum_fluid(u_x_with_half_force_correction)/N_total
u_void_lu = q_box_lu/phi_gross
nu_lu = (tau_plus-0.5)/3
K_gross_lu = nu_lu*q_box_lu/g_lu
K_void_lu = nu_lu*u_void_lu/g_lu
k_puckworks_returned = K_void_lu
K_gross_lu = phi_gross*k_puckworks_returned
```

Directional connected porosity is diagnostic and never replaces gross
porosity in the permeability definition.

## Prospective required-collapse target

G1 may use only the governed VAL-CORPUS-001 Waszkiewicz 5/9/11-bar source
records, exact pre-existing rows or windows, pressure node, time mapping and
units. No redigitization, new favorable window, model-flow substitution,
nominal-pressure substitution, offset, fit, interpolation rule, density rule,
geometry correction, protected datum, or holdout is permitted.

```text
H_c = Q_c/delta_p_c
T_11_5 = H_11/H_5
T_9_5 = H_9/H_5
T_11_9 = H_11/H_9
target attained when K_case/K_reference <= T_11_5
```

The general corrected permeability ratio is

```text
[(Q_h/delta_p_h)/(Q_l/delta_p_l)]*(mu_h/mu_l)*(L_h/L_l)*(A_l/A_h)
```

and may be used only if every correction term is already governed and
source-linked. Otherwise the target is explicitly an
`APPARENT_HYDRAULIC_CONDUCTANCE_RATIO_TARGET` used in a simplified plausibility
screen. The separate `NOMINAL_PRESSURE_ORDERING_LOWER_BOUND_SCREEN` is
`5/11 = 0.4545454545454545`, corresponding to more than
`54.54545454545454%` collapse under that simplified interpretation.

The derivation is frozen now; numerical target values are populated once in a
separate G1 target-freeze commit before any morphology is generated. If the
existing records cannot supply the target without a new selection rule, the
task stops as `REQUIRED_COLLAPSE_TARGET_NOT_GOVERNABLY_DERIVABLE`.

## Exact synthetic geometry families

The heterogeneity family calls locked `make_pack` with `L=40`,
`voxel_um=30.0`, `gs=1.3`, `phis_target=0.55`, `hetero_len=8.0`, `batch=64`,
`r_um=None`, and `w_floor=0.25`. The exact seeds are `42`, `1729`, and
`20260805`; exact amplitudes are `0.0`, `1.0`, and `2.0`. Seed 42 at amplitude
zero must reproduce XSV-TAICHI-001 M0A payload
`10d9a010cbac4b8579154456c4271ecd2808af5116beab15a2ffd4e2c99cd039`.

The coating family starts from exact M0A. It ranks baseline fluid voxels by
increasing periodic Euclidean distance to baseline solid, then by increasing
SHA-256 of `XSV_TAICHI_002_COATING_V1|x|y|z`. For fraction `f`, exactly
`floor(f*N_void_0+0.5)` ranked fluid voxels become solid. One ranking produces
nested `C05`, `C15`, and `C30` masks at fractions `0.05`, `0.15`, and `0.30`.
There is no repair, smoothing, morphology operation, stochastic replacement,
or result-led selection.

Every unique mask is generated twice and frozen by invocation, configuration
hash, C-order uint8 payload hash, counts, gross porosity, and periodic
six-neighbour winding connected porosity in X/Y/Z. No-path cases are retained,
not repaired, and their affected run identities are topology-censored rather
than replaced.

The solver always forces +x. Physical X/Y/Z use exact transposes `(0,1,2)`,
`(1,0,2)`, and `(2,1,0)` respectively; these self-inverse mappings apply to
mask, connectivity, velocity interpretation and localization.

## Frozen 22-identity CUDA matrix

The authoritative order is
[`XSV_TAICHI_002_CASE_MATRIX.csv`](../../verification/cases/xsv_taichi_002/XSV_TAICHI_002_CASE_MATRIX.csv).
It contains nine paired heterogeneity X/MID runs, three additional coating
X/MID runs, six Y/Z anisotropy additions, and four low/high linearity additions.
`C00-X-MID` is identical to `H-A0-S42-X-MID` and is not duplicated. There are
exactly 22 scored identities and at most 24 total process attempts, allowing
only two exact infrastructure retries with no accepted scientific output.

The exact run order is the CSV order. Baseline `H-A0-S42-X-MID` runs first and
must agree with the frozen M0A `K_gross_lu=1.7919979172502785` within `0.25%`,
with exact mask identity, finite positive flow, convergence, regime gates and
gross-area semantics. Otherwise the campaign stops before run 2 as
`XSV_TAICHI_002_BASELINE_REPRODUCTION_FAILURE`.

All runs use actual Taichi CUDA float64 in fresh processes, `tau_plus=1.2`,
check interval `200`, tolerance `1e-6`, minimum `1500` and maximum `50000`
steps, and forces `5e-7`, `1e-6`, `2e-6`. CPU substitution and a duplicate
NumPy matrix are prohibited.

## Metrics and frozen gates

Primitive-derived per-run metrics include convergence, force, q, void
velocity, gross and connected porosity, gross and void K, returned K, identity
residual, maximum velocity, Mach, Reynolds number, source/mask/environment and
attempt identities, and primitive hashes. Middle-force positive-flow cases
also use the locked `sigma_micro` semantics with `ncol=4`, coefficient of
variation and fastest-quartile flow share. Nonpositive mean flow yields null
localization with a typed reason.

| Gate | Threshold |
|---|---:|
| Mach | `<=0.05` |
| `Re_L` | `<=0.10` |
| returned/gross K identity | `<=1e-12` relative |
| extreme-anchor force fit | `R2>=0.9999` |
| q/g deviation | `<=1%` |
| normalized intercept | `<=0.5%` |
| broadly similar gross porosity | absolute delta `<=0.015` |
| near directional connectivity loss | connected retention `<=0.25` with a path retained |

Linearity is applied only to `H-A2-S42-X` and `C30-X`. An extreme that fails
is retained as `EXTREME_GEOMETRY_STOKES_LINEARITY_NOT_ESTABLISHED`; its
middle-force K is not a qualified target-attainment result.

## Prospective result taxonomy

Constriction is classified as non-attainment, moderate C05/C15 attainment,
severe C30-only attainment, near-connectivity-loss-only attainment, or
post-connectivity-loss crossing. Heterogeneity is classified as non-attainment,
attainment without large gross-porosity change, attainment with material
porosity drift, one-of-three attainment, or robust three-of-three attainment.
Localization reports co-occurrence with bulk collapse, localization change
without collapse, or unqualified nonpositive flow. Anisotropy is descriptive
unless directional connectivity is lost; no prospective threshold authorizes
the adjective “strong.” Multiple bounded family statements may coexist.

The result cannot confirm compaction, fines, migration, deposition, clogging,
channeling, damage, real-coffee morphology/permeability/anisotropy, OpenFOAM
validation, new governing physics, or satisfaction of the independent-data
gate.

## Artifact, plot and chronology policy

The acyclic evidence order is protocol, target freeze, geometry freeze,
execution, raw retention, primitive reduction, result reduction,
self-excluding manifest, archive and hash, committed artifact manifest, then
source manifest. Raw masks, velocity fields, logs and caches remain under the
logical `EXTERNAL_EVIDENCE_ROOT`; committed records contain no host, username
or absolute path. Every derived field binds primitive artifact, field names,
formula/version, units and recomputation tolerance. Both manifest generation
and reduced-package generation repeat byte-identically.

Eight deterministic plots expose individual governed cases, failures and
censoring: K/K0 versus gross and connected porosity; coating response;
paired-seed amplitude response; three localization responses; K/K0 versus
localization; three directional anchors; and two q-versus-force anchors. Each
has a machine-readable source table and distinguishes the governed target from
the nominal screen.

Stages are G0 protocol, G1 target, G2 geometry, G3 CUDA, G4 reduction, G5
synthesis and G6 package. Each stage requires its predecessor. Exact-head
`source-and-boundary` and `inexpensive-checks` must pass at G0 and G2 before
the next retained operation and at the final candidate head.

## Claim ceiling and stop conditions

```text
CURRENT_SCIENTIFIC_GATE: ADDITIONAL_INDEPENDENT_DATA_REQUIRED
PHYSICAL_VALIDATION: NOT_ESTABLISHED
INDEPENDENT_PHYSICAL_DATA: NOT_SUPPLIED_BY_THIS_TASK
OPENFOAM_EXECUTION: NONE_AUTHORIZED
FULL_BASKET_EXECUTION: NOT_AUTHORIZED
EXPLICIT_FINES_PHYSICS: NOT_AUTHORIZED
NEW_GOVERNING_PHYSICS: NOT_AUTHORIZED
PROTECTED_OR_HOLDOUT_SCORING: NOT_AUTHORIZED
MERGE: NOT_AUTHORIZED
NEXT_STAGE: NOT_AUTHORIZED
```

The task stops without scope expansion for any starting/dependency/baseline
identity mismatch, ungovernable or ambiguous target, unavailable CUDA float64,
baseline reproduction failure, source change, desired OpenFOAM/full-basket/
explicit-fines work, desired seed/level/force/threshold/matrix expansion,
attempt 25, protected-data need, physical-validation promotion, XSV-TAICHI-003,
or merge. An unfavorable result is retained and never converted into a tuning
cycle.
