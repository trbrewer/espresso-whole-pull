# SCI-LC-001A Stage-A executor implementation authority

Status date: 16 August 2026

Change declaration: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`

```text
PROTOCOL_SPECIFIED = TRUE
EXECUTOR_IMPLEMENTED = TRUE_PENDING_E2_REVIEW
DIAGNOSTIC_TIMING_INTERFACE_IMPLEMENTED = TRUE_PENDING_E2_REVIEW
TIMING_PILOT_AUTHORIZED = FALSE
SCIENTIFIC_EXECUTION_AUTHORIZED = FALSE
PHYSICAL_VALIDATION = NOT_ESTABLISHED
```

## Boundary and scope

`scripts/sci_lc_001a_executor.py` implements the prospective Stage-A execution
interface for the frozen 1,280-row matrix and 3,666 `(case_id, profile)` keys.
It does not itself grant execution authority. `execute` requires a separate
absolute execution-authority artifact binding the exact Git HEAD and tree,
matrix semantic hash, protocol artifact hash, mode, backend, and external
output root. No such real authority is created by E2-R1.
`execute_authorized_graph` is the sole public real-execution path and constructs
a private validated context; private case executors cannot accept an authority
dictionary.

The six modes are:

- `plan`: validate canonical artifacts and construct the graph; zero solves;
- `validate`: additionally validate an external output root; zero solves;
- `execute`: require and validate a separate authority before dispatch;
- `summarize`: validate and summarize an existing store; zero solves.
- `pilot-plan`: validate an authority-bound exact allowlist; zero solves;
- `pilot-execute`: require a separate diagnostic timing authority.

Output roots must be absolute, outside the repository and scientific case
directories, and contain no symlink component. All records use same-directory
temporary files, `fsync`, and atomic rename.

## Graph and numerical profiles

Dynamic rows use exactly `BASE`, `INTEGRATOR_REFINED`, `STARTUP_REFINED`, and
`LINEAR_REFINED`; static rows use exactly `BASE` and `LINEAR_REFINED`. The
result is 2,212 dynamic keys plus 1,454 static keys, or 3,666 total. Cache and
resume identity is exactly `(case_id, numerical_profile)`. There is no combined
profile, retry, tolerance relaxation, profile substitution, hidden initial
condition, sampling trajectory, out-of-matrix sector case, D4 key, or X1 key.

## Scientific implementation

Static execution assembles the frozen one-exchange-plane ring system from the
canonical resistance primitives. BASE calls the authoritative scaled-pivot
binary64 solver. LINEAR_REFINED internally obtains BASE and performs the one
frozen correction.

Dynamic execution implements prescribed-ramp and machine-coupled storage,
lateral flux, signed resistance evolution, the canonical zero-flow
continuation, DOP853 profiles, RHS cap, dense output, and 1,001/2,001 sampling.
All flow thresholds operate on
`q_hat_sector_i=q_i/[(G_ref/N)*Delta_p_ref]`; dimensional and already-scaled
representations therefore share identical reversal and startup decisions.

The scientific gain floor is the non-overridable module constant
`GAIN_DENOMINATOR_FLOOR=1e-12`. Authoritative gain evaluation loads canonical
subject and comparator rows and result records internally. Uncertainty
evaluation derives applicability and profile dependencies internally.
Classification accepts only authoritative real-backend evidence and rejects
all `SYNTHETIC_TEST_ONLY` and `DIAGNOSTIC_TIMING_ONLY` records.

Owner authority `SCI-LC-001A-OWNER-METRIC-AUTHORITY-2026-08-16` prospectively
freezes current evolved-flow reconstruction, `H_q`, phase-invariant
Fourier/Nyquist and centered non-Fourier seed amplitudes, endpoint gain, and
composite-trapezoidal integrated gain on 1,001/2,001 grids. Sampling uses the
same BASE dense output and adds no trajectory. Static classification consumes
`(G_static_H,G_static_mode)` and dynamic classification consumes
`(G_coupling_end,G_coupling_int)` under the existing precedence.

Internal transport tuples remain constructible Python values. They are not
public executor inputs, are absent from the executor export list, and cannot
enter the authoritative gain, uncertainty, or classification paths. No
in-process authentication machinery is used.

## Result store and resume

The external store contains `RUN_MANIFEST.json` and atomic
`cases/<case_id>/<profile>.json` records. The manifest binds authorization,
Git identity, matrix and protocol hashes, executor source hash, output root,
backend, timestamps, task count, and status counts. Records bind case, profile,
row hash, role, boundary mode, authority, solver status, metrics, and checksum.

Resume validates the manifest and every reusable record. `COMPLETE`, `STOPPED`,
`CAPPED`, and `NUMERICALLY_UNRESOLVED` records are preserved and not retried.
Only absent or non-final interrupted work is dispatched. A mismatched manifest
or record fails closed. Records bind an immutable manifest-identity digest and
a manifest checksum ledger, so consistently stale and copied cross-run records
are rejected. No automatic scientific retry exists.

Directional multiplier events are terminal stops. No event can return to a
continuation path, no terminated dense solution is evaluated beyond its root,
and no counted RHS call is made solely to diagnose a root. Wrapped RHS calls
must equal solver-reported `nfev`.

## Diagnostic timing interface

Pilot selection is an explicit canonical case/profile allowlist whose hash and
maximum size are authority-bound. The first pilot requires a new or empty
external root and has reuse disabled. Its evidence kind is permanently
`DIAGNOSTIC_TIMING_ONLY`; it cannot enter scientific evidence, classification,
D4, or X1. E2-R1 creates no pilot authority and runs no pilot.

## Synthetic testing

`SYNTHETIC_TEST_ONLY` exercises all 3,666 keys, persistence, interruption,
resume, dependency arithmetic, and summary generation without integrating a
canonical matrix trajectory. Synthetic records are labeled permanently and
cannot reach scientific classification or export.

The next action is one bounded independent exact-head implementation review.
A passing review may support a separate decision about a small timing pilot;
it does not itself authorize timing, scientific execution, D4, X1, readiness,
merge, or physical-validation claims.
