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

Independent exact-head review rejected the candidate. The positive-diffusivity
development sequence exposed 5.998% reference--fine sensitivity in the
inherited inlet boundary-gradient loss, above the frozen 0.75% gate. Replacing
that case with a zero-diffusivity limit does not qualify mesh sensitivity of
the implemented advection-diffusion capability. The reviewer also found that
the additive runner did not completely assert required aggregate
superposition, total conservation and bounds, deterministic final fields,
all-species serial/MPI equivalence, event-time convergence, direct hydraulic
field identity, and every parser rejection category. The performance sequence
was grouped rather than interleaved. The implementation is therefore a failed
candidate and must not be merged.

Angeloni remains `PROTECTED_EXTERNAL_NO_RETUNING_ENDPOINT_HOLDOUT` with
`PREEXISTING_EXPOSURE = TRUE`. No target values were accessed, no prediction or
score was generated, and no species parameter was fitted. All Stage C values
are manufactured software-verification values. Physical validation remains
`NOT_ESTABLISHED`.
