# SCI-MD-011 result

`SCI_MD_011_POROELASTIC_CLOSURE_TEST_BLOCKED_BY_IDENTIFIABILITY_EXECUTION_DOMAIN_OR_EQUIVALENCE_GAP`

Architecture: `NOT_ADJUDICATED`. Scientific status: `BLOCKED`.

Authority: SCI-MD-010 frozen 56-brew, 11-condition observation interface; Puckworks analysis commit 2058d0e947ee9eb92c52d64f6165b810f1fb4732. The source 60-brew full-data calibration is context only.

Models: immutable B0/B1 baselines, universal P1, and fixed-Phi E2C. Candidate fits estimate effective positive Qc/Pc only. The production-equivalent closure uses the SCI-MD-010 quadratic adapter, not the production machine boundary.

Aggregate results:
- HYD_B0_TRAINING_MEAN: 0.31786798610901296
- HYD_B1_PRESSURE_QUADRATIC: 0.1532500174983135
- HYD_P1_POROELASTIC_UNIVERSAL_LIMIT: 0.14455442903341273
- HYD_E2C_EWP_FINITE_PHI_POROELASTIC_COMPONENT: NOT_COMPUTABLE

Pairwise comparisons:
- B1_VS_P1: COMPLETE delta=0.008695588464900761 interval=[-0.04021079718472187, 0.06296560155251746]
- B1_VS_E2C: NOT_COMPUTABLE delta=None interval=None
- P1_VS_E2C: NOT_COMPUTABLE delta=None interval=None

Every fold, failure, diagnostic, parameter, and identifiability receipt is retained in the machine-readable package. P1/E2C are monotone saturating forms and do not contain turnover physics.

Experiment consequence: `IDENTIFY_EXACT_BLOCKER_NO_MEASUREMENT_UNLESS_IRREDUCIBLE_DECISION_CHANGING_OBSERVABLE`.

Current full EWP: NOT_VALIDATED. Physical validation: NOT_ESTABLISHED. Stage F/D: NOT_AUTHORIZED. M01: NOT_ADJUDICATED.
