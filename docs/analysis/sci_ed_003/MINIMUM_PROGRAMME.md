# SCI-ED-003 minimum programme

The Pareto-minimal candidate is **M01 paired absolute chemistry and mass closure plus only the shot-context portion of M02**. It is a two-stage contract; neither stage is authorized. M03 porosity/permeability, M04 dynamic resistance, and M05 independent transfer remain separate conditional tasks.

## What it would measure

Stage F would preserve linked measurements of total assayable caffeine/trigonelline (`T_total`), every initial and spent reference-extraction cycle (`I_ref_initial`, `I_ref_spent`), absolute mass in consecutive mass-defined cup fractions, whole-cup/fraction reconciliation, retained-liquid and other declared recovery terms, moisture/dry basis, blanks/calibration/recovery/LOD/LOQ/native chromatograms, achieved pressure, beverage-mass history, fraction timing, temperature, and complete preparation/geometry/machine metadata.

The declared operational closure is

`closure_residual[a] = I_ref_initial[a] - M_cup[a] - M_retained[a] - I_ref_spent[a] - M_other_declared[a]`.

Every term must be observed or the result remains incomplete; no unmeasured term is zero by assumption. `T_total`, `I_ref`, `Q_production_solid_initial`, and `c_s0` remain distinct. `I_ref = production M0` and the `c_s0` mapping remain `NOT_ESTABLISHED`.

## Endpoint, replication, and uncertainty

Stage F is nonadjudicative. It learns method feasibility, analyte-specific tail behavior, recovery, pairing, closure, variance/covariance, clock performance, and capability limits. It does not adopt SCI-ED-002’s unsupported 1%, two-consecutive-fraction, or eight-cycle proposal. Every cycle remains raw-retained; caffeine and trigonelline can stop differently. A tail above quantification or decision materiality at the maximum feasible cycle yields no qualified endpoint.

The independent shot unit is an independently ground dose, prepared puck, and shot. Fractions, extraction cycles, analytical preparations, and injections are nested or technical replicates—not independent shots. Numeric counts are `PILOT_REQUIRED`; historical count envelopes and withdrawn SCI-MD-009 values are not adopted.

Stage D, if separately authorized, freezes its endpoint, materiality, acceptance/rejection/no-decision regions, and independent-unit sample size only after Stage F. Its count is calculated from Stage F variance components, the named EWP effect/materiality, coverage and precision/power/assurance, block structure, multiplicity, qualification loss, resource maximum, and an error-controlled sequential/no-decision rule.

## Decision consequences

- Qualified reproducible closure permits consideration of a separate G1 inventory-bridge test; it adopts no bridge.
- Closure failure or excessive variability leaves production inventory and `c_s0` independent/unidentified and creates no predictor.
- Decision-relevant absolute species differences permit a separately scoped chemistry comparison; a negative or null result retains the simpler representation or reports non-identification.
- Qualified `p_in(t)` applies only to the exact future shots; it is not a machine-population boundary.
- M03 is elevated only if its uncertainty can change a named EWP output decision.
- M04 is elevated only with new distinguishing synchronized conditions; negative/null evidence retains fixed resistance by parsimony, while positive evidence authorizes only a G2 proposal.
- M05 follows only after local qualification and a separate prospective transfer freeze.

No equipment selection, procurement, laboratory contact, experiment, data collection, model execution, physics change, or parameter adoption is authorized. Physical validation remains `NOT_ESTABLISHED`.
