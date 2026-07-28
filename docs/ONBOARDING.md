# Onboarding

Read `README.md`, `docs/PROJECT_STATE.md`, `docs/CLAIM_CEILING.md`, the controlling strategy, and `CONTRIBUTING.md`.

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
