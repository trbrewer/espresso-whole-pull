# XSV-FRAC-001 exact discrete cup fractions

## Result

`XSV_FRAC_001_IMPLEMENTED_NUMERICAL_QUALIFICATION_FAIL`

The optional production observation interface conservatively splits the
existing discrete water and per-species solute cup increments at cumulative
beverage-mass boundaries. Boundary and component closure passed the executed
synthetic matrix, but the independent reduced transport route exceeded the
frozen production/reduced parity ceilings. The failure is preserved without
retuning.

“Exact” refers only to conservation against the production solver's existing
rectangular per-step cup-mass quadrature. It does not reconstruct continuous
sub-timestep chemistry or internal PDE state.

## Scope and claim ceiling

No governing physics, pressure boundary, prescribed-flow behavior, extraction
kinetics, inventory predictor, or experimental mapping was added. No
experimental or protected data were used. Physical validation remains
`NOT_ESTABLISHED`; SCI-MD-006 remains unchanged and EXP-006 remains future
experimental work.

The frozen contract is
`validation/contracts/XSV_FRAC_001_CONTRACT.json`; the compact result is
`validation/xsv_frac_001/RESULT.json`. Complete generated evidence remains
outside Git under external identity `xsv-frac-001-qualification-r4`.
