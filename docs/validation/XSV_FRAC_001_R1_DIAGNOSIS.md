# XSV-FRAC-001 R1 diagnosis

Authority: R1 commit `80dcf9ef4397bed79f9917d4ed367b8d3d7675d0`,
tree `e5ed6d536382d8be22927dc2eb580a64e2075598`.

## Confirmed defects

- The comparator used the minimum actual/expected series length and sliced
  both inputs before scoring. Missing or extra aggregate and species rows were
  therefore not rejected.
- Completed and terminal legacy pseudo-species rows used the post-step
  `cupSoluteMass` for cumulative mass and extracted fraction. A boundary inside
  a step therefore included solute not yet allocated through that boundary.
- Pure cases adjudicated closure residuals only. Empty or structurally wrong
  output could pass.
- MPI was executed but not numerically compared; mesh and timestep runs were
  executed but observer agreement was not adjudicated at every resolution.

## Confirmed non-equivalence

The inherited production scenario specifies a 3 s pressure ramp from 0 Pa to
900000 Pa gauge at the inlet, with 0 Pa outlet and front pressure. Production
evaluates `rampedPressure(timeValue, targetInletPressure, pressureRampTime)`;
the R1 reduced route applied the final 900000 Pa drop from its first step.

Production retains a remaining-inventory field in every cell. Its explicit
cell source multiplies the local inventory by the local wet mask and
`max(1-C/Csat,0)`, then caps the source by the local inventory divided by the
actual timestep. The R1 reduced route retained one global inventory scalar per
species, removed `k*M*dt`, distributed that source uniformly, and clipped the
post-solve concentration to capacity without returning clipped mass to the
inventory or accounting for it. These are different forcing and
source/capacity algorithms.

## R1 behavior map

| Required behavior | R1 status |
|---|---|
| Pure exact boundary | executed, incompletely adjudicated |
| Pure multiple boundaries | executed, incompletely adjudicated |
| Pure zero-mass step | executed, incompletely adjudicated |
| Terminal partial enabled | executed, incompletely adjudicated |
| Terminal partial disabled | executed, incompletely adjudicated |
| Irregular boundaries | executed, incompletely adjudicated |
| Legacy effective solute | not executed by the adjudicative runner |
| One indexed/legacy equivalence | not executed |
| Identical split species | not executed |
| Distinct species | not executed |
| Three species/structural balance | not executed |
| Zero extraction rate | not executed |
| Zero diffusivity | not executed |
| Positive diffusivity | executed but not separately adjudicated |
| Timestep refinement | executed but not adjudicated |
| Axial-mesh refinement | executed but not adjudicated |
| Deterministic replay | executed and adjudicated |
| Serial/two-rank equivalence | executed but not adjudicated |
| Wetting/reference smoke | not executed |
| Incomplete final boundary | observed but not a distinct adjudicated behavior |

## Observations and inference

The executed production cases reached zero recorded boundary error and at
most approximately `2.71e-20 kg` component residual. Those observations are
promising but incomplete. Because the compared PDE routes were non-equivalent,
the R1 NRMSE and endpoint discrepancies are nonadjudicative and do not support
an inference about the production collector, extraction model, or kinetics.
