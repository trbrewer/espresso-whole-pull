# SCI-MD-002C decision and parallel-lane charter

## Decision

On 2026-08-16 the owner selected SCI-MD-002C as the next secondary scientific lane from live `origin/main` `db5b0a5492b36d568241f97b482fe90fac8d44da` (tree `3260123d4395dd5d3ec6b088fdb63087a917e9dd`). SCI-MD-002A boundedly rejected reversible consolidation and SCI-MD-002B boundedly rejected one-way wetting-age swelling, with the latter evidence qualified by `PACKAGE_INTEGRITY_RECOVERED_BY_SAME_AUTHORITY_SINGLE_RECORD_EXACT_RESUME`. Fines transport and outlet deposition are distinct because resistance arises from conserved particulate inventory transferred axially into a compact downstream layer.

The retained target is `Q5 > Q9 > Q11`. This is `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `PHYSICAL_VALIDATION_NOT_ESTABLISHED`. Channeling and localization remain exclusively with SCI-LC-001A. Lateral sectors, OpenFOAM, thermal and extraction chemistry, compaction, swelling, active-bed opening, and combined mechanisms are excluded.

## Lane identity

- Task: `SCI-MD-002C`; lane: `EWP-PAR-SCI-MD-002C`; role: secondary scientific lane.
- Owner: sole SCI-MD-002C writer and execution owner.
- Branch: `research/sci-md-002c-axial-fines-deposition` from the authority above.
- Worktree policy: a dedicated path containing `sci-md-002c`; never the primary or SCI-LC worktree.
- GitHub issue and draft PR are recorded in the machine declaration when created.
- External namespace: `SCI_MD_002C_EXTERNAL_BUNDLE`; concrete absolute paths are local metadata and are not committed.
- Puckworks is read-only at commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree `1d553e44ee2f7480a5df521560801b478618cc84`.
- Primary parallel lane: SCI-LC-001A, observed read-only at draft PR #71 and Issue #70; live identities are recorded in preflight evidence.

## One writer and path ownership

Only this lane owner may modify its branch, issue, PR, artifacts, external bundle, authorities, or processes. Shared references may be consumed but never rebound silently; copied output may not be described as independently generated.

Owned patterns are exactly `docs/analysis/sci_md_002c/**`, `validation/cases/sci_md_002c/**`, `scripts/sci_md_002c.py`, `tests/test_sci_md_002c.py`, the external namespace, issue, and draft PR. Forbidden patterns are `docs/analysis/sci_lc_001a/**`, `validation/cases/sci_lc_001a/**`, `scripts/sci_lc_001a*`, `tests/test_sci_lc_001a*`, `solver/**`, `config/**`, production `cases/**`, Puckworks files, global strategy files, and Issue #76.

SCI-LC and Puckworks are read-only. No SCI-LC concepts, multi-streamtube model, output, calibration, evidence, or code may enter this lane.

## Resource and process rules

SCI-LC has priority. Pilot and future execution use one worker, one nested numerical-library thread, no GPU, no OpenFOAM, and at most 16 GiB RSS. Every owned process is recorded in the task ledger. No process belonging to another lane may be signaled, stopped, resumed, or reniced.

## Shared-file and integration policy

Shared strategy, project-state prose, and Issue #76 remain untouched while lanes coexist. Canonically required generated metadata is minimal, isolated, and expected to be reconciled after serial integration. Each lane is reviewed independently; the owner chooses merge order. A later lane incorporates accepted `main`. Frozen scientific ancestry is never rebased or rewritten. The agent neither marks its PR ready nor merges it. Results remain bound to the exact execution source.

## Duplicate-assignment containment

Any overlapping SCI-MD-002C branch, issue, PR, worktree, process, artifact directory, or materially equivalent writer triggers an inventory-only stop with `DUPLICATE_ASSIGNMENT_CONTAINMENT_REQUIRED`. Nothing is created, modified, deleted, or signaled.

## Evidence durability

Every bundle has an authority-bound UUID. Canonical record bytes are written to a temporary file, flushed, file-synchronized, atomically renamed, directory-synchronized where supported, immediately read back, parsed, and checked by internal and full-file hashes before completion is recorded. Manifests receive the same atomic treatment and bind the UUID and ordered-record aggregate. Corruption, malformed JSON, same-size mutation, incomplete temporary-file, resume-integrity, and UUID mismatch tests are mandatory.

## Claim ceiling and closeout

Standing boundaries are `PHYSICAL_VALIDATION_NOT_ESTABLISHED`, `POST_OBSERVATION_MECHANISM_DISCRIMINATION`, `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`, `NO_COMBINED_MECHANISM_AUTHORIZATION`, `NO_SCI_LC_AUTHORIZATION`, `NO_OPENFOAM_AUTHORIZATION`, `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`, and `FINES_CLOSURE_PARAMETERS_NOT_ESTABLISHED_AS_REAL_PUCK_MEASUREMENTS`. The lane may report only a prospective reduced screen, analytical feasibility, numerical verification, a non-adjudicative pilot, closure dependence, and missing measurements. It may not use `FINES_SELECTED`, claim causation or validation, map synthetic fines to source grinds, or promote production physics.

Closeout reports exact Git, dependency, issue/PR, artifact/hash, matrix/cohort, pilot/bundle, verification, process, and isolation identities. The required boundary is `SCI_MD_002C_PREEXECUTION_PACKAGE_COMPLETE_PENDING_INDEPENDENT_REVIEW`; adjudicative execution remains unauthorized.

