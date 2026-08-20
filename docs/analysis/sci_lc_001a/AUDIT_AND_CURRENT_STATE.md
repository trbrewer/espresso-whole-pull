# SCI-LC-001A audit and current state

The scientific anchor remains protocol commit `93959caf85ff26b5e3520fbcb181654ce27db3a0`: 1,280 rows, 3,666 keys (1,454 static and 2,212 dynamic), semantic matrix SHA-256 `4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717`. SCI-ED is accepted on `main` at merge `9ac7bf88340b5c12a0003729ac4e998b7bf67626`.

Historical E2, E3, RCA-002, and E4 Attempts 01–03 are noncanonical, scientifically ineligible, quarantined, and prohibited from reuse or combination. RCA-001 is a completed diagnostic only.

RCA-002 planned 3,666 keys. Immutable counters and an independent filesystem inventory establish 2,555 attempted and complete keys, zero failed or protocol-stopped keys, and 1,111 unattempted keys. Required event-state fields, full dynamic coverage, stop events, and observer health finalization were absent. Its terminal state is therefore `STOPPED`, disposition `STOP_EVENT_STATE_CAPTURE_INCOMPLETE`, event-state capture is incomplete, and classifications equal zero. The exact dispatched count is unresolved because no durable pre-execution per-key dispatch ledger survives; this uncertainty cannot make the corpus eligible.

Attempt 04 is the only remaining execution ordinal. Before readiness it is unstarted, unconsumed, unreserved, and has dispatched zero canonical keys. The family hold remains active. Attempt 05 authority is `NONE`.

The active branch rebuilds the minimal audit layer and imports only the substantive execution-family controls previously exercised on PR #84. PR #82 and PR #84 remain historical candidates until the replacement PR is pushed, then close without merge as superseded. Canonical execution and classification counts remain zero until a valid Attempt 04 terminal result exists.

This work is `NO_GOVERNING_PHYSICS_CHANGE`. Physical validation remains `NOT_ESTABLISHED`; no real-puck regime boundary or material parameter is established.

