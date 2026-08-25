# SCI-MD-004 Stage E1 conditional Darcy reconciliation

Authorization: `SCI-MD-004-STAGE-E1-HYDRAULIC-RECONCILIATION-OWNER-AUTHORIZATION-CONDITIONAL-EFFECTIVE-DARCY-PERMEABILITY-FREEZE-AND-RESUMED-SINGLE-PROTECTED-HOLDOUT-EXECUTION-2026-08-25`

Profile: `EWP_SCI_MD_004_STAGE_E1_G1_HYDRAULIC_ADAPTER_TO_G3_HOLDOUT_V1`

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`.

The merged blocked Stage E1 result at commit `2d719ca226a124fb90d2c5ffff3a995d4a652c4f`
is preserved without relabeling or overwrite. This additive G1 freeze represents
the nominal 40 g yield over the reported duration with the existing
pressure-driven, uniform-Darcy production interface. Each of the 33 non-variety
apparatus conditions has one effective permeability calculated from reported
gauge pressure, duration and geometry plus the accepted Pannusch water
viscosity and density closures. The value is shared by the Arabica/Robusta
pair, H0/H1, and reference/fine cases.

The protocol is `POST_WETTING_SATURATED_CONDITIONAL_EXTRACTION`: the bed starts
fully saturated, the pressure ramp is zero, outlet gauge pressure is zero,
gravity is disabled, and the nominal 0.040 kg beverage mass is diagnostic only.
The grind porosities are O = 0.305, C = 0.330 and F = 0.276. Required particle
density is deterministic geometric bookkeeping, not a measurement.

All 66 zero-inventory production runs pass the analytical-flow tolerance of
`1e-8`, the 0.1 g beverage-mass tolerance, the 0.25% reference/fine tolerance,
finite/nonnegative hydraulic-state checks, full-saturation requirement and
liquid balance. All 264 H0/H1 reference/fine scenarios materialize twice with
identical deterministic executable-input hashes. No species prediction and no
semantic protected-target access occurred during G1.

The inferred permeabilities are `NONPORTABLE_CONDITIONAL_EFFECTIVE_PERMEABILITY`
nuisance inputs. They are not measured or physically validated permeability,
not a grinder closure, not a pressure law, and not transferable.

The generic indexed species solver is software and numerically verified. The
caffeine and trigonelline parameters are training-data estimates, not universal
physical constants. The conditional Angeloni comparison cannot validate machine
hydraulics, permeability, internal transient fields, thermal chemistry, lipid
transport, taste, or unrestricted transfer. General physical validation remains
`NOT_ESTABLISHED`.
