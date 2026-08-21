# SCI-MD-003 / RP-A-001 C1 consumer protocol

Protocol: `SCI-MD-003-RP-A-001-C1-EWP/v1`  
Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`

The consumer accepts only the exact qualified Puckworks v2 export identified in
`PUCKWORKS_ANALYSIS_PIN.json`. It validates schema, SHA-256, execution commit and
tree, protocol, case matrix, measurement assumptions, support invariants,
summary counts, and decision references.

Cross-repository pair eligibility is reconstructed from retained EWP observable
fields and the upstream evidence-domain records. Only level-1/2 scientifically
competing or nested pairs enter measurement coverage. Measurement intervals use
conservative additive bounded half-widths; absent uncertainty is never zero.
Coverage uses only robust records. An empty eligible-pair universe returns
`NO_ELIGIBLE_PAIRWISE_DISCRIMINATION_PROBLEM` and
`NO_COMPLETE_MEASUREMENT_SET`, never a successful empty set.

The final EWP programme decision is derived independently and is distinct from
the imported `PUCKWORKS_COMPONENT_ATLAS_DECISION`. SCI-LC outputs are excluded.
No OpenFOAM execution, solver change, case change, production dependency change,
physical-validation promotion, experiment, or protected scoring is authorized.
