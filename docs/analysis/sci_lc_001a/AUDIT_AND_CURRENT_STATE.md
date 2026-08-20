# SCI-LC-001A audit and current state

Date: 2026-08-19. Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`.

This is the authoritative human-readable status entry point for the clean-path
reconciliation. Issue #70 originally froze the reduced lateral-equalization
protocol. Later work expanded de facto into implementation qualification,
observability, execution, containment, postmortem, lifecycle correction, and a
separately owner-gated final execution. Those later scopes do not rewrite the
original issue scope.

## Current authority and protocol identity

The audited SCI-LC branch anchor is
`93959caf85ff26b5e3520fbcb181654ce27db3a0`, tree
`90500f62016ccb4453fb4b7d4af2aca0834b5f9c`, with parents
`18641c01ebd4d18636c092f616855eb2659c4a09` and
`d242ef63174be28f4487e9cefa924cafb897abfc`. PR #71 is open, draft, unmerged,
and currently conflicts with `main`; Issue #70 is open.

The controlling matrix has 1,280 rows and semantic SHA-256
`4bb979181a0e5c672b896c44e3eee9574e28f0abed1d1f5dc227a47214e21717`.
The frozen graph has 3,666 keys: 1,454 static and 2,212 dynamic.

## Predecessor and completed prerequisite work

Puckworks RP-D-LC-001b is closed at scientific head/tree
`47d39239d745919c46e3718392aa4c39322dbe9f` /
`f16a2c1531af2a8cdb62b4a718abf56e7c5415b8` with disposition
`NO_UNAMBIGUOUS_BELOW_CANDIDATE`. P2a and P2b completed; P3/P4 did not run;
WP6 inverse recovery was not tested. It is neither a negative recovery result
nor an authorized continuation path.

ICA-003 R3 closed the baseline-only classification-scope tranche. OBS-001 was
corrected, independently reviewed, owner-adjudicated, and incorporated in the
two-parent SCI-LC anchor. Any earlier pending wording is historical and stale.

## Historical execution and eligibility

`HISTORICAL_NONCANONICAL_EXECUTION_ATTEMPTS_OCCURRED`.

- E2 stopped on backend-authority mismatch. Its partial evidence is historical
  and ineligible.
- E3 stopped with an incomplete graph. Its partial evidence is historical and
  ineligible.
- RCA-001 and RCA-002 were diagnostics only and may not supply scientific
  results or classification inputs.
- E4 Attempt 01 dispatched 2,768 keys and failed/was contained.
- E4 Attempt 02 dispatched 29 keys and was archived after supervision loss.
- E4 Attempt 03 dispatched 3,151 keys and was stopped under the family
  suspension. Its stale `RUNNING` manifest is not process-liveness evidence.
- E4 Attempts 01--03 are read-only, quarantined, scientifically ineligible,
  non-reusable, non-resumable, non-replayable, and non-importable.

`CANONICAL_SCIENTIFIC_EXECUTION_COUNT: 0`

`CANONICAL_CLASSIFICATION_COUNT: 0`

No E3 or E4 Attempt 01--03 output may be combined into a landscape or used to
support H0--H6.

## Containment, PM-001, and Attempt 04

The family disposition is
`E4_EXECUTION_FAMILY_SUSPENDED_CONTAINED_AND_ADMINISTRATIVELY_CLOSED_PENDING_SEPARATE_INFRASTRUCTURE_CORRECTION`.
PM-001 found stale textual leases, external stop paths that bypassed
executor-owned terminalization, missing atomic attempt reservation, incomplete
hold enforcement, and no implemented correction. The additive finding-count
erratum controls over the earlier summary.

The complete conditional Attempt 04 owner receipt is retained in local Codex
history session `01a01b1d-0fa8-7080-bd57-1862a00fddc9`, timestamp
2026-08-19T18:05:16Z, 37,444 characters, raw-text SHA-256
`23981f243352d2afb5c4997bfe604134733a856087b16808c46957d1726673f8`.
It binds the old exact head and makes readiness a condition of launch. It is a
slot reservation, not corrected-head activation authority. Attempt 04 is
`RESERVED_NOT_STARTED_CONDITIONAL_NOT_LAUNCH_AUTHORIZED`; canonical dispatch is
zero and the attempt is unconsumed. Attempt 05 authority is `NONE`.

## Current administrative, execution, and merge authority

The family hold is active. Scientific launch, retry, replacement, resume,
recovery dispatch, classification, and publication are prohibited. A separate
infrastructure correction, independent exact-head review, readiness pass, and
fresh owner re-anchor to the unchanged corrected head are required before
Attempt 04. PR #71 and `main` merge authority are `NONE`.

SCI-ED-001 completed first serialization and merged through PR #80 as
`9ac7bf88340b5c12a0003729ac4e998b7bf67626`, with parents `e8a66378...` and
the independently approved head `481e9bebe1d01de32b6db5412248c37153e926ed`.
The merge tree equals approved tree `7dd5085a...`. It used the pre-existing
PR-only administrator bypass with zero ruleset mutations; the pre/post policy
SHA-256 is `e901438b...3af2`. Issue #79 is closed. This branch now owns the
serialized shared metadata; PR #84 must regenerate it after incorporating the
frozen PR #82 candidate.

## Known inconsistencies and remaining gates

The prior README and project state still say ICA-003 R3 is pending and use an
unqualified `NO_SCIENTIFIC_EXECUTION` statement. Those surfaces are superseded
by this audit and must be corrected without changing frozen scientific content.
The remaining gates are: task-local reconciliation review, infrastructure implementation review and
owner decision, corrected-head readiness, Attempt 04 owner re-anchor, one fresh
attempt, and independent evidence adjudication.

Physical validation remains `NOT_ESTABLISHED`. This remains a synthetic
reduced-model diagnostic: no real-puck parameter, universal boundary,
production-solver improvement, experiment, or unique mechanism is established.

Machine-readable pointers: `EXECUTION_ATTEMPT_LEDGER.json`,
`EVIDENCE_ARCHIVE_MANIFEST.json`, and `SCI_LC_001A_CURRENT_STATUS.json`.
