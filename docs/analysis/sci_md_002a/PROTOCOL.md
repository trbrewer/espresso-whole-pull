# SCI-MD-002A prospective protocol

Status: `PROSPECTIVE_FROZEN_BEFORE_ADJUDICATIVE_EXECUTION`

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`

Evidence class: `POST_OBSERVATION_MECHANISM_DISCRIMINATION`

## Question and hypotheses

This screen asks whether one reversible finite-rate consolidation state can produce the required pressure-dependent apparent resistance, source pressure ordering, temporal lag, cross-pressure transfer, and a bounded deformation signature. H0–H7 are respectively fixed-hydraulic incapability, quasi-static capability, finite-rate lag, shared cross-pressure transfer, grind transfer where identifiable, deformation distinctiveness, reversible unloading, and bounded-null rejection.

## Model ladder and equations

The fixed control holds geometry, porosity, and permeability fixed. The quasi-static control reuses the accepted WP03 finite-porosity law exactly. The transient state is the load-equivalent consolidation pressure `sigma_c`:

`tau_c d sigma_c/dt = (p_basket - p_outlet) - sigma_c`.

At every time, the accepted depth-resolved WP03 scalar integral is evaluated at `sigma_c`. Its exact bulk height relation gives `epsilon = 1 - H/H0`; local mechanical porosity and permeability retain the accepted solid-volume and permeability laws. Thus pressure/effective stress leads to deformation, porosity, permeability, geometry, resistance, flow, and mass. The state is reversible and no resistance variable evolves independently. `sigma_c=delta_p` is the quasi-static limit; fixed `sigma_c=0` is the frozen limit.

The driving node is basket/puck inlet gauge minus basket-bottom ambient gauge, positive in compression. Prescribed measured basket pressure is primary. The existing lumped machine equations are used unchanged for transfer: `C_u dp_u/dt=Q_supply-Q_puck`, `p_b=p_u-R_line Q_puck`.

## Parameters, cases, and calibration

The canonical JSON protocol freezes all primitives, provenance, numerical controls, bounds, and budgets. `phi0=0.4`, viscosity `0.000315 Pa s`, source geometry, and density `965 kg/m3` follow governed predecessor artifacts. The existing `pc=1,239,155 Pa` is source-derived; other declared mechanical scales and all finite `Theta_c` values are `SYNTHETIC_SCREEN_BOUND`, `NOT_EWP_MEASURED`. One 9-bar hydraulic multiplier is the sole scale anchor; 5 and 11 bar are transfer. Mechanical parameters are shared across pressure groups. Grind transfer is not run unless governed initial structural mapping exists.

The deterministic 580-row matrix contains analytical controls, equilibrium pressure screens, synthetic step/ramp/hold/unload/pulse signatures, all 5/9/11-bar source screens, machine transfer, generic relaxing-resistance controls, and unloading measurement design. No combined mechanism is present. The matrix is canonical in JSON; CSV is a review view.

## Verification and gates

Before source execution: analytical exponential response, exact quasi-static and frozen limits, zero-load behavior, independent equilibrium parity, machine reference, mass/storage balance, state bounds, and selected base/refined-step cases must pass. No clipping is allowed. Gates apply in this order: artifact/numerical validity, resistance sign, pressure ordering, physical bounds, grind direction or explicit non-identifiability, temporal shape, transfer, distinctiveness, then aggregate error. Wrong sign or ordering cannot be rescued by RMSE.

## Stop rules and taxonomy

The machine-readable protocol freezes all pre- and mid-run stop rules. Primary outcomes are the exact SCI-MD-002A survival, not-identified, evidence-limited, single-mechanism-insufficient, and reason-specific rejection labels in the task authority. A source-code defect invalidates the affected execution; it is preserved diagnostic-only and authority is rebuilt from a new commit.

## Claim boundary

`MODEL CLASS: REDUCED_DIAGNOSTIC_TRANSIENT_CONSOLIDATION_MODEL`. Production OpenFOAM physics is unchanged; OpenFOAM and Puckworks execution are prohibited. Physical validation and general whole-solver validation are not established. Wetted-puck modulus is not measured, real-puck poromechanical parameters are not identified, experimental commissioning is not authorized, WP04-TPM-001 is not authorized by this task alone, and combined-mechanism modeling is not authorized.
