# XSV-ENS-001 stochastic GPU pore-scale closure and RVE protocol

Status: `SCIENTIFIC_COMPLETION_PASS_EXECUTED_PENDING_EXACT_HEAD_REVIEW`
Issue: #64
Change declarations: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; any new
geometry family is `DIAGNOSTIC_GEOMETRY_MODEL_CHANGE`; any LBM extension is
`DIAGNOSTIC_PORE_SCALE_MODEL_CHANGE` with production OpenFOAM integration and
Puckworks lock change both false.

The exact-head scientific-completion protocol and adaptive extension are
recorded in `XSV_ENS_001_COMPLETION_PROTOCOL.json` and
`XSV_ENS_001_COMPLETION_MATRIX.json`. They complete the original frozen seed,
batch, maximum-sample, size-candidate and target rules; they do not redefine
those rules after result exposure.

## Purpose and claim boundary

This two-stage prospective programme measures stochastic variability in the
locked overlapping-sphere generator, finite-volume and voxel-resolution
effects, static-state capability relative to the exact SCI-MD-001 ratios, and
diagonal directional and inertial closures. It is a
`STATIC_STATE_CAPABILITY_COMPARISON` and
`POST_OBSERVATION_TARGET_COMPARISON`, not dynamic-mechanism identification.
The geometries are `NOT_REAL_COFFEE_MICROSTRUCTURE`; numerical qualification
is not physical validation.

## Stage 1: non-scored numerical qualification

The pilot may select only precision, force, stopping tolerance, safe lattice
sizes, process isolation, retry policy, and feasible ensemble breadth. It
reproduces the accepted XSV-TAICHI-002 baseline, compares f32/f64 on identical
masks, checks three low forces, and tests memory with at least 20% nominal VRAM
headroom. A three-level same-continuous-geometry revoxelization is attempted.
Pilot cases are `NON_SCORED_NUMERICAL_QUALIFICATION` and cannot select favorable
morphology states.

f32 is eligible only when paired permeability differs from f64 by at most 1%,
mass/flux semantics pass, Mach is below 0.05, localization CV differs by at
most 5%, and directional ratios (when measured) differ by at most 3%. The
qualified force must keep q/g within 1%, Mach below 0.05, and reach relative
q convergence of 1e-6 after at least 1,500 steps. One transparent retry is
allowed only for allocation or process infrastructure failure.

## Stage 2: scored freeze

The CSV and JSON scored matrices are generated and committed after the pilot
and before scored execution. Frozen primary quantities are gross-area `Kx`,
log-K ensemble spread, connected porosity, size stabilization, and paired or
independent ratios to exact targets `0.373506`, `0.389226`, and `0.395294`.
Secondary quantities are diagonal Ky/Kz, localization, morphology descriptors,
and qualified inertial curvature.

Baseline sizes are selected prospectively from 24, 32, 40, 56, 72, 96, 128,
and 160 voxels subject only to pilot memory/runtime. Independent seeds are
fixed in batches of four from `[101, 211, 307, 401, 503, 601, 701, 809,
907, 1009, 1103, 1201, 1301, 1409, 1511, 1601, 1709, 1801, 1901, 2003,
2111, 2203, 2309, 2411]`. Minimum n is 8, batch n is 4, and maximum n is 24.
Sampling stops when the deterministic-bootstrap 95% interval for mean log K
has a relative half-width no greater than 10%; otherwise it stops at n=24 with
uncertainty unresolved.

Equal seed integers across different non-nested domains are
`RELATED_NON_NESTED`, never paired. Only a deterministic transformation of an
identical parent mask is `PAIRED_TRANSFORMATION`.

The sparse morphology programme includes regenerated solid fractions 0.50,
0.55, 0.60, and 0.64; paired static throat-restriction fractions 0, 0.10,
0.20, 0.30, and 0.40; columnar heterogeneity amplitudes 0, 1, and 2 with
correlation lengths 4 and 8 where applicable; and a resolved bimodal arm only
if the smaller radius spans at least four voxels. Directional subsets use all
three diagonal orientations. Inertial cases are selected deterministically
from frozen baseline 10th/50th/90th-percentile rules plus one transformed and
one heterogeneous state; selection cannot change primary results.

## Frozen adjudication rules

Mean stabilization requires the complete bootstrap interval of the mean-K
ratio to the largest size inside [0.90, 1.10], the adjacent-largest comparison
to pass where available, the sampling precision rule to pass, no monotone
trend over the largest sizes, and no unresolved resolution effect above 10%.
Variance stabilization separately requires CV and IQR changes below 15% and
compatible 10th/90th percentile intervals. Axial, directional, localization,
and inertial conclusions are separate.

Paired target attainment uses geometric-mean K ratios and parent-clustered
bootstrap. Robust attainment requires the 95% upper confidence bound at or
below the exact target and at least 75% of connected pairs attaining it.
Independent states use the ratio of geometric means and independent bootstrap;
they are never artificially paired. Connected porosity retention below 25% of
the parent, or loss of a winding path, is classified as near-connectivity or
topology loss. Disconnected cases remain scientific outcomes.

Primary closure models are grouped by parent geometry: A uses porosity and
particle scale; B adds connected porosity, surface area, pore-distance and
backbone descriptors; C adds fabric, heterogeneity, restriction, and resolved
small-particle descriptors. Five-fold grouped cross-validation (or leave-one-
group-out when fewer groups exist) keeps every orientation and force for a
geometry in one fold. Predictive intervals, residual variance, interpolation
domain, and out-of-domain warnings are required. Exploratory descriptors are
labelled and cannot replace frozen primary descriptors.

## Hydraulic quantity contract

`phi_gross=N_fluid/N_total`; `q_box=sum_fluid(u_x+half-force)/N_total`;
`u_void=q_box/phi_gross`; `nu=(tau_plus-0.5)/3`;
`K_gross=nu*q_box/g`; `K_void=nu*u_void/g`; therefore
`K_gross=phi_gross*K_void`. The primary transfer quantity is `K_gross`.
Axis permutations are X=(0,1,2), Y=(1,0,2), Z=(2,1,0). These are diagonal
components, not a complete permeability tensor.

## Evidence retention

Full masks, velocity fields, and logs remain under the external runtime root.
The repository retains identities, hashes, scalar results, plot-source data,
figures, and compact reports. Failed identities are retained as
`DISCONNECTED_GEOMETRY`, `NONCONVERGED`, `GPU_ALLOCATION_FAILURE`,
`NUMERICAL_INSTABILITY`, `MACH_LIMIT_FAILURE`, `LINEARITY_FAILURE`, or
`DESCRIPTOR_FAILURE`.
