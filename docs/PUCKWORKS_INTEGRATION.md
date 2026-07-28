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

WP01R-001 recommends `ADOPT_WITH_FOLLOWUP`; that dependency review does not
authorize calibration, protected comparisons, or R1 implementation.

The issue #4 dossier is prepared from the exact locked commit:
[Markdown](evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.md) and
[JSON](../validation/evidence/WASZKIEWICZ_R1_SOURCE_DOSSIER.json). Its
disposition is `READY_FOR_WP01R_003_WITH_DECLARED_GAPS`; issue #5 must freeze
the calibration/protected-comparison contract before implementation.
