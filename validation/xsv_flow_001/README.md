# XSV-FLOW-001

XSV-FLOW-001 adds a default-disabled, discrete prescribed-flow boundary for
fully saturated static Darcy cases. The frozen qualification covers constant
and piecewise-linear full-basket volumetric-flow targets on uniform and aligned
axial-two-layer meshes, including zero flow, mesh and timestep series, serial
replay, two-rank equivalence, startup rejection, and unchanged legacy modes.

The controller obtains conductance from one solve of the production
`fvm::laplacian(hydraulicMobility, p)` operator and measures achieved flow from
`-pressureEquation.flux()`. It does not use the continuum oracle to control the
solver.

Evidence is simulated synthetic numerical qualification only. This work adds
no governing physics and establishes no physical validation.
