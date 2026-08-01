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

- Python and active-static-gate totals for the open candidate are generated in
  `PACKAGE_QA_STATUS.json`; the merged WP03-001 baseline remains 230 tests.
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

## VAL-CASE-001 candidate

VAL-CASE-001 executed the unchanged merged solver for 47 valid cases and two
invalidated completed endpoints. The exact-repeat feature vector was
byte-for-byte numerically identical. Case-specific tests cover deterministic
input derivation, bounds, finite differences, normalization, Jacobians, SVD,
serialization, run accounting, immutable framework/baseline paths, and the
claim ceiling. Current candidate counts and source identities are recorded in
`PACKAGE_QA_STATUS.json` and `SOURCE_PACKAGE_MANIFEST.json`. Physical
validation remains `NOT_ESTABLISHED`.

Independent review froze a bounded correction of the primary correlation
method before retained-trace access. The freeze changes no result bundle,
protocol, reducer, execution record, report, trace, or scientific input and
authorizes zero new OpenFOAM launches.

## Merged VAL-INFRA-002 repair

VAL-INFRA-002 adds deterministic frozen-scope tests for authentic Stage-0 and
current repository states, unrelated future paths, and protected-scope
mutation, deletion, addition, replacement, rename, contract, identity, and
semantic failures. It performs no OpenFOAM or scientific execution.
The exact-head correction additionally covers file and directory symbolic
links, gitlinks, executable-mode changes, tracked deletion with untracked
replacement, and an equal-tree non-ancestor candidate using real temporary Git
repositories.

WP-0.3B verifies independently re-expressed mathematics, synthetic
identifiability, and measurement bookkeeping. It does not experimentally
validate espresso extraction or WP02 hydraulics, establish parameter
transfer, or introduce runtime extraction physics.

Physical validation remains `NOT_ESTABLISHED`.

## WP-0.3C Stage-0 scaffold

WP-0.3C Stage 0 remains a completed, frozen scaffold. Requirements,
public/private intake templates, and readiness validation are present.
Real-world human and apparatus inputs remain unresolved. Final
preregistration, commissioning, holdout acquisition, model execution, and
scoring are not authorized.

Its historical completion counts are retained in its result records.

## Post-WP03-001 phase

WP03-001 is merged and numerically verified for its tested cases. The active
program phase is source-specific validation and mechanism discrimination.
This documentation alignment performs no model or validation execution and
authorizes no experiment, protected scoring or holdout opening.

Current test and source-manifest identities are generated in
`PACKAGE_QA_STATUS.json` and `SOURCE_PACKAGE_MANIFEST.json`. Physical
validation remains `NOT_ESTABLISHED`.

## Open VAL-001 second correction

The original result remains audit-retained with prospective governance
invalidated. The first corrected invocation remains failed and invalidated
after score exposure. A separately authorized one-token Python Boolean repair
passed synthetic end-to-end testing; one replacement invocation then retained
the canonical V2 bundle with SHA-256
`7968e3b99045da9500442932c536bf920d559ebe660d2bad01f954f36b3f75b5`.
The second cycle performed zero new OpenFOAM builds and executions, and tests
perform zero real-data comparison invocations. The result is post-observation,
not blind, not independent, and not physical validation. PR #38 remains open
pending independent re-adjudication.

## VAL-001 post-result framework hardening

The candidate now has canonical consumed-authority enforcement, deep retained
V2 and invocation-ledger schemas, a durable append-only event journal,
synthetic transaction/concurrency tests, and a versioned raw-string selected-
row identity. The production runner accepts no alternate governed identities.
This cycle performed zero governed comparisons and zero OpenFOAM work.

The deep-schema completion cycle provides exhaustive governed-record inventory coverage, removes prefix
legacy catch-alls, validates immutable records by exact hash plus nested
structure signature, and verifies byte-identical journal-to-summary
regeneration. The current normative remediation directly enumerates 105
records through 68 referenced schema families; sidecar-primary, generic
catch-all, and enumeration-exclusion counts are zero. All mutation
testing remains synthetic; V2 and the invocation journal are unchanged.
## VAL-001 schema provenance and semantic enforcement

- Governed records: 105/105 directly enumerated and validated.
- Normative contracts/schema families: 68/68 current and referenced; zero
  inferred, copied-inferred, signature-selected, filename-selected, or unused.
- Mutation inventory: 340 declared and 340 executed; zero missing, unexpected,
  duplicate, or placeholder cases.
- Schema documents: recursive AST and keyword-value validation enabled.
- Semantic escalation: historical, campaign, identifiability, execution,
  fitting, configuration, claim, dependency, and consumed-state boundaries
  fail closed under synthetic mutation.
- External artifacts: seven prior OpenFOAM files restored read-only and
  hash-verified; zero builds and zero executions in this cycle.
- Physical validation: not established.
VAL-001 explicit-semantics QA verifies zero instance-derived governing schemas,
complete executable-profile dispatch, and externally pinned candidate roots.
All cases are synthetic; governed comparison and OpenFOAM execution counts are
zero for this correction.
