# VAL-CASE-001 frozen protocol

## Identity and authority

- Case: `VAL-CASE-001`
- Issue: `#41`
- Evidence class: `EXPLORATORY`
- Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`
- Scientific purpose: `VALIDATION_DESIGN_AND_PRACTICAL_IDENTIFIABILITY`
- Base commit/tree: `39c7bf0658c344728258ba1b4f8b935a4e889d7d` / `85711011a96ebaa46a77b5165aec0ab46e676542`
- Validation-framework pin: merge commit `a3e632d9deb3c4ac7c34fed079e4ed85bd370a30`, tree `3de55debf9272fb6bdac928a415996fd9e1fb8e9`
- Operating-standard pin: merge commit `39c7bf0658c344728258ba1b4f8b935a4e889d7d`, tree `85711011a96ebaa46a77b5165aec0ab46e676542`
- Puckworks lock: commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree `1d553e44ee2f7480a5df521560801b478618cc84`
- Human-owner authority: parent workspace `AGENTS.md`, SHA-256
  `224fb9f5e7a428a48cd244276daebd3fd21a5ea2e634f194ede0333cd9227c3d`
- External artifact logical identity: `VAL-CASE-001-OPENFOAM12-20260801`
- External artifact location recorded publicly as: `EXTERNAL_RUNTIME_ROOT/VAL-CASE-001-OPENFOAM12-20260801`; the host path is excluded from Git.

This protocol is frozen by a dedicated pre-execution commit. The full commit
and tree are recorded after commit creation without amending this file.

## Scientific questions and claim ceiling

The case screens local influence, practical confounding, observable
information value, and existing universal-versus-finite-porosity branch
separation for the merged hydraulic, machine, and quasi-static-compaction
model. It recommends measurements for a later independently authorized case.
It performs no external-data score, fit, retuning, experiment, protected or
holdout access, framework change, solver change, baseline-configuration
change, or governing-physics change.

`CLAIM_CEILING: VALIDATION_SUPPORT_ONLY`

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`

`STRUCTURAL_IDENTIFIABILITY: NOT_ASSESSED`

## Bound inputs and model branches

| Role | Path | SHA-256 |
|---|---|---|
| R0 scenario parent | `config/reference_R0.json` | `67a3d9e226f5e66a598a9594c6aedf0809eefe8e80745ae142d2812784b7a286` |
| machine definition parent | `validation/wp02/WP02_002_MACHINE_PUCK_COUPLING_RUN_SPEC.json` | `6a9128a1f98ca8b3f87b45592e8d21dda3d77f7325aef43230cdef94402461d4` |
| compaction definition parent | `validation/wp03/WP03_001_POROELASTIC_COMPACTION_RUN_SPEC.json` | `dc687f13c8881c481d5674a226c0236d0f0a3d1e53458a9ea5558b02dfcb3456` |

The existing `none` bed-mechanics branch is the universal pressure-flow
branch. The existing `waszkiewiczQuasiStaticCompaction` /
`waszkiewicz2025FinitePhi` branch is the finite-porosity branch. The middle
machine-coupled parents are existing PE-6 and PE-7 constructions. The
prescribed-pressure information conditions are existing PE-4 (5 bar), PE-3
(9 bar), and PE-5 (11 bar). Derived JSON inputs never modify these parents.

## Parameter inventory and perturbations

The principal classification is shown below. Bounds are contract/domain
bounds, not uncertainty intervals. Every continuous variation is an
exploratory derivative probe.

| ID | Name (symbol) | Units | Baseline | Classification | Admissible domain | Primary probe | Component / expected observables |
|---|---|---:|---:|---|---|---|---|
| `k0` | stress-free permeability, `k_0` | m2 | `4.74023506749502e-15` | `CALIBRATED_PREVIOUSLY` | strictly positive | central +/-5%; half +/-2.5% if selected | finite-porosity hydraulic resistance; flow, mass, pressure |
| `pc` | critical compaction pressure, `p_c` | Pa | `1239155` | `SOURCE_DERIVED` | positive and greater than maximum applied bed drop | central +/-5%; half +/-2.5% if selected | stress normalization and finite-porosity closure; flow, pressure, deformation |
| `phi0` | stress-free porosity, `phi_0` | 1 | `0.4` | `FIXED_PREDECESSOR_VALUE` | `0 < phi_0 < 1` | central +/-5%; half +/-2.5% if selected | finite-porosity closure; porosity and deformation, flow |
| `Cu` | upstream compliance, `C_u` | m3/Pa | `2e-11` | `UNCERTAIN_MODEL_INPUT` | strictly positive | central +/-5%; half +/-2.5% if selected | machine storage; first drip, upstream/basket pressure, flow |
| `Ru` | upstream resistance, `R_u` | Pa s/m3 | `2e11` | `UNCERTAIN_MODEL_INPUT` | nonnegative | central +/-5%; half +/-2.5% if selected | machine pressure-node separation; basket pressure and flow |
| `Qfree` | free supply flow, `Q_free` | m3/s | `6e-6` | `UNCERTAIN_MODEL_INPUT` | strictly positive | central +/-5%; half +/-2.5% if selected | supply curve; pressure, flow, first drip |
| `pshut` | shutoff pressure, `p_shut` | Pa gauge | `1.2e6` | `UNCERTAIN_MODEL_INPUT` | above outlet and initial pressure; compaction drop remains below `p_c` | central +/-5%; half +/-2.5% if selected | supply curve; pressure, flow, deformation, first drip |
| `mechanics` | universal / finite-porosity model form | branch | finite-porosity reference | `MODEL_FORM_SWITCH` | existing branches only | discrete comparison, never differentiated | hydraulic and deformation outputs |
| `mu` | dynamic viscosity | Pa s | `3.15e-4` | `SOURCE_MEASURED` | positive | `NOT_VARIED` | excluded to keep source condition fixed |
| `rho` | liquid density | kg/m3 | `965` | `SOURCE_MEASURED` | positive | `NOT_VARIED` | excluded to keep source condition fixed |
| wetting permeability | wetting Darcy permeability | m2 | `1.77e-15` | `CALIBRATED_PREVIOUSLY` | positive | `NOT_VARIED` | excluded because the case targets saturated hydraulic/compaction discrimination |
| extraction constants | inherited extraction inputs | mixed | parent values | `FIXED_PREDECESSOR_VALUE` | predecessor contract | `NOT_VARIED` | contextual only; no chemistry inference |

Known or suspected correlations are `k0` with `pc`, `pc` with `phi0`, and
`Cu` with `Qfree`; `Ru`, `Qfree`, and `pshut` may jointly shape the machine
operating point. The analysis reports measured local correlations rather than
assuming those expectations are true.

## Prospective run matrix (47 executions)

1. Stage A uses the existing PE-7 middle machine/finite-porosity construction:
   one baseline, one exact repeat, seven +/-5% central pairs, and one PE-6
   universal-branch baseline: 17 runs.
2. Stage B selects exactly three parameters by descending maximum absolute
   normalized sensitivity across the primary compact features (ties broken by
   parameter ID) and runs their +/-2.5% pairs at the Stage-A condition: 6 runs.
3. Stage C uses the existing 5, 9, and 11 bar PE-4/PE-3/PE-5 conditions. At
   each condition it runs finite and universal baselines plus +/-5% pairs for
   `k0`, `pc`, and `phi0`: 8 per condition, 24 runs.

Planned OpenFOAM executions: `17 + 6 + 24 = 47`. No result-dependent case is
added or removed. A failed infrastructure attempt is invalidated and the
identical whole case may be rerun; scientific input may not change.

## Observables and common support

All values come from the existing `postProcessing/wholePull/0/traces.csv`.
The time origin is solver start. Linear interpolation is used at physical
times 10, 15, 20, 25, and 30 s; every valid full-shot case must span them.
Trapezoidal integrals use physical time, preventing dense sampling from
acquiring extra weight.

| Set | Observable | Definition / units / node or basis | Characteristic scale |
|---|---|---|---:|
| A | outlet liquid volume flow | `outlet_flow_m3_s`, basket-bottom outlet face integral, m3/s | `1.5e-6 m3/s` |
| A | cumulative delivered beverage mass | `cup_beverage_mass_kg`, cup accumulation, kg | `0.04 kg` |
| B | basket pressure | `basketPressurePa`, coffee-bed top gauge pressure, Pa; pump/upstream pressure is not substituted | `9e5 Pa` |
| C | deformation | `1 - predictedBedHeightRatio`, volume-weighted fixed-reference-mesh diagnostic, dimensionless | `0.1` |
| C | mechanical porosity | `volumeWeightedMechanicalPorosity`, coffee-bed volume weighted, dimensionless | `0.4` |
| D | physical first drip | `first_drip_s`, sharp-front arrival interpolated by existing solver, s | `10 s` |

Machine-side `upstreamPressurePa` is retained as a separate diagnostic and
measurement-design observable, not substituted for basket pressure. SET_D is
available. No new solver instrumentation is added.

## Sensitivity and practical-identifiability methods

For parameter `p` and physical observable feature `y`, the primary derivative
is `(y_plus - y_minus)/(p_plus - p_minus)`. Residual/change is always
perturbed minus baseline. One-sided formulas are implemented and tested but
are not planned because all frozen probes are interior. The normalized
sensitivity is `(p/scale_y) dy/dp`, using the fixed characteristic scale above
rather than dividing by a near-zero output. Positive parameters additionally
use the equivalent local logarithmic sensitivity where the output is positive.
Physical-unit derivatives remain primary; features are never collapsed to a
single scientific score.

Each observable set forms a scale-normalized Jacobian whose rows are the
equally represented compact physical-time features and whose columns are the
eligible parameters for that condition. SVD uses double precision. Reported
effective rank is the range obtained at relative singular-value tolerances
`1e-2`, `1e-3`, `1e-4`, and `1e-6`. A condition number is reported only when
the smallest singular value is positive and finite. Parameter sensitivity
correlations use centered column correlation when defined and cosine
similarity otherwise; absolute value at least 0.95 is flagged near-collinear.
No measurement uncertainty, confidence interval, Fisher-information claim,
formal identifiability claim, or structural-identifiability claim is made.

Stage-A influence ranking is the maximum absolute normalized sensitivity over
all available SET_A--SET_D compact features. Derivative stability is the
half-step derivative divided by the primary derivative where the primary is
nonzero, with sign agreement reported separately. Numerical repeatability is
the maximum absolute and scale-normalized difference between the two exact
Stage-A baseline traces on the common support.

Branch separation is finite-porosity minus universal for matched conditions.
It is reported in physical units, relative to fixed output scale, and relative
to the maximum exact-repeat difference. The implied future precision target is
the absolute separation; it is not a validation threshold or invented sensor
uncertainty. `EXPERIMENTAL_VARIANT_DISCRIMINATION: NOT_ASSESSED`.

## Evidence, stop, invalidation, and interpretation

No external observations are scored. The locked records are inspected only
to determine whether a future admissible independent dataset exists. In their
absence the disposition is
`NO_ADDITIONAL_ADMISSIBLE_INDEPENDENT_DATASET_AT_LOCKED_EVIDENCE_STATE`.
EXP-004, EXP-001, EXP-002, and EXP-003 remain planning links only.

Stop before execution for any pin/hash mismatch, parent mutation, framework or
operating-standard diff, solver-source diff, run count above 80, unsupported
parameter value, inability to use Foundation OpenFOAM 12, or inability to
retain complete external products. After execution, a material method/data
defect invalidates affected results and permits at most one bounded correction
addendum and complete affected rerun. Metadata-only defects use an addendum;
general reusable improvements are `VALIDATION_INFRASTRUCTURE_BACKLOG`.

Required case statements are:

`PRACTICAL_IDENTIFIABILITY: SCREENING_ONLY_WITHOUT_MEASUREMENT_UNCERTAINTY`

`VALIDATION_FRAMEWORK_DISPOSITION: PINNED_FRAMEWORK_USED_UNCHANGED`

`EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED`

`PROTECTED_OR_HOLDOUT_SCORING: NOT_AUTHORIZED`
