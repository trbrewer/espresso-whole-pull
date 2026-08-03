# VAL-CORPUS-002 Stage B1 infrastructure recovery protocol

Status: prospectively frozen before recovery execution  
Authorization: `VAL-CORPUS-002-B1-CALIBRATION-2026-08-03`  
Profile: `EWP_CALIBRATION_STAGE_V1`

This append-only protocol preserves attempt 1 as
`IMMUTABLE_INFRASTRUCTURE_INTERRUPTED` and authorizes attempt 2 only as
`CONTROLLED_DETERMINISTIC_REPLAY_AND_CONTINUATION`. It does not authorize
Stage B2, transfer-result access, production or sensitivity execution,
protected scoring, refitting, governing-physics work, or merge.

The replay begins at the original frozen log-rate bounds
`[-4.470072424390813, 0.13509776159727813]`. The interrupted interval is
discarded. The best completed diagnostic is not selected and not frozen.
All 20 attempt-1 PASS evaluations must pass complete content verification or
the whole cache is rejected. Evaluations 20 and 21 are not cache eligible.
Reused objectives count toward the 128 objective-bearing evaluation limit;
infrastructure attempts are counted separately and never alter the scientific
interval.

Only `TypedNumericalEvaluationFailure` may become a failed optimizer
evaluation. `InfrastructureFailure`, including preparation, filesystem,
meshing, parsing, launch, MPI, and unclassified process failures, escapes the
optimizer without an objective or interval change. A typed numerical failure
requires affirmative model-output evidence: a pre-End OpenFOAM fatal event,
failure to bracket a target mass, a finite/boundedness or TDS failure, or a
liquid/solute conservation failure.

Evaluation 20 is adjudicated append-only. Its retained solver log reached one
normal `End` at the expected terminal time without a preceding OpenFOAM fatal
or numerical-abort marker; the nonzero exit occurred during MPI finalization.
Its corrected classification is
`POST_END_MPI_FINALIZATION_INFRASTRUCTURE_FAILURE`; it has no objective, cache
eligibility, or retained optimizer-interval effect and may not be salvaged.
Evaluation 21 remains `BLOCKMESH_PRE_SOLVER_INFRASTRUCTURE_FAILURE` with the
same restrictions.

Attempt 2 uses a new nonsymlink execution root. Before model execution it
records the exact environment and resource snapshot, verifies no stale task
process remains, and completes a non-model 16-rank MPI launch smoke check.
The solver, executable, MPI implementation, rank count, case controls,
scientific inputs, objective, bounds, tie break, and stopping rule remain
unchanged. A recurring infrastructure failure ends attempt 2; there is no
automatic third attempt.

P2 may be frozen only after optimizer convergence, a zero-exit selected
evaluation, every numerical gate, the closed governed validator, and the P2
freeze barrier all pass. Bulk P2 materialization and Stage B2 remain
prohibited.
