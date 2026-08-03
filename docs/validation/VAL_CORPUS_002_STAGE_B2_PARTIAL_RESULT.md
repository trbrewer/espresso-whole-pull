# VAL-CORPUS-002 Stage B2 partial result

Disposition:
`VAL_CORPUS_002_STAGE_B2_RESULT_INCOMPLETE_REPEATED_P2_WASZKIEWICZ_MATERIALIZATION_INFRASTRUCTURE_FAILURE`.

The exact fixed B1 rate remained `0.3439597024835067 s^-1`. Forty-four of 45
production identities reached a terminal numerical disposition: 26 passed
(including the exact B1 anchor reuse), and 18 Schmieder H0 identities were
typed failures because 60 g was not bracketed by 90 s. The Waszkiewicz P0 and
P1 executions passed normal completion; predecessor parity passed all 1,500
states over `[0.02, 29.9999999999994] s`.

The final Waszkiewicz P2 identity failed in `prepare_case` before OpenFOAM on
both the original attempt and the one permitted identical retry. The
manifest-bound materialization retained a typed placeholder object whose
`token` was replaced by the selected scalar, rather than producing the scalar
field required by `prepare_case`. Both attempts are immutable and have no
scientific score. The frozen recovery policy prohibits a third attempt, so
the nine sensitivity identities were not executed and governed production
metrics were not calculated.

No refit, protected scoring, transfer-driven tuning, solver change, new
governing physics, VAL-CASE-002 work, or merge occurred. Physical validation
remains not established.
