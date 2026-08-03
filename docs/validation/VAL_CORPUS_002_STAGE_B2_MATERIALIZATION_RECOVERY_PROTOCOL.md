# VAL-CORPUS-002 Stage B2 materialization recovery protocol

Authorization `VAL-CORPUS-002-B2-PRODUCTION-SCORING-2026-08-03` permits one
bounded recovery within `EWP_PRODUCTION_AND_SCORING_STAGE_V1`. The original B2
runtime root and partial result are immutable.

The frozen defect is
`STRUCTURED_WASZKIEWICZ_P2_PLACEHOLDER_WAS_RECURSIVELY_NESTED_RATHER_THAN_COLLAPSED_TO_THE_REQUIRED_SCALAR`.
The Schmieder source form is the exact token at
`chemistry.extractionRateConstant_s_inverse`. The Waszkiewicz source form is
the complete `status`/`token`/`type` object at
`extraction.rate_constant_1_s`. Both normalize to one internal placeholder:
`{"type":"P2_EXTRACTION_RATE_S_INVERSE","value":"UNMATERIALIZED"}`.

Normalization precedes recursive traversal. Materialization replaces exactly
one approved semantic path with the governed finite scalar
`0.3439597024835067 s^-1` (`0x1.6036f8e53bf4ep-2`). A remaining token,
placeholder, unresolved status, wrapper object, nonfinite value, wrong
floating identity, zero/multiple approved paths, or change outside that path
fails closed. `token` is not a reverse-materialization rate key.

The source run matrix, protocol, 30 numeric configurations, and 14 Schmieder
P2 materializations remain unchanged. Only the Waszkiewicz P2 template and
materialized configuration may be superseded; the 45-member aggregate is
regenerated. The historical invalid configuration
`7e7a8977cc45641c6e22b90922a5b370e9e0e81179ad0e1022c371c863c79dbc`
and aggregate
`21e16604072de4b4b5e86561f41b0fd5a28c1c4c486b1e4964b6ef8844279c47`
remain retained.

The original root, both failed preparations, 26 passing identities, and 18
typed target-coverage failures are immutable. A closed 44-identity cache must
verify every configuration, trace, completion, numerical disposition, and
reuse identity before recovery execution. None may be rerun. The corrected
Waszkiewicz P2 case runs in a new root, followed by the eight frozen
nonbaseline sensitivities after exact baseline reuse. No refit, protected
scoring, source reselection, solver change, new physics, VAL-CASE-002 action,
or merge is authorized.
