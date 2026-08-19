# SCI-LC-001A OBS-001 bounded multiplier observability

OBS-001 adds default-disabled, one-way observation at the existing multiplier
guard, contact-direction, candidate-state, accepted-step, located-root,
stopped-result, and normal-completion locations. It declares
`NO_GOVERNING_PHYSICS_CHANGE` and `NO_NUMERICAL_METHOD_CHANGE`.

The single explicit configuration field is `multiplier_diagnostics`, supplied
through `--multiplier-diagnostics-config`. Its modes are `DISABLED`,
`ENABLED_OPTIONAL`, and `ENABLED_REQUIRED`. Enabled modes require an absolute
external sidecar root. No environment or directory-based activation exists.

Every dynamic key receives exactly one terminal diagnostic disposition.
Multiplier-evolution-applicable keys produce either a bounded minimum-margin
summary or a multiplier-domain terminal-event record. Keys with no resistance
evolution receive `NOT_APPLICABLE_NO_RESISTANCE_EVOLUTION` in the manifest and
do not fabricate multiplier evidence. Ordinary guard evaluations are counted
but not streamed. Per-key
records and run-level manifest and health objects use deterministic canonical
JSON, same-filesystem temporary files, flush, fsync, atomic rename, post-write
validation, and no-overwrite behavior.

Both enabled modes are fresh-execution-only. Resume, scientific-result reuse,
prior-manifest consumption, or a nonempty prior result/sidecar root fails before
the first scientific key with
`DIAGNOSTIC_ENABLED_REQUIRES_FRESH_COMPLETE_EXECUTION`. Disabled mode preserves
the pre-OBS reuse behavior.

Diagnostic callbacks return no scientific values. Exceptions are isolated and
reported under `DIAGNOSTIC_EVIDENCE_INCOMPLETE`; they do not rewrite scientific
status, stop token, state, metrics, eligibility, or classification.

Canonical Stage A execution, diagnostic replay, classification, root-cause
selection, correction, and merge remain unauthorized.

The historical `7f345f7` candidate was rejected pending correction because its
dynamic-key cardinality, enabled reuse, and recursive schema claims were not
established. Its no-physics and no-feedback findings remain supported; its
overall PASS claim is superseded.
