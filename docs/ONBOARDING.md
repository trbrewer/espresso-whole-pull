# Onboarding

Read `README.md`, `docs/PROJECT_STATE.md`, `docs/CLAIM_CEILING.md`, the controlling strategy, and `CONTRIBUTING.md`.

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
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_no_physics_change.py --root . --output /tmp/no-physics.json
bash -n Allrun Allverify Allclean Allwmake scripts/*.sh scripts/lib/*.sh
```

These checks do not compile or run OpenFOAM and do not establish physical validation.

Foundation OpenFOAM 12 is the current target. Full runs are manual and release-gated. Do not run `Allrun`, `Allverify`, or `Allclean` as part of routine documentation or CI work.

Run `tools/checkout_puckworks.sh <destination>` only when network dependency checkout is intended. The script verifies the exact locked commit. Puckworks is not a submodule.
