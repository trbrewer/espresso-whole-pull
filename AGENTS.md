# Public Repository Agent Rules

- Read `docs/ONBOARDING.md`, `docs/PROJECT_STATE.md`, `docs/CLAIM_CEILING.md`, and the controlling strategy before substantive work.
- Preserve tag `v0.1.4-public.1` and the offline archival identities in `provenance/`.
- Declare every scientific change as `NO_GOVERNING_PHYSICS_CHANGE`, `SOURCE_SCENARIO_CHANGE_ONLY`, `NUMERICAL_METHOD_CHANGE`, or `GOVERNING_PHYSICS_CHANGE`.
- Never describe numerical qualification as physical validation.
- Do not silently reuse comparison or holdout data for calibration.
- Do not commit generated fields, meshes, processor directories, executables, full logs, uncleaned runs, credentials, hostnames, or local absolute paths.
- Keep Puckworks as a locked external dependency; do not copy rights-restricted material.
- Run source, static, Python, no-physics, shell, JSON, boundary, and secret checks before acceptance.
- Full OpenFOAM runs are manual and release-gated; retain complete evidence outside Git.
