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

The issue #5 contract is now prepared against that same exact lock:
[Markdown](validation/R1_CALIBRATION_AND_COMPARISON_CONTRACT.md) and
[JSON](../validation/contracts/R1_CALIBRATION_AND_COMPARISON_CONTRACT.json).
It freezes one active calibration degree of freedom (uniform permeability)
and five protected per-shot flow shapes. Chemistry is unprotected, and no
poroelastic closure is implemented. Once approved and merged, issue #6 may
implement the deterministic bridge and R1 case generator.

WP01R-004 implements that deterministic bridge:
`python3 scripts/r1_contract_bridge.py --root . --output
config/reconstruction_R1_waszkiewicz_9bar.json --check`. The governed outputs
are the [canonical scenario](../config/reconstruction_R1_waszkiewicz_9bar.json),
[input provenance](../validation/r1/WP01R_004_INPUT_PROVENANCE.json), and
[generated-case manifest](../validation/r1/WP01R_004_GENERATED_CASE_MANIFEST.json).
No Puckworks code or protected series is copied or executed.
