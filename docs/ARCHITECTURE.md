# Architecture

## Indexed passive species (SCI-MD-004 Stage C)

`espressoWholePullFoam` defaults to the unchanged legacy single-effective-
solute route when `soluteTransportModel` is absent. The additive
`indexedPassiveSpecies` route reads a deterministic species order, owns one
field triplet and cumulative mass state per species, advances every species
through one generic transport kernel, and refreshes the legacy fields as sums.
Species state is downstream of hydraulics and cannot feed pressure, saturation,
wetting, material properties, mechanics, machine coupling, or timestep choice.
Indexed output is long-form and separate from the unchanged legacy trace.

The project has four connected layers:

1. `espressoWholePullFoam`, the Foundation 12 whole-puck solver.
2. Deterministic case preparation, analytical checks, and reduced B0 verification.
3. Source, numerical-qualification, provenance, and claim-control tooling.
4. Puckworks as the external evidence/model/data plane.

The bounded R0 state covers pressure, wetting state, Darcy flux, dissolved concentration, remaining extractable inventory, porosity, permeability, retained inventories, and cup accumulation. Porosity and permeability are static for R0.

Generated meshes, fields, qualification runs, processor directories, executables, and full logs remain outside Git. Public Git retains source, templates, compact summaries, and cryptographic identities.

Future mechanisms must be additive, separately switchable, separately verified, and justified by a named residual or engineering decision.
