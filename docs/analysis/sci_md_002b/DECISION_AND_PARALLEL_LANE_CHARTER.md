# SCI-MD-002B decision and parallel-lane charter

Status: `ADJUDICATION_LAYER_CORRECTION_COMPLETE_PENDING_FINAL_REVIEW`

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`; task declaration: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`.

## Decision and scientific context

On 2026-08-16 the owner selected SCI-MD-002B as the independent secondary lane from live EWP authority `c872f782351a22277b7d7a8430bcbf140cff130e`, tree `a0cc697d7a787865baa76f2a8d00ffbb36e48408`. The question is whether higher prescribed pressure advances the Foster wetting front soon enough to give cells more Mo-style swelling age at the common governed reporting point, thereby raising serial resistance enough for `Q5 > Q9 > Q11` with one pressure-shared parameter set.

SCI-MD-002A boundedly rejected its frozen single-state reversible transient-poromechanics family for wrong pressure ordering. Wetting-age swelling is selected because its delay is tied to a separately defined local event rather than to an arbitrary resistance clock. Fines migration is deferred because it needs distinct transport/deposition evidence and more states. SCI-LC localization, circumferential sectors, lateral exchange, and OpenFOAM are excluded because they answer another lane's spatial question and would destroy mechanism isolation. SCI-MD-002B is complementary to, but consumes no result or candidate from, SCI-LC-001A-C3. This is post-observation mechanism discrimination; `PHYSICAL_VALIDATION_NOT_ESTABLISHED`.

Alternatives considered were fines deposition/erosion, transient poromechanics, machine-only control, viscosity change, and evolving lateral localization. Transient poromechanics has already received its bounded SCI-MD-002A screen; the others are outside this task's single chain.

## Lane identity

- Task: `SCI-MD-002B`; lane: `EWP-PAR-SCI-MD-002B`; role: independent secondary reduced-model lane.
- Owner role: `SOLE_SCI_MD_002B_WRITER_AND_EXECUTION_OWNER`.
- Branch: `research/sci-md-002b-wetting-age-swelling`; dedicated worktree required and never shared.
- Issue: #74; draft PR: #75 (must remain draft).
- External namespace: `SCI_MD_002B_EXTERNAL_BUNDLE`; machine absolute paths are non-authoritative and uncommitted.
- Start: EWP HEAD/tree above. Puckworks lock: commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree `1d553e44ee2f7480a5df521560801b478618cc84`.
- Primary lane observed read-only at correction start: SCI-LC-001A-C3, branch `research/sci-lc-001a-protocol`, head `4f06c5e179d9e6f045e1b58cef06ffa98ec0fbea`, issue #70, draft PR #71.

## Pre-execution review correction

The first independent review approved the concept and isolation but required full governed pressure histories, separation of wetting and bed porosity, calculated swelling-storage bookkeeping, executable temporal outputs and matched uncertainty, and complete authority-gated execution/reduction. This correction preserves all earlier commits and pilot attempts. Attempts 1 and 2 remain superseded diagnostic-only; attempt 3 exposed a synthetic-control pressure-dispatch defect; attempt 4 exposed incomplete ledger closeout; both are preserved diagnostic-only. Fresh attempt 5 passed its non-adjudicative integrity and process-ledger checks. It changes no production or SCI-LC path and authorizes no adjudicative execution.

## Ownership and paths

Only this lane's owner may modify its branch, worktree, issue, PR, protocol, matrix, external bundle, authorities, processes, or completion comments. Puckworks and SCI-LC are read-only. Shared references may be consumed at recorded identities but never silently rebound; copied output is never independently generated evidence.

Owned patterns are exactly `docs/analysis/sci_md_002b/**`, `validation/cases/sci_md_002b/**`, `scripts/sci_md_002b.py`, `tests/test_sci_md_002b.py`, `SCI_MD_002B_EXTERNAL_BUNDLE/**`, issue #74, and the task draft PR. Forbidden patterns are `docs/analysis/sci_lc_001a/**`, `validation/cases/sci_lc_001a/**`, `scripts/sci_lc_001a*`, `tests/test_sci_lc_001a*`, `solver/**`, `config/**`, production `cases/**`, all Puckworks paths, issue #70, PR #71, and every SCI-LC worktree/bundle/authority/process.

## Process, resource, and shared-file rules

The primary lane has priority. This tranche uses one worker, one nested numerical-library thread, no GPU, no OpenFOAM, at most 16 GiB RSS, and no heavy Puckworks sweep. Every owned process and PID is recorded. No other lane's process may be signaled, stopped, resumed, or reniced.

Shared status/strategy files are avoided while lanes coexist. Global generated metadata is touched only if canonical checks require it, in a distinct reconciliation commit, and regenerated after serial integration. SCI-LC scientific files are never concurrently edited.

## Integration and duplicate containment

Each lane is independently reviewed. The owner selects merge order; a later lane integrates accepted `main` and regenerates shared metadata. Frozen scientific sources are not rebased or rewritten, and agents do not mark their own PR ready or merge it. Results remain bound to exact execution source.

On any duplicate assignment, create and modify nothing further, signal no process, inventory branches/worktrees/issues/PRs/processes/artifacts, report `DUPLICATE_ASSIGNMENT_CONTAINMENT_REQUIRED`, and stop.

## Claim ceiling and closeout

Prohibited promotions include physical or whole-solver validation, proof of real espresso causation, measured swelling/accommodation parameters, Mo-powder-to-source-grind mapping, production-physics promotion, swelling selection, SCI-LC conclusions, universal pressure/grind behavior, taste prediction, or combined-mechanism conclusions. Standing statements are `PHYSICAL_VALIDATION_NOT_ESTABLISHED`, `POST_OBSERVATION_MECHANISM_DISCRIMINATION`, `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`, `NO_COMBINED_MECHANISM_AUTHORIZATION`, and `NO_SCI_LC_001B_AUTHORIZATION`.

Closeout reports exact starting/final Git identities and commits; issue/PR state; hashes and row counts; Puckworks identity/cleanliness; model/gates/bounds/design blocks; exact verification and pilot evidence; external manifest identity; unchanged forbidden paths; process state; and the two required terminal statuses. Adjudicative execution, scientific reduction, ready transition, merge, and issue closure remain separately authorized.
