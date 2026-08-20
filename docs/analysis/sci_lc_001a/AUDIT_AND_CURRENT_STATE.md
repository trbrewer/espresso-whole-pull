# SCI-LC-001A audit and current state

The scientific anchor remains protocol commit `93959caf85ff26b5e3520fbcb181654ce27db3a0`: 1,280 rows, 3,666 keys (1,454 static and 2,212 dynamic), semantic matrix SHA-256 `4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717`. SCI-ED is accepted on `main` at merge `9ac7bf88340b5c12a0003729ac4e998b7bf67626`.

Historical E2, E3, RCA-002, and E4 Attempts 01–03 are noncanonical, scientifically ineligible, quarantined, and prohibited from reuse or combination. RCA-001 is a completed diagnostic only.

RCA-002 planned 3,666 keys. Immutable counters and an independent filesystem inventory establish 2,555 attempted and complete keys, zero failed or protocol-stopped keys, and 1,111 unattempted keys. Required event-state fields, full dynamic coverage, stop events, and observer health finalization were absent. Its terminal state is therefore `STOPPED`, disposition `STOP_EVENT_STATE_CAPTURE_INCOMPLETE`, event-state capture is incomplete, and classifications equal zero. The exact dispatched count is unresolved because no durable pre-execution per-key dispatch ledger survives; this uncertainty cannot make the corpus eligible.

Attempt 04 was reserved once and executed fresh at exact head `34af7e56f4887abd0a11e1dff0e825c935dc62e2`. All 3,666 planned keys were dispatched and terminalized: 3,558 `COMPLETE`, 108 `STOPPED`, zero failed, and zero unattempted. Required diagnostic finalization is unhealthy: 1,044 applicable records were written, while 108 other applicable stopped cases have no accepted multiplier terminal record. The attempt is therefore terminal, quarantined, scientifically and canonically ineligible, and produced zero classifications. No retry is permitted. Attempt 05 authority is `NONE`.

PR #85 rebuilt the minimal audit layer and imported only the substantive execution-family controls previously exercised on PR #84; it was merged normally into the protocol branch. PR #82 and PR #84 are closed without merge as superseded. One fresh canonical execution occurred; canonical classification count remains zero because Attempt 04 is ineligible.

This work is `NO_GOVERNING_PHYSICS_CHANGE`. Physical validation remains `NOT_ESTABLISHED`; no real-puck regime boundary or material parameter is established.
