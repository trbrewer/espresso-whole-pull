# SCI-ED-001 result

## Disposition

`SCI_ED_001_FROZEN_FAMILIES_REMAIN_OBSERVATIONALLY_EQUIVALENT`

The frozen screen did not identify a single program, or a set of at most three programs, that robustly separated all six primary family pairs under N1. The best ranked partial design was `P8_SLOW_RAMP_5_TO_9` with `M0`. It separated three of six pairs using the prospectively frozen `normalized_flow_at_0s` feature:

| Pair | N0 | N1 margin | N1 result |
|---|---:|---:|---|
| F_TPM / F_SWELL | 0.690564 | 0.288851 | ROBUSTLY_SEPARATED |
| F_TPM / F_FINES | -0.012730 | -0.081399 | OVERLAPPING |
| F_TPM / F_GENERIC | -0.055033 | -0.123988 | OVERLAPPING |
| F_SWELL / F_FINES | 0.692072 | 0.283451 | ROBUSTLY_SEPARATED |
| F_SWELL / F_GENERIC | 0.690762 | 0.281855 | ROBUSTLY_SEPARATED |
| F_FINES / F_GENERIC | -0.012531 | -0.088395 | OVERLAPPING |

The discriminating feature is the design-clock-zero flow divided by the frozen two-second pre-event mean. It therefore measures continued state evolution across the end of preconditioning, not a terminal-flow or absolute hydraulic-anchor difference. All other programs separated zero complete-envelope pairs under N1 with M0. The unload/reload, pulse, repeated-cycle, and fast/slow companion histories did not overcome full parameter-envelope overlap with the frozen extracted features.

M0 is `PARTIALLY_DISCRIMINATING`, not sufficient. M1 through M6 did not increase quantified coverage. Upstream pressure was not common to the family interfaces. Deformation, wetting, and fines outputs were family-specific rather than common quantitative observables; absent outputs were not treated as structural zero. No fines/turbidity uncertainty target existed. Consequently, direct-observable value remains `NOT_ESTABLISHED_IN_COMMON_COMPARISON_SPACE`, rather than zero.

## Execution authority

- Repository: `trbrewer/espresso-whole-pull`
- Worktree: `/home/tim/espresso-development/espresso-whole-pull-sci-ed-001`
- Branch: `research/sci-ed-001-virtual-pressure-program-discrimination`
- Issue: #79
- Draft pull request: #80
- Starting commit/tree: `e8a66378d7829877fb74c87889193f32dd977772` / `1c51175a8c5035c0cab989fada791aebb78f6fd7`
- Exact execution commit/tree: `5217b4b8b9984e01a849b82bda6d61b60ff07a2c` / `a15e6597c65a7c920ff84874c1798c6623efed97`
- Exact implementation SHA-256: `c8c4d6260ec25c94aa4b388d0bd63c19d45afaa1512f6f2f17018615384a3938`
- Protocol SHA-256: `fc04193bb95179ee7221f5a27974760c5ea2b0604f52182fe7a0c08f36eb5953`
- Case-matrix SHA-256: `d63a020aaf9f7afa381a2994941a686669d08a111bb18c48722068902e556448`
- External authority: `SCI_ED_001_EXTERNAL_BUNDLE/attempt_004`
- Rows: 2,628 expected, 2,628 completed, 0 invalid; 1,314 base/refined pairs
- Workers: 8; elapsed: 939.122 s; parent peak RSS: 199,368,704 bytes
- Ordered record aggregate: `9a0bcea35850d8ea94db16e0aa9a6af15fc7f2ee8b0f2bae6be6b5a4cdd5336e`

Attempts 001–003 are preserved as non-adjudicative failed attempts: authority typo, authority-byte canonicalization defect, and invalid absolute-anchor reduction, respectively. Attempt 004 was a complete fresh execution with no record reuse and passed bundle verification and deterministic reduction.

## Family signatures and limits

- F_TPM retained finite-rate resistance lag, reversible single-mode deformation, unload recovery, and hysteresis behavior across all 35 eligible stems.
- F_SWELL retained wetting-age state evolution, one-way swelling persistence, and accommodation dependence across all 72 eligible stems.
- F_FINES retained release, transport, deposition, outlet flux, cake resistance, pause/reload behavior, and the synthetic-window reset limitation across all four inventory-feasible stems. The 92 inventory-impossible rows remained controls only.
- F_GENERIC retained nonphysical relaxing-resistance lag and pressure-history dependence across all 35 eligible stems.

These signatures did not imply robust cross-family separation wherever the complete expanded intervals overlapped. The predecessor families had already been rejected for wrong source pressure ordering; this screen did not fit, rehabilitate, or physically select them.

## Limitations

This is post-observation, model-informed design using synthetic basket-top pressure programs. Initial states remain model-specific; fines retain `SYNTHETIC_WINDOW_START_RESET` and `PRE_WINDOW_FINES_STATE_NOT_ADJUDICATED`. Swelling is one-way coupled, poromechanics is one reversible mode, and generic relaxation is a nonphysical surrogate. There is no localization, combined mechanism, real apparatus feasibility model, independent data, demonstrated sensor performance, physical validation, or experimental commissioning.

`MODEL_INFORMED_FUTURE_DESIGN_ONLY`

`PHYSICAL_VALIDATION_NOT_ESTABLISHED`

`EXPERIMENTAL_COMMISSIONING_NOT_AUTHORIZED`

