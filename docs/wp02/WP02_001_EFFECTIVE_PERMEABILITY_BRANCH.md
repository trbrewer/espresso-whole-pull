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
