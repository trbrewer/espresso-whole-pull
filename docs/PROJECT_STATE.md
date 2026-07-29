# Project State

- Current development: `0.2.0-dev.1`, milestone `WP-0.2A`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- Public source verification: 129/129 PASS
- Scientific inputs: 19/19 byte-identical to archival baseline
- Frozen R0 scientific-configuration change: false
- Governed R1 scenario present: true
- WP01R-005 R1 scenario change: false
- Governing-physics change in WP01R-005: false
- Governing-physics change in WP02-001: true
- WP02 optional closure added: true
- Release qualification: `NOT_YET_FINALIZED`
- R0 claim ceiling: `NUMERICALLY_QUALIFIED_CALIBRATION_BASELINE`
- Physical validation: `NOT_ESTABLISHED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule

WP01R-001 dependency review is complete. Puckworks is locked to reviewed
`main` snapshot `fc61c4670ec7bf801e40bb391aab16048b8da26b` with recommendation
`ADOPT_WITH_FOLLOWUP`. WP01R-002 through WP01R-005 are merged, and issue #7
is complete. WP01R-005
completed one governed R1 execution and an explicitly non-blinded protected
comparison without retuning. Numerical, conservation, and calibration gates
passed; the protected flow-shape gate failed and exactly reproduced the
preliminary PR #16 disposition. R0 remains frozen and unchanged. Physical
validation is `NOT_ESTABLISHED`.

WP01R-006 selects the Waszkiewicz saturated dissolution-indexed
effective-permeability branch for WP-0.2A. No new physics is implemented by
the decision; issue #18 is the next governed implementation task.
Machine/headspace coupling remains the runner-up.

WP02-001 added the optional saturated dissolution-indexed effective-permeability
closure. Its corrected uniform fixture, disabled R0 regression, and disabled
constant-R1 regression passed. One governed 9-bar source-linked reconstruction
and one predeclared 8-bar no-retuning same-campaign comparison both passed their
frozen flow-shape gates. A retained-trace endpoint representation correction
was committed before the sole score-bearing analysis; neither solver was
rerun, and no fitting or post-result adjustment occurred. These same-campaign
results do not establish independent validation. Physical validation remains
`NOT_ESTABLISHED`.
