# SCI-LC-001A OBS-001 bounded multiplier observability

OBS-001 adds default-disabled, one-way observation at the existing multiplier
guard, contact-direction, candidate-state, accepted-step, located-root,
stopped-result, and normal-completion locations. It declares
`NO_GOVERNING_PHYSICS_CHANGE` and `NO_NUMERICAL_METHOD_CHANGE`.

The single explicit configuration field is `multiplier_diagnostics`, supplied
through `--multiplier-diagnostics-config`. Its modes are `DISABLED`,
`ENABLED_OPTIONAL`, and `ENABLED_REQUIRED`. Enabled modes require an absolute
external sidecar root. No environment or directory-based activation exists.

Each dynamic key retains one terminal stop record or one bounded minimum-margin
summary. Ordinary guard evaluations are counted but not streamed. Per-key
records and run-level manifest and health objects use deterministic canonical
JSON, same-filesystem temporary files, flush, fsync, atomic rename, post-write
validation, and no-overwrite behavior.

Diagnostic callbacks return no scientific values. Exceptions are isolated and
reported under `DIAGNOSTIC_EVIDENCE_INCOMPLETE`; they do not rewrite scientific
status, stop token, state, metrics, eligibility, or classification.

Canonical Stage A execution, diagnostic replay, classification, root-cause
selection, correction, and merge remain unauthorized.
