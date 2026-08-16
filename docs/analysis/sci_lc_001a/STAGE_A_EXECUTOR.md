# SCI-LC-001A Stage-A executor implementation authority

Status date: 16 August 2026

Change declaration: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`

```text
PROTOCOL_SPECIFIED = TRUE
EXECUTOR_IMPLEMENTED = TRUE_PENDING_REVIEW
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
output root. No such real authority is created by E1.

The four modes are:

- `plan`: validate canonical artifacts and construct the graph; zero solves;
- `validate`: additionally validate an external output root; zero solves;
- `execute`: require and validate a separate authority before dispatch;
- `summarize`: validate and summarize an existing store; zero solves.

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
all `SYNTHETIC_TEST_ONLY` records.

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
or record fails closed. No automatic scientific retry exists.

## Synthetic testing

`SYNTHETIC_TEST_ONLY` exercises all 3,666 keys, persistence, interruption,
resume, dependency arithmetic, and summary generation without integrating a
canonical matrix trajectory. Synthetic records are labeled permanently and
cannot reach scientific classification or export.

The next action is one bounded independent exact-head implementation review.
A passing review may support a separate decision about a small timing pilot;
it does not itself authorize timing, scientific execution, D4, X1, readiness,
merge, or physical-validation claims.
