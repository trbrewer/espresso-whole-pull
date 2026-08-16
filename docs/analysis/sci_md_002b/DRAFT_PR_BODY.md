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

The enduring charter records one-writer, path/process/resource, integration, duplicate-containment, and claim rules. The corrected canonical protocol freezes A0/C0/C1/S1/S2/R1 arms, a deterministic 456-row matrix (hard cap 2,500), an indivisible sorted 435-row adjudicative cohort (432 S1 plus three C0), full governed P5/P9/P11 pressure histories, explicit observed/reference-model field semantics, separate `phi_wet` and `epsilon_b0`, matched base/refined companions, candidate-level gate precedence, analytical controls, physical bounds, dispositions, pilot selection, and external record schema.

The reduced model contains only `pressure -> wetting time -> local swelling age -> particle expansion -> bed geometry/porosity -> permeability/resistance -> axial flow`. It integrates and inverts each full governed pressure history, reimplements the pinned nonlinear Mo spherical diffusion/volume relation and relative Carman-Kozeny effect without extraction, calculates solid/pore/bulk volumes and swelling storage, and emits deterministic temporal records. A volume-consistent accommodation parameter spans fixed height to constant porosity. One 9-bar hydraulic scale is transferred unchanged.

S2 is retained as `SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED`: the available evidence does not uniquely close distributed swelling storage with moving cell volume, and unsupported physics was not invented.

Adjudicative mode and the scientific reducer are fully implemented but require a separately owner-created exact-identity authority token and the exact 435-row cohort. Production code returns mechanical expected bindings only and cannot mint the token, owner role, authorization date, or a valid authority. No token exists in this tranche. The reducer requires all 435 records and 72 complete candidate stems, applies gates per candidate, uses observed-flow targets for aggregate metrics last, and reports exact assumption-dependence support.

## Verification and pilot

Both pre-execution review rounds are addressed. Attempts 1 through 5 remain preserved unchanged. Final attempt 6 completed all eight frozen rows in 17.26 s at 52.9 MiB peak RSS, verified corrected source-field semantics, immutable records and ledger closeout, contained no complete adjudicative candidate triplet, used no owner token, and ran no scientific reducer or ordering calculation. Final focused, repository-wide, manifest, static and CI results are reported at the frozen head. No OpenFOAM, GPU, heavy Puckworks execution, adjudicative source sweep, or scientific disposition is part of this PR.

Claim ceiling: `PHYSICAL_VALIDATION_NOT_ESTABLISHED`; `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; `NO_COMBINED_MECHANISM_AUTHORIZATION`; `NO_SCI_LC_001B_AUTHORIZATION`.

This PR must remain draft. Adjudicative execution, scientific classification, ready-for-review transition and merge require separate owner authorization following independent exact-head pre-execution review.

## Owner-authorized execution result

Following final exact-source owner authorization, the exact 435-row cohort was executed from `ee3a35e0bd8791415056f4537ead5e050052d020` (tree `57a8b96ef4806707553034092430afdc11eadaf8`). The original attempt suffered one isolated malformed-record integrity failure and emitted no scientific disposition. That failed package remains preserved byte-for-byte.

Under separate recovery authorization, a physically separate clone retained all 434 valid records unchanged and regenerated only `S1-SOURCE-P9-M-D1.0-CM0.05-AC0.0-REFINED` through the frozen same-source, same-authority exact-resume path. The replacement scientific result matched independent clean-process simulations byte-for-byte. The recovered 435-record bundle passed the frozen verifier. Two reducer runs were byte-identical and emitted `SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING`: all 72 candidates passed numerical/physical validity and resistance direction, and all 72 robustly failed pressure ordering. No candidate reached temporal or aggregate comparison.

Evidence qualifier: `PACKAGE_INTEGRITY_RECOVERED_BY_SAME_AUTHORITY_SINGLE_RECORD_EXACT_RESUME`.

This rejects only the frozen one-way wetting-age swelling family over the executed bounds. `PHYSICAL_VALIDATION_NOT_ESTABLISHED`; no mechanism is selected; S2 remains design-blocked; porosity-bound robustness is unestablished; no production, OpenFOAM, GPU, SCI-LC, Puckworks, grind-transfer, or combined-mechanism work is authorized or performed.

PR #75 must remain draft and unmerged pending owner scientific and exact-head review. Issue #74 remains open.
