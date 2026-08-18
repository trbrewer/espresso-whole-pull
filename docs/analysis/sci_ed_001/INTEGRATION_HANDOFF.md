# SCI-ED-001 integration handoff

`SHARED_METADATA_RECONCILIATION_REQUIRED`

SCI-ED-001 deliberately did not edit shared metadata owned by the active SCI-LC-001A lane. A later integration owner must, after resolving all active-PR ordering, regenerate only the deterministic entries required for the final SCI-ED task-local files in:

- `SOURCE_PACKAGE_MANIFEST.json`;
- `PACKAGE_QA_STATUS.json`;
- any narrowly required `docs/PROJECT_STATE.md` integration status.

That owner must preserve the SCI-ED source hashes, execution authority, null result, claim ceiling, and the historical/current-physics-verifier distinction. No shared verifier, predecessor package, SCI-LC artifact, solver, configuration, case, dependency, or Puckworks lock requires an SCI-ED scientific change.

The prior stopped preflight remains external and non-adjudicative: `SCI_ED_001_BASELINE_RED`, corrected as `HISTORICAL_VERIFIER_INAPPLICABLE_TO_CURRENT_ACTIVE_SOLVER`, with no execution, repository change, branch, issue, PR, or bundle from that stopped attempt.

Review must confirm that PR #80 remains draft and that its path set has zero overlap with the live SCI-LC-001A PR.

