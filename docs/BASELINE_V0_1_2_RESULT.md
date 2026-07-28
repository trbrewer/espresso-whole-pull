# Successful v0.1.2 target baseline retained as historical evidence

The bundled baseline run-status artifact records a completed OpenFOAM Foundation 12 execution on `<HOSTNAME>` with 64 MPI ranks.

Selected results were:

| Quantity | v0.1.2 result |
|---|---:|
| First drip | 4.701696185 s |
| Final outlet flow | 1.480794817 mL/s |
| Beverage mass at 30 s | 40.91085794 g |
| Time to 40 g | 29.40444868 s |
| Cumulative TDS | 11.70000447% |
| Extraction yield | 23.93286103% |
| Maximum liquid residual | 2.50e-15 kg |
| Maximum solute residual | 1.85e-13 kg |

All required v0.1.2 numerical gates passed. The result also exposed the two small systematic effects corrected in v0.1.3:

- a `-0.1268756%` straight-sided wedge scaling bias;
- a `-0.010 s` end-step pressure-ramp bias in first-drip timing.

The original machine-readable artifact is included at:

```text
baseline_evidence/v0_1_2/ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_2.json
```

This is predecessor regression evidence. It is not a v0.1.4 runtime result and is not independent physical validation.
