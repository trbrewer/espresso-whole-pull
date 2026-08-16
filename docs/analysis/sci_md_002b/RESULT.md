# SCI-MD-002B Result

Status: `ADJUDICATIVE_EXECUTION_AND_REDUCTION_COMPLETE_PENDING_OWNER_REVIEW`.

## Question and authority

This reduced, post-observation mechanism-discrimination screen asked whether pressure-dependent wetting time coupled to bounded, pressure-shared particle swelling could produce enough additional high-pressure axial resistance to reproduce `Q5 > Q9 > Q11`.

The exact 435-row cohort (432 S1 records and three C0 controls) was executed from commit `ee3a35e0bd8791415056f4537ead5e050052d020`, tree `57a8b96ef4806707553034092430afdc11eadaf8`, under external owner authority SHA-256 `a38c7c208888fecbbd3de8745010d2c483d38b956fed3d4fab99f33d54847d6b`. The reviewed branch authority was commit `8165ecd5b3c4fa523470f867e6e663a7468aac0b`, tree `c5c30bcc59925fa83c13eef66491086e06b8949b`.

## Package-integrity incident and recovery

The original attempt completed 435 trajectories, but its subsequent integrity check found one malformed record: `S1-SOURCE-P9-M-D1.0-CM0.05-AC0.0-REFINED`. No scientific disposition was emitted from that failed package. The original attempt remains byte-preserved as failed-package incident evidence.

Recovery used `PACKAGE_INTEGRITY_RECOVERED_BY_SAME_AUTHORITY_SINGLE_RECORD_EXACT_RESUME`. All 434 valid records were retained byte-for-byte; the one copied malformed record was replaced in a physically separate recovery clone by the frozen executor's exact-resume path using the same source and authority. The replacement's canonical scientific result was byte-identical to two clean-process simulations. The complete recovery bundle passed the unchanged frozen verifier before reduction. Full details are in `INTEGRITY_INCIDENT_AND_RECOVERY.md`.

## Frozen reduction

The exact machine disposition is:

`SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING`

All 72 candidate stems passed numerical and physical-state validity and passed the required resistance direction. All 72 then failed the pressure-ordering gate robustly; none was numerically unresolved. Consequently, no candidate reached the temporal-signature, assumption-dependence, grind-identifiability, or aggregate-comparison gates. RMSE and MAE were not calculated because aggregate comparison is permitted only after every earlier gate passes.

| Gate state | Candidate count |
|---|---:|
| Complete candidates | 72 |
| Numerical/physical valid | 72 |
| Resistance-direction pass | 72 |
| Pressure-ordering pass | 0 |
| Pressure-ordering numerically unresolved | 0 |
| Robust wrong-ordering rejection | 72 |
| Temporal-signature evaluated | 0 |
| Aggregate-comparison eligible | 0 |

The closest signed margins occurred for powder E, diffusivity multiplier 2.0, `C_M = 0.1`, and fixed height (`accommodation = 0.0`):

- `M59 = -3.314698510955386e-05 kg/s`, with `U59 = 3.159415638040629e-07 kg/s`.
- `M911 = -1.3221263408696969e-05 kg/s`, with `U911 = 1.2601847261215773e-07 kg/s`.

Both margins remain negative after the prospectively frozen uncertainty allowance. No assumption set survived pressure ordering, so accommodation or particle-size capability dependence cannot be inferred. The recorded `phi_wet` and `epsilon_b0` sensitivity bounds were not matrix axes; robustness across those bounds is not established.

## Interpretation and limits

The result rejects only the frozen one-way wetting-age swelling family over the executed bounds. It does not establish that swelling is absent in real espresso, does not select another mechanism, and does not validate the physical model or whole solver. Direct swelling, deformation, bed-height, first-drip, wetting-front, and particle-size-to-source mapping evidence remains necessary for mechanism discrimination.

Standing limits:

- `PHYSICAL_VALIDATION_NOT_ESTABLISHED`
- `POST_OBSERVATION_MECHANISM_DISCRIMINATION`
- `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`
- `NO_COMBINED_MECHANISM_AUTHORIZATION`
- `NO_SCI_LC_001B_AUTHORIZATION`
- `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`
- `PHI_WET_AND_EPSILON_B0_BOUND_ROBUSTNESS_NOT_ESTABLISHED`
- `SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED`

The integrity recovery does not promote the mechanism and does not authorize production physics, OpenFOAM work, two-way swelling feedback, grind transfer, or combined-mechanism modeling.
