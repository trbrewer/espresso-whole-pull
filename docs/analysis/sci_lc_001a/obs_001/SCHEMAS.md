# OBS-001 diagnostic schemas

- `espresso.whole_pull.sci_lc_001a.multiplier_stop_event.v1`
- `espresso.whole_pull.sci_lc_001a.multiplier_margin_summary.v1`
- `espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_health.v1`
- `espresso.whole_pull.sci_lc_001a.multiplier_diagnostic_manifest.v1`

Every float is retained as a human value when finite, Python round-trip text,
big-endian IEEE-754 binary64 hexadecimal bytes, dtype, and finite category.
Vectors retain shape, dtype, component order, and exact elements. Unknown fields
and missing required fields fail validation.

Minimum-margin ties use accepted-step index, candidate-step index, simulation
time, profile order, sector index, then event sequence. Record identities exclude
wall-clock time. The manifest binds each expected dynamic key to exactly one
terminal record and declares an ordinary guard-event stream count of zero.
