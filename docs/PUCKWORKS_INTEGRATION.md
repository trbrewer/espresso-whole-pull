# Puckworks Integration

Puckworks is the external public evidence/model/data dependency. This
repository uses a machine-readable full-commit lock and deterministic
checkout-and-verification script, not a Git submodule.

The reviewed `refs/heads/main` snapshot is
`fc61c4670ec7bf801e40bb391aab16048b8da26b`. The lock means
`REVIEWED_MAIN_AT_RECORDED_UTC_CUTOFF`; it does not claim permanent alignment
with a moving upstream branch. See the
[impact report](integration/PUCKWORKS_UPDATE_IMPACT.md) and its
[machine-readable companion](../validation/integration/PUCKWORKS_UPDATE_IMPACT.json).

Puckworks is neither vendored nor a submodule. No rights-restricted material is
copied, and per-artifact rights review remains required. Future adopted inputs
must record model IDs, units, pressure nodes, evidence roles, uncertainty, and
rights status.

WP01R-001 recommends `ADOPT_WITH_FOLLOWUP`. Issue #4, the governed
source/quantity/evidence dossier, is next; this dependency review does not
authorize calibration, protected comparisons, or R1 implementation.
