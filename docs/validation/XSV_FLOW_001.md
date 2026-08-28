# XSV-FLOW-001 prescribed-flow boundary

Select the interface explicitly; omission still selects `prescribedPressure`.

```foam
pressureBoundaryModel prescribedFlow;
prescribedFlowBoundary
{
    scheduleType constant;
    volumetricFlowRateM3PerS 1.0e-6;
    absoluteFlowToleranceM3PerS 1.0e-12;
    relativeFlowTolerance 1.0e-8;
}
```

For a linear schedule, use `scheduleType piecewiseLinear`, `timesS`, and an
equal-length `volumetricFlowRatesM3PerS` list. Times must increase strictly and
cover the run. The solver samples at `runTime.value()`—the existing production
right endpoint—and linearly interpolates between knots. Endpoint and exact-knot
values are used directly. Targets are nonnegative full-basket volumetric flow
in m³/s, positive from inlet to outlet. `targetInletPressure` remains a legacy
schema field but is ignored in this mode.

The v1 boundary admits only initially fully saturated, static-mesh,
incompressible Darcy cases with `uniform` or `axial_two_layer` permeability.
It rejects wetting, Forchheimer resistance, compaction, evolving permeability,
machine compliance, nonzero pressure ramp, radial profiles, reverse targets,
and incompatible pressure patch types.

At startup the solver applies a 100 kPa numerical reference drop to a separate
no-read/no-write pressure copy, solves the production finite-volume operator,
and divides its globally reduced, sector-scaled signed outlet flux by 100 kPa.
At each step it divides the requested flow by that discrete conductance, solves
the ordinary pressure equation, and verifies target error, signed inlet/outlet
closure, direction, and agreement with the legacy positive outlet trace. Zero
flow gives inlet pressure equal to outlet pressure and is governed by the
absolute tolerance.

Only active prescribed-flow cases create
`postProcessing/prescribedFlow/0/prescribed_flow.csv`. Its columns report time,
target and achieved signed/positive flows, inlet flow and pressures, discrete
conductance, error and limits, error ratio, closure, reverse flows, and the
three runtime gate flags. The existing `wholePull/traces.csv` schema is
unchanged.

The XSV-FLOW-001 result supports only the claim “implemented and numerically
qualified” for this discrete synthetic contract. It changes no constitutive,
material, extraction, or machine physics; physical validation remains
`NOT_ESTABLISHED`. An accepted schedule is not thereby a measured schedule.
