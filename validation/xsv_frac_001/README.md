# XSV-FRAC-001

`NUMERICAL_METHOD_CHANGE`; governance class G2; no new governing physics.

The optional collector partitions the exact component increments used by the
production solver's existing rectangular per-step cup-mass quadrature. A
single scalar allocation is applied to water and every species when one step
crosses one or more cumulative beverage-mass boundaries. Boundary times use
`piecewise_constant_step_flux_mass_partition` and are diagnostic only; no PDE
state is interpolated.

Run the synthetic harness outside Git after loading Foundation OpenFOAM 12:

```bash
python3 -m tools.xsv_frac_001.runner \
  --work-root /external/path/xsv-frac-001 --openfoam-ranks 1 2 \
  --candidate-build-receipt /external/path/candidate-receipt.json \
  --baseline-build-receipt /external/path/baseline-receipt.json
```

The runner returns 0 on PASS, 2 on numerical qualification failure, and 3
when OpenFOAM is unavailable. Generated cases, logs, meshes, fields, and
processor directories remain outside Git.

R1 remains a preserved FAIL. R2 replaced the noncomparable reduced-PDE
acceptance route with an independent trace-difference observer oracle and
produced 20/20 passing observer comparisons, but its executable/source binding
and cross-level adjudication remained insufficient; R2 therefore remains a
preserved terminal FAIL. R2A closed those two gaps and passed the complete
bound qualification, deterministic replay, serial/two-rank equivalence, all
four default-disabled regressions, hosted CI, and focused exact-head review.
PR #110 is merged, issue #109 is closed, and the final disposition is
`XSV_FRAC_001_R2A_PASS_MERGED_AND_CLOSED_RETURN_TO_MODEL_DEVELOPMENT`. This
does not validate the transport PDE, indexed kinetics, an experimental
campaign, or physical espresso behavior.
