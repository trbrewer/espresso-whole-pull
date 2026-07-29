# Package QA status — current main

## Immutable v0.2.0 release snapshot

The published `v0.2.0` release remains immutable. Its qualification snapshot
is:

- 119/119 Python tests: PASS
- 34/34 active static gates: PASS
- 131/131 source-manifest entries: PASS
- OpenFOAM Foundation 12 build: PASS
- release disposition:
  `SOFTWARE_AND_SOURCE_LINKED_RECONSTRUCTION_RELEASE_PASS`
- physical validation: `NOT_ESTABLISHED`

The historical WP-0.2F role describes release finalization only; it is not the
active repository-governance milestone. Earlier 36-test/32-gate package
construction counts are historical pre-release evidence, not current totals.

## WP-0.3B governed results

The first canonical non-protected reference result remains:

`NONPROTECTED_REFERENCE_VERIFICATION_FAIL`

Its Moroney endpoint refinement metric was dominated by binary64 roundoff.
That result and its original contract were preserved unchanged.

The separately governed A1/P1 correction replaced the controlling observable
with a predeclared full-trajectory norm, completed the source-consistent
asymptotic derivation, corrected observable uncertainty propagation, and
restored the Python 3.8 and CI boundaries. Its sole amended canonical
invocation produced:

`NONPROTECTED_EXTRACTION_REFERENCE_AND_OBSERVABLE_VERIFICATION_PASS_AFTER_GOVERNED_AMENDMENT`

All Moroney, Matias, Liang, and observable subgates passed. No tolerance was
relaxed. OpenFOAM, Puckworks, protected-data, WP02-analyzer, scientific-score,
and source/holdout-fit counts remained zero.

## Current repository checks

- Python tests: 195/195 PASS
- active static gates: 34/34 PASS
- source manifest: recorded in `PACKAGE_QA_STATUS.json` and
  `SOURCE_PACKAGE_MANIFEST.json`
- historical v0.1.4 integrity: PASS
- governing-change boundary: PASS
- release integrity: PASS
- WP-0.3A boundary: PASS
- WP-0.3B/A1/P1 boundary:
  `AMENDED_CANONICAL_RESULT_PRESENT_AND_VERIFIED`
- shell syntax: PASS
- JSON syntax: PASS

WP-0.3B verifies independently re-expressed mathematics, synthetic
identifiability, and measurement bookkeeping. It does not experimentally
validate espresso extraction or WP02 hydraulics, establish parameter
transfer, or introduce runtime extraction physics.

Physical validation remains `NOT_ESTABLISHED`.

## WP-0.3C Stage-0 scaffold

The current governance milestone is WP-0.3C Stage 0. Requirements,
public/private intake templates, and readiness validation are present.
Real-world human and apparatus inputs remain unresolved. Final
preregistration, commissioning, holdout acquisition, model execution, and
scoring are not authorized.

Current Stage-0 checks comprise 195/195 Python tests, 34/34 active static
gates, and 143/143 source-manifest entries.
