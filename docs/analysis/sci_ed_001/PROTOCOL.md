# SCI-ED-001 prospective protocol

## Question and hypotheses

The screen asks which frozen pressure program, or smallest set of at most
three programs, and which synchronized measurement package robustly
distinguishes transient poromechanics, one-way wetting-age swelling,
fixed-active-bed axial fines deposition, and generic relaxing resistance.
H0 through H8 are frozen exactly as stated in Issue #79 and the controlling
execution authority: constant-pressure non-identifiability; reversible unload
signature; persistence; rate/history; direct-measurement advantage;
apparatus-observability distinction; possible multi-program need; structural
equivalence; and reduced-model-space limitation.

## Frozen families and initial state

The primary envelope contains all 35 valid finite-rate SCI-MD-002A stems for
both F_TPM and F_GENERIC, all 72 physically and numerically valid SCI-MD-002B
stems, and all four inventory-feasible and numerically/physically valid
SCI-MD-002C stems. The other 92 fines candidates remain provenance controls
and do not enter the viable family envelope. No favorable representative is
selected.

All families begin from their canonical predecessor state and evolve at
500000 Pa basket-top gauge pressure. From the SCI-MD-002B front identity,
using its frozen hydraulic anchor `2.7738376540492074e-15 m2`, the conservative
full-depth bound at 5 bar is `3.6566667790356795 s`. The frozen safety margin
is `max(1.0 s, 10%) = 1.0 s`, giving `t_pre = 4.65666677903568 s`. No state is
reset at `t_design=0`. Fines retain `SYNTHETIC_WINDOW_START_RESET` and
`PRE_WINDOW_FINES_STATE_NOT_ADJUDICATED`.

## Programs, observables, and uncertainty

P0 through P8, their exact piecewise-linear breakpoints, the 80 s horizon,
measurement packages M0 through M6, N0/N1 interval expansions, denominator
floor, output grid, feature list, event windows, companion contrasts, and
normalizations are frozen in the canonical JSON. A 20 ms output grid is a
planning-compatible numerical grid, not demonstrated instrument performance.
No fines uncertainty target exists, so a direct fines feature is
`DIRECT_MEASUREMENT_TARGET_NOT_QUANTIFIED` under N1.

Absolute outputs are used only when node, unit, reference, and hydraulic
anchor are directly comparable. Primary dynamic features use prospectively
declared ratios and matched-program contrasts. Missing outputs are not zeros;
structural zero is used only where an inherited contract explicitly excludes
the state.

## Numerical and adjudication rules

Every eligible family/stem/program response has matched 20 ms base and 10 ms
refined integrations. Numerical uncertainty is the absolute feature
difference. Family intervals span every eligible stem and expand by numerical
and, for N1, planning measurement bounds. Pairwise separation requires
strictly disjoint complete intervals. Overlap, numerical uncertainty,
non-comparability, and unquantified direct measurements remain distinct.

Program ranking and the capped deterministic set cover use the lexicographic
rules in `SCI_ED_001_PROTOCOL.json`. No response-dependent program, feature,
threshold, parameter, window, normalization, or row may be added.

## Execution and claim boundary

Commit A freezes this protocol and the current-main production-physics
boundary. Commit B must pass predecessor replay before any adjudicative run.
Complete atomic records remain in immutable attempts under the external
symbolic namespace `SCI_ED_001_EXTERNAL_BUNDLE`; Git receives only bounded
reductions.

The active solver already contains accepted historical governing changes.
The task-specific verifier proves only
`SCI_ED_001_INTRODUCED_NO_NEW_GOVERNING_CHANGE` relative to the frozen start.
The historical v0.1.4 verifier is retained and is not an active-solver
equivalence gate.

This is `MODEL_INFORMED_FUTURE_DESIGN_ONLY`.
Physical validation is not established and experimental commissioning is not
authorized.
