# Assumptions, exclusions, and claim ceiling — v0.1.4

## What a passing `./Allrun` establishes

A passing reference workflow establishes that, on the selected OpenFOAM Foundation 12 installation:

- the source package and no-physics-change contracts passed;
- the custom solver compiled from the recorded source;
- the exact executable and Foundation build environment were recorded;
- the heterogeneous layered-pressure fixture passed;
- the reference mesh passed full topology and geometry checks;
- the simulation reached 30 s;
- reconstructed fields, traces, inventories, and conservation gates passed;
- analytical wedge-volume, first-drip, retained-water, and uniform-Darcy checks passed;
- OpenFOAM/B0 parity passed;
- explicit concentration, inventory, retained-water, and cumulative-mass monotonicity gates passed.

It does not freeze the release. The acceptance remains pending standard qualification.

## What a passing standard `./Allverify` additionally establishes

A passing standard qualification establishes that:

- the exact `./Allrun` executable and build inputs were reused unchanged;
- all ten matrix runs passed their own acceptance reports;
- all nine aggregate time-step, mesh, rank, and layered-fixture gates passed;
- the governing source contract remained unchanged after qualification;
- acceptance and run status were finalized with the qualification hash;
- source, build, scientific input, reference artifacts, field contents, and qualification acceptances were cryptographically verified;
- the terminal manifest was generated last and verified read-only.

This supports `FROZEN / QUALIFIED` for the bounded WP-0.1 numerical implementation.

## Calibration status

R0 is an engineering calibration scenario. Saturated permeability was selected to place the simplified 20 g, 58 mm, 9 bar case near an approximately 40 g beverage endpoint at 30 s. That endpoint is not an independent validation target.

The extraction-rate constant, initial extractable fraction, effective diffusivity, and concentration ceiling are engineering assumptions for WP-0.1. The resulting TDS and extraction yield are internally conserved model outputs, not validated chemistry for a named coffee.

## Principal physical assumptions

- 58 mm nominal circular puck represented by a straight-sided 5° axisymmetric wedge;
- 20 g dry dose, porosity 0.40, particle-solid density 1400 kg/m³;
- fixed, uniform 93 °C liquid properties;
- prescribed bed-top pressure ramp to 9 bar gauge in 3 s;
- ambient-gauge basket-bottom outlet;
- sharp-front pore-volume wetting;
- incompressible saturated Darcy flow;
- uniform, static permeability and porosity in R0;
- one effective soluble inventory with first-order release and a capacity ceiling;
- conservative advection–dispersion in the wetted pore volume;
- no gravity in the reference configuration.

## Excluded mechanisms

WP-0.1 excludes:

- resolved air–water two-phase flow;
- capillary-pressure curves and hysteresis;
- dissolved or trapped CO₂;
- transient heat transfer;
- temperature- or concentration-dependent viscosity;
- swelling, poroelastic compaction, damage, and dissolution-driven geometry change;
- mobile/bound fines, capture, release, and clogging;
- spontaneous asymmetric channel formation;
- detailed shower screen, headspace, basket-hole, paper-filter, and machine hydraulics;
- multispecies chemistry and particle-size-resolved intraparticle diffusion;
- taste or sensory prediction.

## Supported claim

After both workflows pass:

> The bounded WP-0.1 R0 model is code-verified, numerically qualified under the declared analytical, reduced-twin, discretization, heterogeneous-pressure, and MPI-decomposition tests, and bound into an acyclic immutable release record.

## Unsupported claims

The release does not establish:

- independent physical validation of first drip, flow, TDS, extraction yield, or fields for a real shot;
- transfer across coffees, grinders, preparations, baskets, filters, or machines;
- validated evolving puck structure, fines, or channeling;
- a universally predictive espresso simulator;
- engineering optimization or sensory accuracy.

The terminal manifest therefore records:

```text
physical_validation_status: NOT_ESTABLISHED
next_scientific_milestone:  WP-0.1R
```
