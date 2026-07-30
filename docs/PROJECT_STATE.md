# Project State

- Current released version: `v0.2.0`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- Public source verification: 149/149 PASS (WP02-002 development branch)
- Published v0.2.0 source verification: 131/131 PASS
- Scientific inputs: 19/19 byte-identical to archival baseline
- Frozen R0 scientific-configuration change: false
- Governed R1 scenario present: true
- WP01R-005 R1 scenario change: false
- Governing-physics change in WP01R-005: false
- Governing-physics change in WP02-001: true
- WP02 optional closure added: true
- Release qualification: `PASS`
- Release disposition: `SOFTWARE_AND_SOURCE_LINKED_RECONSTRUCTION_RELEASE_PASS`
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

WP-0.2F successfully published v0.2.0. WP01R-006 selected the Waszkiewicz saturated dissolution-indexed
effective-permeability branch for WP-0.2A. WP02-001 implemented and tested it,
merged through PR #20, and is scientifically closed. WP-0.2F release
finalization and WP-0.2G post-release reconciliation are complete. WP-0.3A
reviewed moving-upstream Puckworks evidence and froze the independent-holdout
and mechanism-discrimination contract without execution. No currently
reviewed candidate qualifies as an independent hydraulic holdout. The
solver-support triage adopts bounded evidence corrections, analytic
verification targets, and an inactive Vaca Guerra prior specification without
advancing the dependency lock. The next evidence task is the specified
independent pressure/flow campaign. Independent
physical validation has not started. Machine/headspace coupling remains a
later hypothesis subject to holdout evidence and a separate decision.

WP-0.3B implements non-protected Moroney, Matias, and Liang mathematical
references plus method-explicit TDS, EY, and retained-liquid measurement
kernels. They are verification support only, are not connected to WP02, and
do not establish physical validation. The canonical run passed Matias, Liang,
and observable gates but failed the predeclared Moroney timestep-refinement
ratio gate; the result remains a governed verification failure without
tolerance relaxation.

WP-0.3B-A1-P1 preserves that failure and the subsequent transcription and
derivation checkpoint. Commit 3B froze the state
`PREEXECUTION_FROZEN_AWAITING_CANONICAL_RESULT` before the amended invocation.
The P1 boundary corrects generated-path handling, historical-runner
reachability, observable uncertainty propagation, and Python 3.8 portability
without changing a scientific threshold.

The one P1-bound amended canonical invocation subsequently passed every
Moroney, Matias, Liang, and observable subgate. Its disposition is
`NONPROTECTED_EXTRACTION_REFERENCE_AND_OBSERVABLE_VERIFICATION_PASS_AFTER_GOVERNED_AMENDMENT`.
The original governed FAIL remains unchanged and independently addressable.
This mathematical and measurement verification does not establish physical
validation.

WP02-001 added the optional saturated dissolution-indexed effective-permeability
closure. Its corrected uniform fixture, disabled R0 regression, and disabled
constant-R1 regression passed. One governed 9-bar source-linked reconstruction
and one predeclared 8-bar no-retuning same-campaign comparison both passed their
frozen flow-shape gates. A retained-trace endpoint representation correction
was committed before the sole score-bearing analysis; neither solver was
rerun, and no fitting or post-result adjustment occurred. These same-campaign
results do not establish independent validation. Physical validation remains
`NOT_ESTABLISHED`.

WP-0.3C Stage 0 has begun as a protocol and input-intake scaffold. No final
preregistration exists, no commissioning or holdout acquisition has occurred,
and no model execution or scoring has occurred. Human, apparatus,
instrumentation, calibration-resource, material, and custody inputs remain
required. Readiness fails closed on incomplete or mismatched packages and a
complete package still requires separate governed review. Physical validation
remains `NOT_ESTABLISHED`.
