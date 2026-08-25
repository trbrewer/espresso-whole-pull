# SCI-MD-004 Stage E1 protected holdout result

Authorization:
`SCI-MD-004-STAGE-E1-OWNER-AUTHORIZATION-SINGLE-PROTECTED-HOLDOUT-PREDICTION-NUMERICAL-FREEZE-ONE-SCORER-INVOCATION-AND-FINAL-SCIENTIFIC-DISPOSITION-2026-08-24`.

Governance class: **G3 — protected holdout prediction and scoring**.
Change declaration: **NO_GOVERNING_PHYSICS_CHANGE**.

## Result

`SCI_MD_004_STAGE_E1_EXECUTION_CONTRACT_BLOCKED_BEFORE_TARGET_ACCESS`

The target-blind materialization gate inspected the unchanged production
solver and its accepted case materializer against all 264 frozen configuration
intents. Every frozen case contains
`conditional_outlet_mass_flow_kg_s`, derived from nominal yield divided by
reported duration. The production interface supports only
`prescribedPressure` and `lumpedMachineCompliance`; it has no accepted
prescribed outlet-flow boundary.

Using `prescribedPressure` with the inherited template permeability would
predict a flow rather than impose the frozen conditional flow. Fitting
permeability, adding a flow boundary, or introducing a lumped machine model
would each violate the Stage E1 authorization. The hydraulic contract therefore
cannot be represented without an unauthorized choice.

No complete executable scenario was emitted. Production solver executions,
Angeloni predictions, prediction rows, protected scorer processes, and
post-holdout retuning events are all zero. A silent SHA-256 integrity read
required during preflight exposed no target values and was isolated from all
scientific decisions; semantic protected-target access is zero.

The accepted source, Stage E0 freeze, governance, solver-source, and executable
identities were verified. The production solver source remains SHA-256
`9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599`.
The accepted executable remains
`d793a731fd2f4f82e623350c61835d0e955d886849f5e363a5abd8dd0fae4c93`.

## Claim ceiling

The generic indexed species solver remains software and numerically verified.
The caffeine and trigonelline parameters remain training-data estimates, not
universal physical constants. No Angeloni predictive comparison occurred.
This result validates neither internal transient fields, thermal chemistry,
lipid transport, taste, nor unrestricted transfer. General physical validation
remains **NOT_ESTABLISHED**.

The next model-development decision requires new owner authority to reconcile
the conditional hydraulic input with an already accepted production-solver
boundary representation. This authorization does not permit that revision.
