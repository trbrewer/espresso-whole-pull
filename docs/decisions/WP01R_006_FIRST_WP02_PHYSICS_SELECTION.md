# WP01R-006 first WP-0.2 physics selection

Declaration: `NO_GOVERNING_PHYSICS_CHANGE`.

WP01R-005 reproduced the late hydraulic scale but failed all five protected
temporal flow-shape comparisons: the constant-permeability prediction had zero
protected-window variation. The primary residual is
`STRUCTURAL_MODEL_INADEQUACY`.

## Decision

Select
`WASZKIEWICZ_SATURATED_DISSOLUTION_INDEXED_EFFECTIVE_PERMEABILITY` for
`WP-0.2A_SOURCE_LINKED_SATURATED_HYDRAULIC_EVOLUTION`.

The future branch will optionally apply the locked Waszkiewicz closed-form,
dissolution-indexed effective-permeability multiplier during the saturated
stage. It changes hydraulic resistance only. It will be disabled by default
and must preserve frozen R0 and constant-permeability R1.

The initial driver is the source empirical dissolved-mass sigmoid. That driver
is softly circular because it derives from same-rig TDS and flow. The branch is
a `SOURCE_LINKED_POST_FIT_RECONSTRUCTION`, not independent validation. No
coefficient may be selected from the five protected 9-bar scores.

## Ranked candidates

1. **Waszkiewicz saturated dissolution-indexed effective permeability —
   selected.** It directly introduces the missing time-dependent resistance,
   uses the strongest immediately available locked source evidence, and has a
   short independent verification route.
2. **Machine/headspace and measured basket-pressure coupling — runner-up.**
   It has strong engineering value and pressure-node evidence, but the frozen
   basket-node scale and late magnitude already passed. Select it next if the
   resistance branch leaves a coherent boundary-history residual.
3. **Pressure-only poroelastic compaction.** Relevant to equilibrium pressure
   response, but pressure alone cannot create the persistent trend at nearly
   steady pressure.
4. **Bounded radial/depth heterogeneity.** Valuable for spatial residuals, but
   static heterogeneity does not explain the coherent mean-flow rise.
5. **Improved wetting or gas displacement.** Important during the first
   approximately 5–10 s, outside the protected saturated window.
6. **Thermal transport or concentration-dependent viscosity.** Plausible, but
   transient temperature/property evidence is insufficient and identifiability
   is weak.
7. **Fines migration and clogging.** High engineering value, but presently
   lacks an identifying transport/capture closure.
8. **Channel initiation or damage.** Requires non-axisymmetric or damage
   evidence and carries high implementation risk.
9. **Improved extraction closure.** Needed for chemistry, which was unprotected
   and does not directly resolve the hydraulic residual.
10. **Multispecies chemistry.** Important long-term, but not connected to the
    present protected hydraulic failure.

The JSON companion records evidence, identifiability, rights, numerical and
conservation risk, verification, validation opportunity, engineering value,
cost, claim impact, and disposition for every candidate.

## First implementation boundary

The future branch may independently calculate `qhat`, the porosity factor,
static flow, the empirical dissolved-mass trajectory, dynamic flow, and a
bounded effective-permeability multiplier. It may activate that multiplier
only in the saturated hydraulic branch and must retain the constant branch as
an exact regression control.

It may not initially move the mesh, change bed depth or pore-volume storage,
solve displacement/stress, alter sharp-front wetting, implement machine
compliance, fit a generic `K(t)`, couple to solver-predicted dissolved mass, or
add swelling, fines, channeling, damage, heat, variable viscosity, or new
chemistry.

## Entry gates and claim ceiling

Implementation requires independent closed-form tests, scalar/vector Puckworks
parity without runtime import, disabled-branch recovery, R0 and constant-R1
regression, a uniform-pressure fixture, conservation, boundedness, and a
predeclared non-9-bar no-retuning same-campaign comparison. It must copy no GPL
code or protected article content.

The branch may test whether source-linked saturated evolving resistance
improves the Waszkiewicz reconstruction. It cannot establish independently
validated deformation, transfer, early wetting, channeling, or a universal
permeability law.

Future implementation is governed by [issue #18](https://github.com/trbrewer/espresso-whole-pull/issues/18).
No governing physics is implemented by this decision.
