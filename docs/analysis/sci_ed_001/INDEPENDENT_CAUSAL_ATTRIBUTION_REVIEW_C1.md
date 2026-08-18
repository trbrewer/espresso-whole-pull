# SCI-ED-001-C1 independent causal-attribution review

Phase-I disposition: `SCI_ED_001_C1_REVIEW_CONFIRMS_COMMON_HISTORY_FEATURE_ASYMMETRY`.

Primary classification: `COMMON_HISTORY_FEATURE_ASYMMETRICALLY_EXPOSED`.

The review examined candidate commit `640540b23e400a95ce86dcd718fa372217912738`, tree `7a71ebabda86c44d2700a8cf979baf0f50d392ee`, and immutable execution attempt 004 with ordered raw aggregate `9a0bcea35850d8ea94db16e0aa9a6af15fc7f2ee8b0f2bae6be6b5a4cdd5336e`.

All 292 family/stem/resolution groups were compared across P0--P8. There were 148 exactly identical prefixes and 144 numerically identical prefixes; zero groups materially differed. The maximum relative difference was `4.8905016961739676e-14`. Every design-zero pressure was exactly 500,000 Pa. The maximum cross-program difference in `normalized_flow_at_0s` was `4.440892098500626e-16`.

`normalized_flow_at_0s` uses only the frozen `[-2,0]` denominator interval and the exact design-zero row. It uses no sample with `t_design > 0`. The P8 ramp has not changed pressure at that state. The diagnostic is available from every raw program trajectory but was emitted only for P8 by its implementation event list.

Commit A froze generic normalization families and event windows. It did not explicitly name `normalized_flow_at_0s`, nor did it freeze the concrete P8 `[0,10]` extraction list. Normalized event-point features first appeared in execution-source correction commit `5217b4b8b9984e01a849b82bda6d61b60ff07a2c`. Their exact prospective mapping is ambiguous. Independently of that mapping gap, an exact-zero common-prefix feature cannot earn pressure-program coverage.

The defect is load-bearing because all three robust N1 separations attributed to P8 selected this feature. Phase II is authorized. No corrected ranking, coverage, set cover, or outcome was calculated before the correction rule in Commit E.

