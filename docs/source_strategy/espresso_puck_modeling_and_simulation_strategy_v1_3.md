# Espresso Puck Modeling and Simulation Strategy

**Strategy version:** 1.3  
**Date:** 29 July 2026  
**Status:** Controlling strategy after merged WP02-001; WP-0.2F release
finalization is immediate  
**Supersedes:** Strategy v1.2 without rewriting it  
**Current package line:** 0.2.0-dev.1 pending v0.2.0 finalization  
**Physical validation:** `NOT_ESTABLISHED`

## Completed foundation

The immutable `v0.1.4-public.1` package remains the sanitized public R0
baseline. Its bounded R0 configuration is `FROZEN / QUALIFIED` for numerical
and provenance purposes; it did not introduce governing physics relative to
its qualified predecessor and it did not establish physical validation.

WP01R-001 through WP01R-006 completed dependency review, source dossier,
calibration and comparison contracting, deterministic R1 construction,
governed execution, residual classification, and selection of the first
WP-0.2 mechanism. The reviewed Puckworks dependency remains fixed at commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`. A fresh moving-upstream
alignment review is required before adopting any newer Puckworks identity.

## WP02-001 outcome

The constant-permeability R1 run reproduced its late hydraulic scale but
predicted zero protected-window variation. The protected temporal-flow-shape
gate failed, identifying `STRUCTURAL_MODEL_INADEQUACY` rather than a numerical,
conservation, or calibration failure.

WP01R-006 therefore selected the Waszkiewicz saturated
dissolution-indexed effective-permeability closure. WP02-001 implemented it as
one optional, disabled-by-default saturated resistance branch. It changes
effective permeability only; it does not move the mesh, change pore volume,
alter wetting, or solve full deformation.

Independent closed-form checks, locked-Puckworks parity, the deterministic
uniform-pressure fixture, the disabled R0 regression, and the disabled
constant-R1 regression passed. The governed 9-bar source-linked reconstruction
passed all frozen aggregate gates. The predeclared 8-bar no-retuning
same-campaign comparison also passed. The 8-bar outcome is not independent
validation.

Both completed traces ended at `102.999999999997 s`, representation-equivalent
to the governed `103.0 s` endpoint. A committed pre-score correction selected
the existing final sample only at source index 999 under an ULP-scale bound.
It changed no trace, mapping, selector, gate, or score formula. The first
analyzer attempt remains a pre-score software failure; exactly one
score-bearing analysis followed.

## Claim boundary

WP-0.2A establishes a source-linked multi-pressure reconstruction result for
one same-campaign closure. It does not establish full poroelastic deformation,
transfer across coffees, grinders, baskets, machines, or rigs, early wetting,
channeling, fines, chemistry, taste, or a universal permeability law.
Physical validation remains `NOT_ESTABLISHED`.

## Immediate program sequence

1. Complete WP-0.2F as a no-governing-physics v0.2.0 release-finalization task.
2. Preserve the scientific result and executed solver identity unchanged.
3. Package and software-qualify the source release with an independently
   recorded release executable.
4. Begin no new mechanism until independent holdout evidence and
   multi-mechanism discrimination are contracted.
5. Use residual evidence—not implementation convenience—to select later
   machine/headspace coupling, fuller poroelasticity, or another mechanism.

Development remains progressive and one mechanism at a time. Source linkage
and same-campaign success motivate independent holdout validation; they do not
replace it.
