# SCI-MD-002B: reduced pressure-coupled wetting-age swelling signature screen

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`

Task declaration: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`

This task asks whether pressure-dependent Foster wetting times, coupled to the bounded Mo particle-swelling law with pressure-shared parameters, can create sufficient additional high-pressure axial resistance to reproduce the retained source ordering `Q5 > Q9 > Q11`.

SCI-MD-002A rejected its frozen single-state reversible transient-poromechanics family for wrong pressure ordering. SCI-MD-002B is a complementary but operationally and scientifically independent secondary lane alongside SCI-LC-001A-C3. It consumes no SCI-LC result, code, candidate, calibration, or output.

Scope is limited to a task-local one-dimensional reduced diagnostic, prospective protocol and deterministic matrix, analytical/reference controls, executor/reducer, tests, immutable external pilot records, and a small non-adjudicative pilot. Non-goals include production OpenFOAM changes or runs, Puckworks modification, fines, poromechanics, lateral localization, combined mechanisms, physical validation, and adjudicative 5/9/11-bar execution.

Owned paths are `docs/analysis/sci_md_002b/**`, `validation/cases/sci_md_002b/**`, `scripts/sci_md_002b.py`, `tests/test_sci_md_002b.py`, and `SCI_MD_002B_EXTERNAL_BUNDLE`. SCI-LC paths, production `solver/**`, `config/**`, production `cases/**`, common utilities, and Puckworks are prohibited/read-only as declared in the lane charter.

Puckworks is a read-only scientific reference locked by EWP at `fc61c4670ec7bf801e40bb391aab16048b8da26b` (tree `1d553e44ee2f7480a5df521560801b478618cc84`).

Claim ceiling: `PHYSICAL_VALIDATION_NOT_ESTABLISHED`; `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; `NO_COMBINED_MECHANISM_AUTHORIZATION`; `NO_SCI_LC_001B_AUTHORIZATION`.

Current authority permits implementation, controls, tests, and a non-adjudicative pilot only. Adjudicative execution and scientific classification require a separately supplied owner authority bound to the exact reviewed head and artifacts. Independent exact-head pre-execution review is mandatory.

Acceptance for this tranche is a deterministic, verified package; no complete pilot source triplet; a draft unmerged PR; clean lane/process boundaries; and terminal state `SCI_MD_002B_PREEXECUTION_PACKAGE_COMPLETE_PENDING_INDEPENDENT_REVIEW` with `SCI_MD_002B_ADJUDICATIVE_EXECUTION_NOT_AUTHORIZED`.
