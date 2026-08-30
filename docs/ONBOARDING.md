# Onboarding

Read `README.md`, `docs/PROJECT_STATE.md`, `docs/CLAIM_CEILING.md`, the
[current scientific execution plan](strategy/DATA_FIRST_SCIENTIFIC_DEVELOPMENT_PLAN.md),
[controlling strategy](strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md),
the [concise roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md),
the [post-WP03 validation plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md),
[Puckworks integration](PUCKWORKS_INTEGRATION.md), and `CONTRIBUTING.md`.
Before substantive science or new measurement, also read
`strategy/AVAILABLE_DATA_FIRST_POLICY.md`,
`../provenance/AVAILABLE_DATA_AUTHORITY.json`, and the task's completed data
preflight. External data unavailable in the checkout are not absent.

For validation work, also read the
[Validation Operating Standard v1](validation/VALIDATION_OPERATING_STANDARD_V1.md)
and use its
[review checklist](validation/VALIDATION_REVIEW_CHECKLIST_V1.md). New cases may
start from the concise templates in `docs/validation/templates/`; reusable
nonmaterial improvements belong in the
[validation infrastructure backlog](validation/VALIDATION_INFRASTRUCTURE_BACKLOG.md).

## Governed issues and pull requests

Choose the **Evidence or governance task** issue form for no-physics evidence
inventories, dependency reviews, source dossiers, calibration or validation
contracts, rights reviews, and scientific decision records. Choose the
**Scientific change proposal** form for scenario, numerical-method, or
governing-physics changes.

One governed issue should normally lead to one principal pull request. Do not
duplicate the same material across issue-form fields. Every pull request must
identify its issue and select exactly one change declaration.

Generated OpenFOAM fields, meshes, processor directories, executables, logs,
and uncleaned runs remain outside Git. R1 implementation may not begin before
its evidence and protected-comparison contracts are accepted.

## Inexpensive checks

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_source_manifest.py --root .
PYTHONDONTWRITEBYTECODE=1 python3 scripts/static_validate.py --root .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_v0_1_4_baseline_integrity.py --root . --output /tmp/v0-1-4-baseline.json
bash -n Allrun Allverify Allclean Allwmake scripts/*.sh scripts/lib/*.sh
```

These checks do not compile or run OpenFOAM and do not establish physical validation.

The v0.1.4 baseline-integrity check protects immutable historical evidence.
Current active-boundary and release-integrity checks are the commands invoked
by `.github/workflows/static-validation.yml`, selected according to the active
task's change declaration. `scripts/verify_no_physics_change.py` remains the
historical v0.1.4-versus-v0.1.3 release verifier; it is not a global
current-main no-change assertion after authorized solver development. Root
`Allverify` is an archival/release qualification workflow, not a routine
current-development acceptance command.

Foundation OpenFOAM 12 is the current target. Full runs are manual and release-gated. Do not run `Allrun`, `Allverify`, or `Allclean` as part of routine documentation or CI work.

Run `tools/checkout_puckworks.sh <destination>` only when network dependency checkout is intended. The script verifies the exact locked commit. Puckworks is not a submodule.
