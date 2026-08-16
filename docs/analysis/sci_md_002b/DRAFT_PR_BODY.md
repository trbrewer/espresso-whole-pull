## Purpose

Freeze the prospective SCI-MD-002B reduced pressure-coupled wetting-age swelling signature screen. The question is whether pressure-dependent Foster wetting time plus pressure-shared Mo-style swelling can produce sufficient additional high-pressure axial resistance for `Q5 > Q9 > Q11`.

Refs #74.

## Scientific and lane boundary

- `NO_GOVERNING_PHYSICS_CHANGE`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`.
- Follows SCI-MD-002A's bounded rejection of its frozen single-state transient-poromechanics family.
- Independent of SCI-LC-001A-C3: no SCI-LC code, result, candidate, calibration, artifact, process, or path is consumed or modified.
- Task-owned files are only `docs/analysis/sci_md_002b/**`, `validation/cases/sci_md_002b/**`, `scripts/sci_md_002b.py`, and `tests/test_sci_md_002b.py`.
- Production `solver/**`, `config/**`, production `cases/**`, and all SCI-LC paths are unchanged.
- Puckworks is read-only at EWP lock `fc61c4670ec7bf801e40bb391aab16048b8da26b`.

## Package

The enduring charter records one-writer, path/process/resource, integration, duplicate-containment, and claim rules. The canonical protocol freezes A0/C0/C1/S1/S2/R1 arms, a deterministic 243-row matrix (hard cap 2,500), pressure-shared candidate sets, analytical controls, physical bounds, gate precedence, numerical-uncertainty ordering rules, dispositions, pilot selection, and external record schema.

The reduced model contains only `pressure -> wetting time -> local swelling age -> particle expansion -> bed geometry/porosity -> permeability/resistance -> axial flow`. It reimplements the pinned nonlinear Mo spherical diffusion/volume relation and relative Carman-Kozeny effect without extraction. A volume-consistent accommodation parameter spans fixed height to constant porosity. One 9-bar hydraulic scale is transferred unchanged.

S2 is retained as `SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED`: the available evidence does not uniquely close distributed swelling storage with moving cell volume, and unsupported physics was not invented.

Adjudicative mode requires a separately owner-created exact-identity authority token and currently fails closed. The frozen eight-row pilot contains no adjudicative source row, no 5/9/11 source triplet, and cannot run scientific reduction.

## Verification and pilot

Focused controls currently pass 23/23; deterministic generator/reference/boundary and full repository checks plus the non-adjudicative pilot will be reported in a subsequent bounded commit. No OpenFOAM, GPU, heavy Puckworks execution, adjudicative source sweep, or scientific disposition is part of this PR.

Claim ceiling: `PHYSICAL_VALIDATION_NOT_ESTABLISHED`; `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; `NO_COMBINED_MECHANISM_AUTHORIZATION`; `NO_SCI_LC_001B_AUTHORIZATION`.

This PR must remain draft. Adjudicative execution, scientific classification, ready-for-review transition and merge require separate owner authorization following independent exact-head pre-execution review.
