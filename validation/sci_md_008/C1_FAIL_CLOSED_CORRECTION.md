# SCI-MD-008-C1 fail-closed correction

The original public command-line route and its inventory-dependent scientific
STOP were valid. Review found an unused but callable implementation that could
run and score the blocked 48-condition target matrix, plus a synthetic helper
that could emit inventory-invariance PASS rows without production execution.

C1 deletes `run_matrix`, `score`, `prediction_row`, `inventory_gate`,
`adjudicate`, and the unreachable target-plot generator. The module now has one
scientific runner, `run_inventory_gate`, and validates the real 36-row gate
table, 18-run manifest, recomputed maximum difference, exact STOP disposition,
zero target predictions, and four explicit BLOCKED target tables before
returning the nonzero scientific-stop status.

No production run, target scoring, parameter change, governing-physics change,
or scientific reinterpretation occurred during this correction. The retained
result remains
`SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT`.
