# SCI-MD-002C Result

Status: `ADJUDICATIVE_EXECUTION_AND_REDUCTION_COMPLETE_PENDING_OWNER_REVIEW`.

## Question and authority

This reduced, post-observation mechanism-discrimination screen asked whether one pressure-shared, finite-inventory, mass-conserving axial fines-release, transport, and downstream-deposition mechanism could create sufficient additional resistance at 9 and 11 bar to reproduce `Q5 > Q9 > Q11`.

The exact 579-row cohort (576 S1 records and three C0 controls) was executed from commit `cb9ebd2d4ba220d4777f033e06eddbae787b519a`, tree `393ede84c88ae330faf103ce3845936dc0f9fc73`, under external owner authority SHA-256 `34f644ffd23ef36076015aba2789e1a8b598a52d021f25563473814caffa2c4b`. The reviewed branch authority was commit `be4079f28070e6b601fe6a9fb6461b5f421ca4b1`, tree `05e09705fdab079c1692b18c298172f3c01993e7`.

The source window is a saturated-model approximation with `SYNTHETIC_WINDOW_START_RESET`: full unreleased inventory is uniformly distributed axially, while mobile, deposited, and escaped fines and cake resistance start at zero. `PRE_WINDOW_FINES_STATE_NOT_ADJUDICATED`; these states were not observed at the source-window start.

## Package integrity

All 579 immutable records passed exact authority, UUID, source, schema, parameter, internal-hash, and full-file-hash checks. After execution closeout, write permission was removed from `case_records/`, every record, and `manifest.json`. Three frozen bundle verifications produced the same manifest SHA-256 `fd1267cf515db4388177eb2cb713ebee97f9a3cece9403caf373149965940dcb` and ordered-record aggregate `d5a5bb2225da8f53e934a04ea3aa14d7b37f06ab07ae936ed21b0efc7a21be34`. Two frozen reductions were byte-identical with SHA-256 `565fac7ae38e90fe715791ebc40680630495297ded1a570270e147aa36cd2036`.

## Frozen reduction

The exact machine disposition is:

`SCI_MD_002C_REJECTED_WRONG_PRESSURE_ORDERING`

All 96 candidate stems were numerically and physically valid. The prospective feasibility bounds classified 92 as insufficient-inventory negative controls. The remaining four analytically potentially feasible stems passed resistance direction but robustly failed pressure ordering. None passed ordering, so temporal signature and aggregate comparison were not evaluated under the frozen gate precedence. No RMSE or MAE is eligible.

| Gate state | Candidate count |
|---|---:|
| Complete candidates | 96 |
| Numerical/physical valid | 96 |
| Inventory feasible | 4 |
| Inventory-impossible negative controls | 92 |
| Resistance-direction pass | 4 |
| Pressure-ordering pass | 0 |
| Pressure-ordering numerically unresolved | 0 |
| Robust wrong-ordering rejection | 4 |
| Temporal-signature evaluated | 0 |
| Aggregate-comparison eligible | 0 |

All four feasible stems used fines fraction `0.1`, mobilizable fraction `0.75`, retention `1.0`, specific cake resistance `1.0e13 m/kg`, compact-layer porosity `0.5`, and particle velocity ratio `1.0`. Their release-closure outcomes were:

| Release rate (1/s) | Exponent | M59 (kg/s) | U59 (kg/s) | M911 (kg/s) | U911 (kg/s) | Outcome |
|---:|---:|---:|---:|---:|---:|---|
| 0.02 | 1.0 | -3.5467028009640664e-4 | 1.6870642170351176e-7 | -1.344316426628323e-4 | 4.792029044257441e-8 | Wrong ordering |
| 0.02 | 2.0 | -3.1866778950102447e-4 | 2.1794751403636254e-7 | -1.117473940496997e-4 | 5.1937937111268956e-8 | Wrong ordering |
| 0.1 | 1.0 | -3.1669991655515473e-4 | 4.4350689898170134e-7 | -1.3406677251259237e-4 | 7.348534301974529e-8 | Wrong ordering |
| 0.1 | 2.0 | -2.7260010319550294e-4 | 3.066128123695817e-7 | -1.198739817596001e-4 | 1.7436610906225794e-8 | Wrong ordering |

The closest `M59` was `-2.7260010319550294e-4 kg/s` with `U59 = 3.066128123695817e-7 kg/s`. The closest `M911` was `-1.117473940496997e-4 kg/s` with `U911 = 5.1937937111268956e-8 kg/s`. Both remain robustly negative under the prospectively frozen uncertainty rule.

## Interpretation and limits

The result rejects only the frozen one-dimensional axial, fixed-active-bed, synthetic-window-reset fines family over the executed bounds. It does not establish that fines are absent from real espresso and does not identify another mechanism.

No assumption set survived ordering, so capability dependence cannot be inferred. Retention was bounded prospectively, but compact-layer porosity remained fixed at `0.5` and `particle_velocity_ratio = 1.0` remained a synthetic fastest-transport upper bound. Robustness to layer porosity, particle retardation, or pre-window fines state is not established. The active bed did not open as fines left, and no lateral or channeling physics was tested.

Direct turbidity, mobilizable-inventory, retained/deposited-mass, particle-size, compact-layer structure/conductivity, and interruption/recovery measurements remain necessary for mechanism identification.

Standing limits:

- `PHYSICAL_VALIDATION_NOT_ESTABLISHED`
- `POST_OBSERVATION_MECHANISM_DISCRIMINATION`
- `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`
- `NO_COMBINED_MECHANISM_AUTHORIZATION`
- `NO_SCI_LC_AUTHORIZATION`
- `NO_OPENFOAM_AUTHORIZATION`
- `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`
- `FINES_CLOSURE_PARAMETERS_NOT_ESTABLISHED_AS_REAL_PUCK_MEASUREMENTS`
- `SYNTHETIC_WINDOW_START_RESET`
- `PRE_WINDOW_FINES_STATE_NOT_ADJUDICATED`

This result does not select or validate fines physics and does not authorize production, OpenFOAM, SCI-LC, grind-transfer, or combined-mechanism work.
