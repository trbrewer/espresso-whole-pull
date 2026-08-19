# OBS-001 diagnostic schemas

- `espresso.whole_pull.sci_lc_001a.multiplier_stop_event.v1`
- `espresso.whole_pull.sci_lc_001a.multiplier_margin_summary.v1`
- `espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_health.v2`
- `espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_manifest.v2`

Every float is retained as a human value when finite, Python round-trip text,
big-endian IEEE-754 binary64 hexadecimal bytes, dtype, and finite category.
Vectors retain shape, dtype, component order, and exact elements. Unknown fields
and missing required fields fail recursively at every closed object level.
Validation is independent of sealing: strict scalar types, closed enums,
SHA-256 encodings, decimal/hex float equivalence, state shape and order, sector
sets, bounds and margins, record/payload coupling, and health/manifest
reconciliation are checked after any independently recomputed integrity hash.
Stop-event validation additionally closes the currently empty parameter-binding
object, rejects undeclared per-sector state payloads, checks event-root sector
values against the retained primitives, couples the exited bound and contact
category to the signed margin, and requires exact exceedance values only for an
actual finite exceedance. Manifest v2 includes the scientific stop token so an
applicable `STOPPED` key cannot be mislabeled as a multiplier-domain stop merely
by asserting an expected payload type. Entries are key-ID sorted and validation
status is coupled to disposition and payload presence.

Minimum-margin ties use accepted-step index, candidate-step index, simulation
time, profile order, sector index, then event sequence. Record identities exclude
wall-clock time. Every expected dynamic key has one manifest disposition.
Applicable complete and multiplier-stopped keys bind a summary or stop record;
`NO_EVOLUTION` keys bind an explicit not-applicable disposition without a
multiplier payload. The ordinary guard-event stream count is zero.

Stop-event and margin-summary v1 retain their published structure and gain
strict enforcement only. Health and manifest increment to v2 because their new
applicability fields and reconciliation counts are incompatible required
structure. Historical v1 health and manifest records are superseded and are not
approved for replay.
