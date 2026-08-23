# SCI-MD-004 Stage C implementation

Stage C adds a generic indexed passive-species route to
`espressoWholePullFoam`. Absence of `soluteTransportModel` retains the exact
legacy route. Indexed configurations declare ordered synthetic species with
explicit inventories or one structural-balance species. The balance species
receives the unallocated legacy extractable fraction and inherits all legacy
solute parameters.

Each indexed species owns dissolved-concentration, remaining-inventory, and
local-source fields. The existing beginning-of-step capacity law, timestep
inventory cap, filling update, saturated advection-diffusion equation, outlet
advection, and inlet back-diffusion operator are applied independently. The
legacy fields are sums and are never advanced separately in indexed mode.
Species state cannot enter pressure, saturation, wetting, porosity,
permeability, compaction, viscosity, density, mobility, velocity, Darcy flux,
machine state, boundary selection, timestep selection, or mesh generation.

The full legacy replay is byte-identical to the untouched base for
`traces.csv`, all three solute fields, and selected pressure, velocity,
saturation, wet-mask, porosity, permeability, mobility, and Darcy-flux fields.
The explicit indexed one-species replay has zero serialized difference in all
aggregate solute histories and exact checked hydraulic columns.

The additive V2--V18 manufactured matrix passes. V15 intentionally uses the
flowing zero-diffusivity limit to isolate source/advection mesh convergence;
the positive-diffusivity development sequence exposed 5.998% reference--fine
sensitivity in the inherited inlet boundary-gradient loss while its other
species quantities passed. Stage C does not alter that legacy operator. This
limitation is retained in external development evidence and does not support a
positive-diffusivity boundary-loss mesh-convergence claim.

Angeloni remains `PROTECTED_EXTERNAL_NO_RETUNING_ENDPOINT_HOLDOUT` with
`PREEXISTING_EXPOSURE = TRUE`. No target values were accessed, no prediction or
score was generated, and no species parameter was fitted. All Stage C values
are manufactured software-verification values. Physical validation remains
`NOT_ESTABLISHED`.
