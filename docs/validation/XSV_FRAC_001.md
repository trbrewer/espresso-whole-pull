# XSV-FRAC-001 exact discrete cup fractions

## Result

`XSV_FRAC_001_R2_OBSERVER_QUALIFICATION_FAIL_TERMINAL`

The optional production observation interface conservatively splits the
existing discrete water and per-species solute cup increments at cumulative
beverage-mass boundaries. R2 passed all 20 frozen behaviors against an
independent discrete-stream observer oracle, including refinement levels,
serial/two-rank comparison, deterministic replay, and four default-disabled
runtime regressions. These numerical observations are preserved, but the
exact-head review rejected acceptance because executable/baseline authority
was not fail-closed and cross-level refinement was not adjudicated. Those
substantive defects make the terminal R2 disposition FAIL.

R1 remains an overall FAIL. Its zero boundary errors and approximately
`2.71e-20 kg` component residuals were valid but incomplete observations. Its
legacy cumulative pseudo-species output was defective, and its reduced-PDE
parity was non-adjudicative because the two routes used different pressure
forcing and different source/capacity algorithms. R2 fixes the legacy output
and removes that reduced-PDE route from acceptance; it does not reinterpret
the R1 scores as a production-model disagreement.

“Exact” refers only to conservation against the production solver's existing
rectangular per-step cup-mass quadrature. It does not reconstruct continuous
sub-timestep chemistry or internal PDE state.

## Scope and claim ceiling

No governing physics, pressure boundary, prescribed-flow behavior, extraction
kinetics, inventory predictor, or experimental mapping was added. No
experimental or protected data were used. Physical validation remains
`NOT_ESTABLISHED`; SCI-MD-006 remains unchanged and EXP-006 remains future
experimental work.

The R2 contract is `validation/contracts/XSV_FRAC_001_R2_CONTRACT.json`.
`validation/xsv_frac_001/R1_RESULT.json` preserves R1,
`validation/xsv_frac_001/R2_RESULT.json` records the complete R2 matrix, and
`validation/xsv_frac_001/RESULT.json` is the programme summary. Generated run
products remain outside Git under evidence identity
`xsv-frac-001-r2-qualification-final-677bc30`.
