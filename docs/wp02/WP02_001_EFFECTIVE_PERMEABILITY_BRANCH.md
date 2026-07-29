# WP02-001 saturated effective-permeability branch

Declaration: `GOVERNING_PHYSICS_CHANGE`.

WP02-001 adds one optional, disabled-by-default saturated hydraulic closure.
It maps the locked Waszkiewicz dissolution-indexed dynamic-flow shape onto the
existing basket-pressure-calibrated Darcy permeability. The source shape uses
the nominal 9-bar or 8-bar campaign bin; the absolute Darcy scale retains the
corrected basket/puck-inlet pressure. This interface mapping is not claimed as
a verbatim paper permeability equation.

The authoritative frozen contract is
[`WP02_001_CLOSURE_CONTRACT.json`](../../validation/wp02/WP02_001_CLOSURE_CONTRACT.json).
Canonical scenarios are generated and checked with:

```bash
python3 scripts/wp02_contract_bridge.py --root . --check
```

The branch is inactive during wetting. After saturation but before source
support, it holds the source state at 10.01001001001001 s and applies the
predeclared `1e-6` elliptic regularization floor. Thereafter it uses
`source_time = solver_time - 3 s`. The fixed source-processing 8-second offset
is excluded.

The frozen comparisons are the unchanged five-shot 9-bar reconstruction and a
four-shot 8-bar no-retuning same-campaign transfer. Neither comparison is
independent validation. No parameter, activation time, pressure, floor,
smoothing, shift, or scale may be selected from their scores.

The implementation does not move the mesh, change porosity or storage, modify
wetting, add solid mechanics, machine coupling, fines, channeling, thermal
transport, or chemistry. Physical validation remains `NOT_ESTABLISHED`.

Commit 1 omitted the mandatory uniform-pressure verification fixture. A
separate pre-execution completeness correction adds the canonical
`fixture_WP02_001_uniform_pressure` case, its serial runner, and its
closed-form/OpenFOAM verifier without changing the frozen solver or closure.
The fixture contains no protected observations and is code verification, not
physical validation.

Fixture attempt 1 used ten-significant-digit ASCII field output. Its CSV trace
matched the independent multiplier to `7.43e-15` relative error, while the
round-tripped field failed the unchanged `1e-12` gate because of serialization
rounding. The fixture-only field precision is therefore frozen at 17
significant digits for double-precision round-trip code verification. This
changes no solver calculation, scientific value, or acceptance tolerance.

Both governed OpenFOAM executions then completed. The first analyzer invocation
stopped before parsing protected rows because the recorded trace endpoints
(`102.999999999997 s`) were representation-equivalent to, but slightly below,
the governed `103.0 s` endpoint. The frozen analyzer correction reconciles only
source index 999 within a `1.4551915228366852e-11 s` ULP-scale bound, selects
the existing final trace sample, and changes no trace, source grid, mapping,
selector, gate, or score formula. The failed invocation is retained as a
`PRE_SCORE_SOFTWARE_FAILURE` in the
[endpoint amendment](../../validation/wp02/WP02_001_ANALYZER_ENDPOINT_AMENDMENT.json).

The one committed score-bearing analysis is recorded in the
[result](../../validation/wp02/WP02_001_VERIFICATION_AND_RESULTS.json) and
[run status](../../validation/wp02/WP02_001_RUN_STATUS.json). The five 9-bar
normalized RMSE values were `0.0839666`, `0.0720130`, `0.129074`, `0.0812166`,
and `0.103868`; Pearson values were `0.990718`, `0.991767`, `0.951082`,
`0.989034`, and `0.965891`. The four 8-bar normalized RMSE values were
`0.0811251`, `0.0626600`, `0.0637870`, and `0.143777`; Pearson values were
`0.989670`, `0.989147`, `0.989170`, and `0.978228`. Both predeclared aggregate
gates passed without fitting or post-result adjustment.

The 9-bar outcome is a source-linked reconstruction test. The 8-bar outcome is
a predeclared no-retuning same-campaign comparison, not independent
validation. Neither establishes full poroelastic deformation, transfer across
rigs, early wetting, channeling, chemistry, taste, or a universal permeability
law. Physical validation remains `NOT_ESTABLISHED`.
