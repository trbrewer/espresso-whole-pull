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
  --baseline-solver /external/path/starting-main/espressoWholePullFoam
```

The runner returns 0 on PASS, 2 on numerical qualification failure, and 3
when OpenFOAM is unavailable. Generated cases, logs, meshes, fields, and
processor directories remain outside Git.

R1 remains a preserved FAIL. Its reduced-PDE comparison was non-adjudicative
because forcing and source/capacity semantics differed. R2 instead compares
the C++ observer with an independent Python oracle built by differencing the
solver's per-step cumulative mass traces. This qualifies the observation and
partition interface only; it is not physical validation and does not validate
the transport PDE, an experimental campaign, or an indexed kinetic law.
