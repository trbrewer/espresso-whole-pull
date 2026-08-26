# SCI-MD-007-R2 consumer qualification

Candidate scope: exact handoff of Puckworks producer candidate
`bd811cff2765573b5f9a4c8bf26f95a5a0d6392f` / tree
`5cbfa7092f9731f281e54e702065a31831b4ca53`.

The hermetic verifier passed exact export and manifest hashes, R2 schemas,
mandatory gate structures, independent Boolean disposition reduction, the
claim ceiling, and inactive predictor/physics boundaries. The optional
cross-repository verifier passed the exact remote, commit, tree, export object,
manifest object, and every input/output member hash in the producer manifest.

Qualification evidence:

- focused handoff and tamper suite: 14 test methods, PASS;
- complete Python suite: 968 tests, PASS;
- static validation: 38/38 gates, PASS;
- source manifest: 513 files, PASS;
- baseline, governing-change, release, WP-0.3A, WP-0.3B, and WP-0.3C boundary checks: PASS;
- shell syntax, JSON syntax, and secret-pattern scan: PASS;
- exact `origin/main...SCI-MD-007-R2` solver/case/config changed-path set: empty.

The legacy `verify_no_physics_change.py` comparison retains its pre-existing
main-versus-v0.1.3 solver-source difference. The exact SCI-MD-007 branch diff
contains no solver, case, or configuration change and is the task-specific
no-physics evidence.

No OpenFOAM command was executed. Physical validation remains
`NOT_ESTABLISHED`; this handoff does not establish extractable inventory or
`c_s0`, activate a runtime provider, reuse Angeloni, reopen SCI-MD-006, or run
the separate deferred G0 task.
