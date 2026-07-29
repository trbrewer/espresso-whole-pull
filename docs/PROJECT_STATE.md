# Project State

- Public baseline: `v0.1.4-public.1`, sanitized derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- Public source verification: 106/106 PASS
- Scientific inputs: 19/19 byte-identical to archival baseline
- Governing-physics change: false
- Scientific-configuration change: false
- R0 claim ceiling: `NUMERICALLY_QUALIFIED_CALIBRATION_BASELINE`
- Physical validation: `NOT_ESTABLISHED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule

WP01R-001 dependency review is complete. Puckworks is locked to reviewed
`main` snapshot `fc61c4670ec7bf801e40bb391aab16048b8da26b` with recommendation
`ADOPT_WITH_FOLLOWUP`. WP01R-002 through WP01R-004 are merged. WP01R-005
completed one governed R1 execution and an explicitly non-blinded protected
comparison without retuning. Numerical, conservation, and calibration gates
passed; the protected flow-shape gate failed and exactly reproduced the
preliminary PR #16 disposition. R0 remains frozen and unchanged. Physical
validation is `NOT_ESTABLISHED`; the next separately authorized solver task
should address the reproduced evolving-hydraulic-structure residual.
