# XSV-TAICHI-001 saturated hydraulic closure parity

## 1. Identity and status

- Task: `XSV-TAICHI-001`
- Authorization: `XSV-TAICHI-001-G5-RADIAL-MESH-ALIGNMENT-2026-08-04`
- Profile: `EWP_XSV_TAICHI_001_G5_RADIAL_MESH_ALIGNMENT_CORRECTION_STAGE_V1`
- Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`
- Evidence class: `SIMULATED_SYNTHETIC_REFERENCE`
- Current status: `XSV_TAICHI_001_EXECUTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW`
- Issue: [#58](https://github.com/trbrewer/espresso-whole-pull/issues/58)
- Branch: `verification/xsv-taichi-001-saturated-hydraulic-closure-parity`
- Pull request: [#59](https://github.com/trbrewer/espresso-whole-pull/pull/59),
  `OPEN_DRAFT_UNMERGED`

### Human-owner staged authorization and task-specific capability profile

The human owner authorized this task-specific, nonreusable profile. It permits
only the prospectively gated synthetic NumPy, Taichi CPU/CUDA and unchanged-
source Foundation OpenFOAM 12 executions declared here. It grants no physics
change, calibration, protected scoring, dependency advance, or merge. It does
not replace independent physical data. Retained numerical execution remains
prohibited until the protocol-first commit and both required exact-head CI
checks pass.

## 2. Why the task is being conducted now

VAL-CORPUS-002 is complete, approved and merged, while the scientific gate
remains `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`. This parallel computational-
verification task qualifies a closure interface before any later morphology
work is considered. It neither satisfies nor weakens that evidence gate.

## 3. Scientific questions

The governed order is: locked NumPy/Taichi backend parity; exact quantity and
reference-volume semantics; analytical channel verification; transfer of one
frozen M0 closure to the continuum gross-area Darcy convention; exact uniform,
series and parallel OpenFOAM composition; and a reusable fail-closed contract.

## 4. Non-purposes and claim ceiling

The work does not represent real coffee morphology, infer real-coffee
permeability, test fines, identify mechanisms, run a full basket, use physical
data, validate espressoWholePullFoam, or establish transfer.

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION: NOT_ESTABLISHED
DIRECT_VALIDATION_OF_ESPRESSO_WHOLE_PULL_FOAM: NO
INDEPENDENT_PHYSICAL_DATA: NO
NEW_GOVERNING_PHYSICS: NOT_YET_JUSTIFIED
```

## 5. Repository and model architecture

Puckworks is a detached, read-only runtime dependency. Its locked D3Q19 TRT
NumPy reference, Taichi implementation and pack generator produce the three
fixed synthetic masks and LBM results. The repository-local runner performs
visible reductions and creates cases for the unchanged current
`espressoWholePullFoam`. Raw products stay outside Git.

## 6. Locked source identities

| Source | Identity |
|---|---|
| espresso-whole-pull start | commit `0dc98b649312108067310a90b9a8f79e636c4adb`; tree `0e981087e27c7e04bdcd0acec2da2ec59c3953d7` |
| Puckworks | commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`; tree `1d553e44ee2f7480a5df521560801b478618cc84` |
| `lb_reference.py` | `9a60371d7777d3d91fe7df2ea529db498268f12b08ab6c461ec511190a0a989f` |
| `lb_taichi.py` | `c0c52eaae0d6f5753eac3b41501db6645251efe56812c152b83ad2a521d9663f` |
| `pack_generator.py` | `864416314c889793684fef0a143cab48f99056b72f715adf1a522298c7d9512b` |
| `espressoWholePullFoam.C` | `a292021a19740e4dd8869a2fa63aaeaa95ea3843016734768b492ca2d2f38dd7` |

## 7. Quantity and reference-volume contract

The mask convention is `solid == 1`, `fluid == 0`. Define

```text
phi_gross = N_fluid / N_total
q_box_lu = sum_fluid(u_x_with_half_force_correction) / N_total
u_void_lu = q_box_lu / phi_gross
nu_lu = (tau_plus - 0.5) / 3
K_gross_lu = nu_lu * q_box_lu / g_lu
K_void_lu = nu_lu * u_void_lu / g_lu
K_void_lu = K_gross_lu / phi_gross
k_puckworks_returned = nu_lu * q_box_lu / (g_lu * phi_gross)
k_puckworks_returned == K_void_lu
```

Connected porosity is a diagnostic and never replaces gross porosity in these
definitions.

## 8. Prospective permeability-adapter hypothesis

The immutable primary adapter is

```text
K_EWP_lu = K_gross_lu
K_EWP_lu = phi_gross * k_puckworks_returned
K_EWP_SI = K_EWP_lu * delta_x_m^2
G_SI = delta_p_Pa / bed_length_m
q_Darcy_SI = K_EWP_SI * G_SI / mu_SI
```

The diagnostic alternate is `K_ALT_lu = k_puckworks_returned`. It cannot be
substituted after exposure. Failure of the primary mapping requires
`REFERENCE_VOLUME_ADAPTER_REJECTED_REQUIRES_SEPARATE_CORRECTION`.

## 9. Fixed geometry definitions and hashes

- `CH33`: `33 x 33 x 33`, flow `+x`, solid walls `z=0,32`, periodic x/y,
  fluid width `h=31`, `phi=31/33`.
- `SP32`: exact locked `lb_reference.sphere_case(L=32, c_nom=0.08)` mask.
- `M0A`: exact locked `make_pack(L=40, voxel_um=30.0, gs=1.3,
  phis_target=0.55, hetero_amp=0.0, hetero_len=8.0, seed=42)` mask.

Payload and configuration hashes, counts, gross porosity and x-connected
porosity are populated only in the separately committed geometry freeze.

## 10. Fixed case matrix

The authoritative matrix is
`verification/cases/xsv_taichi_001/XSV_TAICHI_001_CASE_MATRIX.csv`.
It contains exactly 19 retained LBM runs and eight retained OpenFOAM runs.
LBM uses float64, `tau_plus=1.2`, `nu_lu=(tau_plus-0.5)/3`, check interval
200, relative convergence tolerance `1e-6`, minimum 1500 steps, force levels
`5e-7`, `1e-6`, `2e-6`, and fixed maxima CH33 40000, SP32 30000, M0A
50000. Each Taichi run uses a fresh process.

OpenFOAM uses unchanged source, Foundation 12, prescribed pressure, saturated
Darcy only, zero extraction, constant viscosity `1e-3 Pa s`, density metadata
`1000 kg/m3`, and no machine, wetting, chemistry, compaction, Forchheimer or
dissolution-indexed permeability branch. Uniform target superficial velocities
are `2.5e-4`, `5e-4`, and `1e-3 m/s`. The engineered composition contrast is
`K_B=0.4*K_A` with equal axial lengths. The original exactly equal radial-area
fixture was found pre-solve to be incompatible with the frozen uniform radial
mesh and is superseded by authorized amendment 001 below.

### Authorized protocol amendment 001: mesh-conforming radial interface

The original revision-1 radial fixture used `R/sqrt(2)`, declared area
fractions `0.5/0.5`, and pressure drop `0.5314632027264452 Pa`. Its first
`OF-PARALLEL-1` invocation stopped before time advancement with `Radial
interface does not align with mesh: 0.0002136229947`. It produced no usable
flow result and is permanently retained as
`PROTOCOL_INVALID_PRE_SOLVE_MESH_INTERFACE_MISALIGNMENT`.

Fresh human authorization
`XSV-TAICHI-001-G5-RADIAL-MESH-ALIGNMENT-2026-08-04` selects the unique mesh
face minimizing `abs((j/512)^2 - 0.5)`: face `362`. Revision 2 is therefore
`MESH_CONFORMING_NEAR_EQUAL_AREA`, not exactly equal area:

```text
interface_radius = basket_radius * 362 / 512
interface_radius = 0.0004786795997912995 m
f_inner = (362 / 512)^2 = 0.4998931884765625
f_outer = 1 - f_inner = 0.5001068115234375
K_parallel = f_inner*K_A + f_outer*K_B
K_parallel = 1.1288553286128047e-09 m2
delta_p_parallel = mu*bed_depth*target_q/K_parallel
delta_p_parallel = 0.5315118640909556 Pa
inner_flow_share = 0.7141985132218613
outer_flow_share = 0.2858014867781387
```

The 512-cell uniform radial mesh, grading 1.0, wedge, closure values, target
flow, source, alignment tolerance and all G5 thresholds remain unchanged.
G0-G4 and the valid `OF-SERIES-1` result are accepted and prohibited from
rerun. The case matrix still contains eight governed OpenFOAM identities;
attempt provenance records one invalid pre-solve attempt and raises only the
process-attempt ceiling from eight to nine. The three remaining invocations
are corrected `OF-PARALLEL-1`, unchanged `OF-SERIES-16`, and corrected
`OF-PARALLEL-16`, in that order. This amendment does not change the claim
ceiling or establish physical validation.

## 11. Acceptance gates

- **G0:** exact authority, protocol-first commit, draft PR, source-and-boundary
  and inexpensive-checks PASS before retained execution.
- **G1:** duplicate mask/config hashes, valid porosity and x-through
  connectivity, geometry-freeze commit and exact-head CI PASS.
- **G2:** finite positive results; convergence before maximum; Mach `<=0.05`;
  `Re_L<=0.10`; backend q and K parity `<=0.25%`; mid-force velocity L2
  `<=2%`; channel K errors `<=0.75%`; force fit `R2>=0.9999`, q/g deviation
  `<=1%`, normalized intercept `<=0.5%`.
- **G3:** returned-k identity relative tolerance `1e-12`; primary channel
  error `<=0.75%` and at least five times closer than the alternate.
- **G4:** uniform Q and q errors `<=0.50%`; Q/delta-p deviation `<=0.50%`;
  flux imbalance `<=1e-6`; alternate-porosity flow difference `<=1e-6`.
- **G5:** series/parallel total and share errors `<=1%`; serial/MPI metrics
  `<=1e-8`; flux imbalance `<=1e-6`.
- **G6:** complete matrices, evidence, schemas, deterministic reduction,
  repository qualification, source parity, protected parity and unchanged
  claim ceiling.

Every numerical or infrastructure failure uses the exact typed dispositions
from the human directive. No failed or unfavorable row may be omitted.

## 12. Runtime and artifact policy

Complete evidence lives under a content-addressed logical
`EXTERNAL_EVIDENCE_ROOT`; committed records contain no host, username or
absolute path. The acyclic order is protocol, geometry, execution, raw
retention, reduction, self-excluding manifest, archive, archive hash,
committed result/artifact manifest, then source-manifest regeneration.
CUDA uses one exact bundle, actual CUDA float64, one primary attempt and at
most one identical infrastructure retry.

## 13. Execution chronology

1. Startup identities and read-only dependency: PASS.
2. Issue #58: OPEN.
3. Branch: CREATED_FROM_EXACT_START.
4. Protocol-first commit `55c5335547892e74d58b049121211245b0cf8fd6`
   and draft PR #59: COMPLETE; exact-head G0 CI pending.
5. G0 and G1: PASS.
6. G2: PASS with 19/19 governed LBM cases.
7. G3: `GROSS_AREA_DARCY_ADAPTER_CONFIRMED`.
8. G4: PASS with four uniform OpenFOAM traces.
9. G5: PASS. `OF-SERIES-1`, `OF-SERIES-16`, corrected revision-2
   `OF-PARALLEL-1`, and corrected revision-2 `OF-PARALLEL-16` pass all
   analytical, flux-balance and serial/MPI gates. The original radial
   revision-1 attempt remains retained as
   `PROTOCOL_INVALID_PRE_SOLVE_MESH_INTERFACE_MISALIGNMENT`.
10. G6: PASS. The complete external archive and deterministic reduced package
    are hash-bound; repository qualification is complete pending exact-head CI.

## 14. Numerical results

All 19 LBM cases and eight final OpenFOAM case identities pass. Maximum
NumPy/Taichi permeability disagreement is `2.712603934824874e-6`; maximum
Taichi CPU/CUDA disagreement is `2.582235654693448e-12`; maximum governed
mid-force fluid-cell velocity relative L2 difference is
`2.490029824514269e-4`. Maximum channel permeability error is
`5.188549174506077e-4`, the returned-k identity error is
`3.547176316439907e-16`, and the gross-area adapter is more than 125 times
closer than the alternate.

The M0A origin fit gives `K_gross=1.7919979172502785 lu2` and
`K_EWP=1.6127981255252507e-9 m2`. Uniform OpenFOAM errors are at numerical
roundoff and the porosity-invariance difference is zero at recorded precision.
Series total-flow error is `0.002878157997348123`; its maximum serial/MPI
diagnostic difference is `1.389913098940108e-11`. Corrected radial total-flow
errors are at most `5.148998262299268e-11`, zone-share errors are below
`9.619849887436926e-11`, and serial/MPI differences are below
`1.2016994613028095e-12`. Flux imbalance is below `1e-12` for the composition
fixtures. The complete exact values are governed by
`verification/cases/xsv_taichi_001/XSV_TAICHI_001_RESULT.json`.

Overall disposition:
`XSV_TAICHI_001_CLOSURE_PARITY_ESTABLISHED`. This qualifies only the exact
synthetic saturated-Darcy fixtures and declared closure contract.

## 15. Typed failures, if any

`PROTOCOL_INVALID_PRE_SOLVE_MESH_INTERFACE_MISALIGNMENT` for the original
revision-1 `OF-PARALLEL-1` attempt. It is not a scored flow result.

## 16. Limitations

The three fixtures are synthetic methods controls. M0A is one overlapping-
sphere mask with no fines or representativeness claim. The engineered second
closure is not a second morphology. Reynolds and Mach are numerical-regime
diagnostics. Any later morphology, anisotropy, fines, RVE or full-basket work
requires fresh authority.

## 17. Scientific interpretation

The Taichi/OpenFOAM saturated closure interface, gross-area Darcy adapter,
uniform consumption, axial-series composition, and mesh-conforming near-equal-
area radial composition are qualified for the exact synthetic fixtures only.
The original exact equal-area radial fixture was protocol-invalid for the
frozen mesh; face 362 was selected prospectively without flow-result tuning.
Real-coffee permeability and morphology are not established, fines and full-
basket transfer were not tested, the independent-data gate is unchanged, and
`PHYSICAL_VALIDATION` remains `NOT_ESTABLISHED`.

## 18. Forward decision ladder

Pass permits only recommending
`XSV-TAICHI-002_SYNTHETIC_MORPHOLOGY_AND_REQUIRED_PERMEABILITY_COLLAPSE_SCREEN`
with `AUTHORIZATION: NOT_GRANTED`. Adapter, backend, OpenFOAM, or
infrastructure failure maps to the exact separately unauthorized correction
class in the human directive. In all outcomes the independent-data gate and
human-owner decision remain unchanged.

## 19. Standing instructions for future Taichi/OpenFOAM work

Preserve the exact quantity/reference-volume contract, separate backend
parity from physical validation, bind every closure to geometry/source/unit
hashes, retain failures, and require fresh human authority for every added
geometry, run, threshold, mechanism, physical datum, XSV stage or merge.

## Post-execution exact-head final-package correction

On 5 August 2026, exact-head review of `f9fe87269b351d088fd88e83359a8c34a6dd1fac`
identified that the first final reducer asserted gate and summary PASS values
instead of deriving them fail closed, while `PACKAGE_QA_STATUS.json` retained
stale G0 state. The correction re-reduces the same immutable external archive,
verifies all 1,545 self-excluding manifest members and the archive inventory,
and derives every G0--G5, local-package, run-row, and overall disposition from
the frozen thresholds and retained records. Final exact-head CI remains
external to the committed result and is resolved during review.

No NumPy LBM, Taichi, CUDA, OpenFOAM, blockMesh, checkMesh, geometry generation,
case generation, calibration, refit, or protected scoring was repeated. The
pre-correction result, summary, and artifact-manifest identities remain in Git
history as `d3b3b7d8d5c480160d0d89d60c143e776070b07d5783b47fa38e2660b7fc63c7`,
`5f957575982b6c85f94a5b296b6efaacacf223aafc134a2f08247e903889ed24`, and
`be2cddab2ab952d82930aedb594c4e79af5e23fc5fb1cacc81de8b79be4cf414`.
The corrected identities are bound by `PACKAGE_QA_STATUS.json` and the XSV
artifact manifest at the exact candidate head. The derived scientific outcome
and synthetic-fixture interpretation are unchanged; independent physical data
remain required and `PHYSICAL_VALIDATION` remains `NOT_ESTABLISHED`.

## Post-execution end-to-end closure-lineage correction

On 5 August 2026, review of `ecea08bab9b4210aeb0eda2c32e5037111978882`
found that the reducer did not yet gate the complete M0A-CUDA-to-OpenFOAM
closure handoff or reconstruct every OpenFOAM diagnostic from its retained
primitive structured fields. The correction derives all per-run LBM
quantities, the three-point M0A origin fit, lattice and SI closures, engineered
K_B, porosity, bed depth, gross area and equivalent radius, and binds those
values exactly to the frozen fixture. It also distinguishes the 1,545
self-excluding manifest members from the archive's 1,546 regular files.

Primitive trace reduction retained one new typed integrity failure:
`OF-SERIES-1`'s stored flux-imbalance field does not reproduce from the
mandated `xsv_trace.json` outlet flow and final `traces.csv` inlet flow within
the `1e-12` formula-integrity tolerance. The recomputed imbalance remains far
below the unchanged `1e-6` scientific gate; it was retained without rerun,
retuning or suppression. Consequently the end-to-end closure handoff itself
passes, G5 retains `STRUCTURED_TRACE_DERIVED_FIELD_MISMATCH`, and the overall
package disposition is `XSV_TAICHI_001_COMPLETE_WITH_TYPED_FAILURES`.

No NumPy, Taichi, CUDA, OpenFOAM, blockMesh, checkMesh, geometry, or case
operation was repeated. The pre-correction runtime/result/summary/artifact
hashes remain in Git history as `dee90e1eb2182a968c91844009fa49a4e3be767c2b997b7e1ac6bd9af7b2caa1`,
`93fd6a7604511fb92e94d825f7f21dc41c33627df48d43ca08e0e18076f55ac1`,
`a83080b7ca707b99545bfba6f2f420f6e8f1afa8a8022bfe332325f2fc5a463f`,
and `8794ad07532f3fed953169b318b6d9d874a9a1177247ee03b767cc6d26722f4a`.
The synthetic-only claim ceiling and independent-data gate are unchanged;
`PHYSICAL_VALIDATION` remains `NOT_ESTABLISHED`.
