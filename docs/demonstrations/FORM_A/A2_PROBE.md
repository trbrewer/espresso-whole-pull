# A2 retirement and retained 9-bar probe

A2 was retired after partial execution. Its increasing recovery factor cannot delay physical front arrival relative to A1 under the same prescribed pressure history. Extraction indexing under R0 (0.15/s) also caps recovery at exp[-exp(-1/Xc)]. The full capability campaign was not completed; no A2 grade is assigned.

Xc from A1 at outlet M=Mc is **0.8294438807 / 0.8422833432 / 0.8524326302** at **6 / 9 / 11 bar**. The unchanged 9-bar value gives a recovery ceiling of **0.737080**. The single DESCRIPTIVE_ALL probe uses the existing 0.005-s step and solver; only field-output cadence changed to retain the requested snapshots.

| Time, s | A2/A1 flow | Mean X | Min cell X | Max cell X | Mean R_cell | Global R(M_A1) |
|---|---|---|---|---|---|---|
| 10 | 1.254014 | 0.324357630 | 0.164033123 | 0.619450437 | 0.505453111 | 0.400369122 |
| 20 | 1.155075 | 0.571878807 | 0.208518404 | 0.914709479 | 0.597318336 | 0.508024976 |
| 40 | 0.965114 | 0.939319817 | 0.769514005 | 0.995753488 | 0.720067730 | 0.745692699 |
| 60 | 0.810643 | 0.996592369 | 0.985449512 | 0.999788806 | 0.736167200 | 0.908151618 |
| 100 | 0.742525 | 0.999991514 | 0.999963510 | 0.999999478 | 0.737077362 | 0.992665790 |

Means are cell-volume weighted, equivalent to initial-solid weighting for this uniform R0 inventory. R_cell is evaluated from snapshot X; the [CSV](A2_PROBE.csv) also records the preceding-step recovery actually used and global R evaluated at A2’s own outlet mass. Global R in the table uses A1’s cumulative outlet mass on the same stable-pressure clock.

At 100 s the flow ratio is 0.742525 while X exceeds 0.999963 in every cell. This is a numerical probe observation, distinct from the algebraic recovery cap and its approximately 1.551 g/s descriptive liquid-flow bound. Ten completed A2 campaign cases, including both cases active when the hold arrived, are retained. All 69 unstarted cases remain blocked; no outputs were deleted.

[Parameters, hashes, native accounting and retained-case records](A2_PROBE.json). A0 and A1 remain unchanged.
