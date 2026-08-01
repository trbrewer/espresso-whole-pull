# VAL-CASE-001 hydraulic/compaction sensitivity and practical identifiability

## Disposition and scope

VAL-CASE-001 completed the prospectively frozen exploratory, model-internal
sensitivity campaign with one bounded correction for inadmissible pressure
probe endpoints. Forty-seven valid Foundation OpenFOAM 12 cases completed at
32 ranks. Two originally completed 5% endpoints were invalidated, and two
opposite endpoints failed during case preparation before OpenFOAM launch. The
replacement matrix completed without a failed OpenFOAM run. No observation
was fitted, retuned, or scored.

```text
SCIENTIFIC_RESULT_DISPOSITION:
  VALIDATION_SUPPORT_SENSITIVITY_AND_IDENTIFIABILITY_SCREENING

VALIDATION_FRAMEWORK_DISPOSITION:
  PINNED_FRAMEWORK_USED_UNCHANGED

CLAIM_CEILING:
  VALIDATION_SUPPORT_ONLY_PHYSICAL_VALIDATION_NOT_ESTABLISHED
```

`PRACTICAL_IDENTIFIABILITY: SCREENING_ONLY_WITHOUT_MEASUREMENT_UNCERTAINTY`

`STRUCTURAL_IDENTIFIABILITY: NOT_ASSESSED`

## Identities and execution

- Base: `39c7bf0658c344728258ba1b4f8b935a4e889d7d`, tree
  `85711011a96ebaa46a77b5165aec0ab46e676542`.
- Frozen protocol: `b5ffc581b79adfc9807face27777a0ae9dc582f8`,
  tree `85827508b6b5c23eaca020c8e36ae20b54023aa0`.
- Framework: `a3e632d9deb3c4ac7c34fed079e4ed85bd370a30`,
  tree `3de55debf9272fb6bdac928a415996fd9e1fb8e9`, unchanged.
- Operating standard: `39c7bf0658c344728258ba1b4f8b935a4e889d7d`,
  tree `85711011a96ebaa46a77b5165aec0ab46e676542`, unchanged.
- Executable SHA-256:
  `0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c`.
- External artifact: `VAL-CASE-001-OPENFOAM12-20260801`; 856,193
  files, 26,087,704,396 bytes, aggregate SHA-256
  `a1a9814ad043c1b33186ea5783f26eafc6cb4006d910984cbe23c4c37a9ae6b8`.
- Planned/valid completed OpenFOAM runs: 47/47. Total launches including two
  invalidated completed endpoints: 49. Failed OpenFOAM runs: zero. Failed
  pre-launch preparations: two.

The exact-repeat finite-porosity machine baseline matched in every compact
feature: maximum absolute and fixed-scale-normalized differences were both
zero.

## Local sensitivity and derivative stability

The Stage-A ranking by maximum absolute fixed-scale normalized sensitivity was:

| Rank | Parameter | Maximum absolute normalized sensitivity |
|---:|---|---:|
| 1 | stress-free porosity `phi0` | 0.94235 |
| 2 | machine shutoff pressure `pshut` | 0.81656 |
| 3 | stress-free permeability `k0` | 0.76623 |
| 4 | critical compaction pressure `pc` | 0.57165 |
| 5 | free supply flow `Qfree` | 0.35487 |
| 6 | upstream resistance `Ru` | 0.24803 |
| 7 | upstream compliance `Cu` | 0.24106 |

This is a maximum-over-features screening rank, not an uncertainty or
importance distribution. At 30 s, flow was most sensitive to `k0` (0.7448),
then `pc` (0.5316), while basket pressure was most sensitive to `pshut`
(0.8166). Deformation was most sensitive to `phi0` (0.7498) and `pc`
(-0.5716). First drip was insensitive to the saturated compaction inputs in
this model, but responded to `Qfree` (-0.3549), `pshut` (-0.2471), `Cu`
(0.2411), and `Ru` (0.1893).

The frozen top-three half-step checks had 100% derivative-sign agreement.
Median magnitude ratios were 0.999998 (`phi0`), 1.000117 (`pshut`), and
1.000094 (`k0`). Maximum absolute ratio-minus-one values were respectively
`2.31e-5`, `6.95e-3`, and `1.06e-3`. The local derivatives are stable at the
declared probe scales.

## Observable information and practical confounding

| Observable set | Jacobian | Singular-value range | Condition number | Effective-rank range (`1e-2` to `1e-6`) |
|---|---:|---|---:|---:|
| SET_A: flow and delivered mass | 10 x 7 | 2.510 to `6.30e-6` | 398,233 | 3--7 |
| SET_B: SET_A + basket pressure | 15 x 7 | 2.631 to `1.86e-5` | 141,581 | 4--7 |
| SET_C: SET_B + deformation/porosity | 25 x 7 | 3.147 to `9.48e-4` | 3,318 | 5--7 |
| SET_D: SET_C + first drip | 26 x 7 | 3.151 to `1.92e-3` | 1,637 | 5--7 |

At the more interpretable `1e-3` relative tolerance, effective rank rises
from 4 for SET_A and SET_B to 5 for SET_C and 6 for SET_D. Flow alone is
practically insufficient. Basket pressure materially improves conditioning
and the conservative lower rank. Deformation breaks the nearly exact
`k0`/`pc`/`phi0` hydraulic collinearity. First drip adds machine-boundary
information but no saturated-compaction information under the unchanged
wetting-isolation contract.

SET_A has near-collinear `k0`/`pc`/`phi0` sensitivities (cosines 0.99975,
0.99988, and 0.99998), plus machine-side `Qfree`/`Ru` (-0.98069) and
`Ru`/`pshut` (-0.97310) confounding. Pressure removes several cross-group
near-collinearities but retains the two machine pairs and compaction triple.
Adding deformation removes the compaction-triple near-collinearity; adding
first drip reduces but does not eliminate `Qfree`/`Ru` and `Ru`/`pshut`
confounding.

The prescribed-pressure condition screen for `k0`, `pc`, and `phi0` was most
well conditioned at 5 bar: condition number 3.49 and rank 3 at every declared
tolerance. The 9-bar condition has condition number 15.8 and rank 3. At 11 bar,
`k0` and `pc` become nearly collinear (cosine 0.99987), the condition number
rises to 145, and rank ranges 2--3. Thus low plus middle pressure is more
informative for separating these local compaction parameters than high
pressure alone.

Supported screening categories are:

- `FLOW_ONLY_OBSERVABLES_PRACTICALLY_INSUFFICIENT`;
- `PRESSURE_PLUS_FLOW_IMPROVES_INFORMATION`;
- `DEFORMATION_OBSERVABLE_REQUIRED_FOR_DISCRIMINATION`;
- `FIRST_DRIP_OBSERVABLE_ADDS_INFORMATION` for machine-boundary parameters;
- `PARAMETER_GROUPS_PRACTICALLY_CONFOUNDED`; and
- `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`.

## Existing model-form separation

The universal and finite-porosity branches differ well above the exact-repeat
floor, but no independent measurement uncertainty is available:

| Condition | Flow separation at 30 s | Delivered-mass separation at 30 s | Basket-pressure separation | Bed-height-ratio separation |
|---|---:|---:|---:|---:|
| prescribed 5 bar | +0.4508 mL/s | +11.016 g | 0 Pa (prescribed node) | 0.06336 |
| prescribed 9 bar | approximately 0 | approximately 0 | 0 Pa (prescribed node) | 0.08334 |
| prescribed 11 bar | -0.3187 mL/s | -8.168 g | 0 Pa (prescribed node) | 0.08498 |
| machine middle | +0.2042 mL/s | +4.820 g | -81.70 kPa at 30 s | 0.07366 |

The 9-bar hydraulic identity is expected from the predecessor's matched
construction and does not establish physical equivalence. Maximum deformation
separation occurs at 11 bar. Maximum declared flow/mass separation occurs at
5 bar. Machine coupling makes basket pressure additionally discriminating.
All branch separations exceed zero numerical repeatability, but measurability
cannot be assessed without sensor and preparation uncertainty.

Future design targets should resolve substantially less than the predicted
signals; a useful initial target is about 10% of the smallest relevant
machine-condition separation: basket pressure around 8 kPa, flow around
0.02 mL/s, delivered mass around 0.5 g, and bed-height ratio around 0.006
(about 0.05 mm for the 9 mm reference depth). These are design targets, not
validated thresholds.

`EXPERIMENTAL_VARIANT_DISCRIMINATION: NOT_ASSESSED`

## Minimum independent measurement package

| Measurement | Definition and synchronization | Informative conditions / role | Principal confounders | Design target | Status |
|---|---|---|---|---|---|
| Basket pressure | gauge pressure at coffee-bed top, synchronized to common shot start | 5, 9, 11 bar and machine-coupled transients; separates supply/basket nodes and improves hydraulic rank | machine pressure response, upstream resistance | <=8 kPa, <=20 ms sampling | essential |
| Outlet liquid flow and cumulative delivered mass | basket-bottom liquid volume or mass flow and its time integral; synchronize with pressure | all conditions; informs `k0`, `pc`, supply curve and water delivery | scale dynamics, evaporation/retention, density conversion | <=0.02 mL/s and <=0.5 g; <=20 ms raw with documented filtering | essential |
| Puck deformation / bed height | independent bed-height change or equivalent compaction at defined axial/spatial basis | especially 5 and 9 bar; separates `phi0`/`pc`/`k0` and model forms | basket compliance, boundary motion, spatial nonuniformity | <=0.05 mm; at least inlet/center/outlet or justified bulk basis | essential |
| Machine-side pressure | separate gauge pressure upstream of declared `Ru`, never substituted for basket pressure | machine-coupled transient; informs `Ru`, `Qfree`, `pshut`, `Cu` | sensor-node placement and line dynamics | <=8 kPa, synchronized <=20 ms | essential for machine coupling |
| Physical first drip / wetting time | independently observed first physical outlet liquid, same time origin | machine transients; adds `Cu`, `Qfree`, `Ru`, `pshut` information | outlet holdup and detection threshold | <=0.02 s | optional but high value |
| Reproduction metadata | temperature, dose, coffee-bed hydraulic area/geometry, bed depth, preparation and shot timing | every condition | uncontrolled preparation variation | direct measurement with uncertainty reported, not invented here | essential |

At least two prescribed pressure levels (5 and 9 bar) plus one machine-coupled
shot are recommended. High pressure alone is not sufficient for the local
compaction triple. Calibration should not begin until synchronized pressure,
flow/mass, deformation, and reproduction metadata are independently measured;
first drip should be added when machine transient discrimination is a goal.

The recommendation links to locked Puckworks planning only: EXP-004 for
hydraulic pressure/flow characterization, EXP-001 for wetting and first drip,
EXP-002 for swelling/geometry observables, and EXP-003 for fines or retained
material context. Those campaigns are not commissioned or available by this
case.

## Evidence and claim boundary

The locked evidence inventory contains no additional admissible independent
dataset compatible with an unchanged current configuration:

`NO_ADDITIONAL_ADMISSIBLE_INDEPENDENT_DATASET_AT_LOCKED_EVIDENCE_STATE`

No VAL-CASE-002 was started. No framework, operating-standard, solver source,
baseline configuration, Puckworks lock, governing equation, constitutive
physics, calibration, or claim ceiling changed.

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
GENERAL_PHYSICAL_VALIDATION: NOT_ESTABLISHED
GENERAL_WHOLE_SOLVER_PHYSICAL_VALIDATION: NOT_ESTABLISHED
STRUCTURAL_IDENTIFIABILITY: NOT_ASSESSED
EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
PROTECTED_OR_HOLDOUT_SCORING: NOT_AUTHORIZED
HOLDOUT_EXECUTION: NOT_AUTHORIZED
NEW_GOVERNING_PHYSICS: NOT_AUTHORIZED
```
