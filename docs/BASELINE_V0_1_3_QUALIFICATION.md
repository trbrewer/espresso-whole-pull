# Qualified v0.1.3 baseline retained by v0.1.4

Version 0.1.4 binds, but does not reinterpret, the target-qualified v0.1.3 numerical evidence.

The v0.1.3 standard campaign completed ten runs and passed all nine aggregate gates. The reference result reported:

| Quantity | v0.1.3 result |
|---|---:|
| First drip | 4.711696185 s |
| Final outlet flow | 1.482675972 mL/s |
| Cup water at 30 s | 36.170177 g |
| Cup solute at 30 s | 4.787691 g |
| Total beverage at 30 s | 40.957867 g |
| Time to 40 g | 29.374480 s |
| Cumulative TDS | 11.689306% |
| Extraction yield | 23.938453% |
| Maximum liquid residual | 6.00e-16 kg |
| Maximum solute residual | 1.84e-13 kg |

The declared qualification findings included:

- maximum 0.020 s versus 0.005 s time-step difference of approximately 0.124%;
- maximum 256 × 512 versus 512 × 1024 mesh difference of approximately 0.560%;
- maximum reference-rank difference of approximately 2.23e-9;
- serial/16-rank layered-fixture agreement at approximately 1e-12 or better for flow and both probes;
- 32 ranks as the fastest tested routine configuration for the 131,072-cell reference mesh.

The machine-readable evidence is retained under:

```text
baseline_evidence/v0_1_3/
```

The `source_contract/` subdirectory provides the exact solver, reduced mathematics, configurations, Make files, initial fields, and discretization dictionaries against which v0.1.4 proves no governing-physics change.

This evidence establishes numerical qualification of the bounded model, not independent physical validation.
