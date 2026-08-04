# VAL-CORPUS-002 Stage B1 recovery result

`VAL_CORPUS_002_STAGE_B1_CALIBRATION_COMPLETE_PENDING_REVIEW`

Attempt 1 remains immutable and `INFRASTRUCTURE_INTERRUPTED`. All 20 PASS
evaluations were content-verified as a complete cache with aggregate
`5b42c436b7f7b29bff9c5f38b39541be785dbcf4e1c2052ee3d064768a9e340f`.
Evaluation 20 is append-only adjudicated as
`POST_END_MPI_FINALIZATION_INFRASTRUCTURE_FAILURE`; evaluation 21 remains
`BLOCKMESH_PRE_SOLVER_INFRASTRUCTURE_FAILURE`. Neither has an objective or
cache eligibility.

Attempt 2 replayed the frozen optimizer from its original bounds. It reused
20 verified objectives and completed 26 new zero-exit evaluations. There were
no attempt-2 infrastructure failures or typed numerical failures. The final
log interval width was `7.687140035628204e-09`, within the frozen `1e-8`
tolerance.

The selected fresh evaluation is `k = 0.3439597024835067 s^-1`
(`0x1.6036f8e53bf4ep-2`), with `log(k) = -1.0672307724139207`
(`-0x1.11360930cd77cp+0`) and objective
`0.003931989579189616`. Its ordered 20/40/60 g model vector is
`[2.782144673131987, 4.227214080217558, 4.334636376028199] g`.
All target, finite, boundedness, TDS, liquid-balance, and solute-balance gates
pass. The governed validator and P2 freeze barrier pass. This freezes only a
candidate eligible for independent review; Stage B2 has not started, bulk P2
materialization was not performed, and no transfer result was accessed.
