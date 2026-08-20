# SCI-LC-001A-INF-001 execution-family correction

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`. This correction changes
control infrastructure only. It cannot authorize science, alter the matrix,
classify evidence, invoke D4/X1/OpenFOAM/Puckworks, or create Attempt 05.

`scripts/sci_lc_001a_family_controller.py` is the single authority-bound family
controller. Its versioned states are `UNALLOCATED`, `RESERVED`, `STARTING`,
`RUNNING`, `STOP_REQUESTED`, `FINALIZING`, `COMPLETE`, `FAILED`, `STOPPED`,
`ABORTED_BEFORE_DISPATCH`, `ARCHIVED`, and `QUARANTINED`. Illegal transitions
fail deterministically. Scientific eligibility is recorded separately.

Reservation holds an exclusive `flock`, validates a closed exact authority
record, rejects ordinals above its stated maximum or above 04, refuses a
pre-existing root, binds authority/head/tree/root/controller identity, and
persists through file and directory `fsync` plus atomic replacement. Repeating
the identical reservation is idempotent; a conflicting reservation fails.
The supervised launcher deliberately accepts separate closed-schema control
and execution authority files through `SCI_LC_CONTROL_AUTHORITY` and
`SCI_LC_EXECUTION_AUTHORITY`; the former reserves the attempt slot and the
latter is validated by the scientific executor. The family-hold record must
match the exact control-authority SHA-256 at reservation and dispatch gates.

The family hold is closed-schema and is checked at allocation, reservation,
post-reservation, root/unit/service boundaries, pre-dispatch, every dispatch,
replacement, retry, resume, recovery, classification, and publication. The
executor now refuses real dispatch without the controller and checks it before
each key. Readiness is permanently synthetic and reports zero canonical keys,
zero budget consumption, and an unreachable canonical dispatcher.

Process identity includes PID, `/proc` start ticks, executable, command digest,
working directory, unit, attempt, root, and authority hash. Recovery returns a
typed no-dispatch disposition for live-process/missing-manifest,
dead-process/running-manifest, service/process/lease mismatch,
root/reservation mismatch, and stale lease after a terminal manifest.

The version-controlled wrapper handles normal exit, SIGINT, and SIGTERM and
drives idempotent finalization. The systemd template uses `Restart=no`,
`KillMode=control-group`, fixed environment binding, journal capture plus
wrapper-owned fixed evidence logs, and `ExecStopPost`. The prior external
readiness-only no-op wrapper had SHA-256
`695cd1ad2d7ab6be0aa62933932faa1c1cd24fef863bad180b8f089b8413b8a9`;
it is historical evidence and not an execution dependency.

The focused suite covers concurrent and repeated reservation, Attempt 05,
holds, interrupted state, lifecycle legality, dispatch consumption, repeated
terminalization/cancellation, SIGINT/SIGTERM/systemd/supervisor-loss paths,
stale leases, orphan states, service mismatch, readiness isolation,
quarantine immutability, import absence, and PID-reuse-resistant identity.
Canonical Stage-A dispatch in all tests is zero.
