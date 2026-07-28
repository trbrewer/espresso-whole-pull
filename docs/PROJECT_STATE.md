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
`ADOPT_WITH_FOLLOWUP`. WP01R-002 and WP01R-003 are merged; issues #4 and #5
are complete. The deterministic R1 bridge and case generator are implemented
on the WP01R-004 review branch. R0 remains frozen and unchanged. No R1
OpenFOAM execution or protected comparison has occurred; issue #7 is next
after implementation review and merge.
