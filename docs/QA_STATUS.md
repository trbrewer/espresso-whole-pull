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

## Merged VAL-CASE-001

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

The resulting v2 reduction reproduced the frozen centered correlations,
retained the superseded cosines as supplemental diagnostics, matched a direct
double-precision SVD reference, and changed only prospectively allowed fields.
Two independent analysis-only outputs were byte-identical; all 47 retained
trace identities and metadata were unchanged.

Independent exact-head review approved the corrected result at
`a9b02e48d460cb072529ebcdb3660418c88af9d7`; PR #42 merged it as
`c2c3136e5aae74306f37f8389f945139a9d9009f`. The final disposition remains
validation support only. Physical validation is `NOT_ESTABLISHED`, and
structural identifiability is `NOT_ASSESSED`.

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

## VAL-DATA-001 planning candidate

VAL-DATA-001 adds only an append-only campaign-reference erratum and a
non-commissioning synchronized hydraulic-compaction measurement plan. It
changes no result, code, configuration, framework, standard, dependency, or
physics and performs no scientific or experimental execution.
The bounded planning correction records
`VAL_DATA_001_REVIEW_STATUS: CORRECTED_PENDING_EXACT_HEAD_REVIEW`, makes the
future evidence route prospective, fixes prescribed pressure at the basket-top
node, and adds parameter-role, data-schema, timing, and deformation contracts.
`EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED`, VAL-CASE-002 remains
`NOT_STARTED`, and physical validation remains `NOT_ESTABLISHED`.
The final evidence/schema correction preserves that status while separating
frozen parameter classifications from future roles, closing route/partition/
replicate/block parents and foreign keys, and making the signal table the sole
authority for measured pressure.
The referential-integrity correction additionally verifies exact locked versus
future-template parents, complete signal-sample references, globally unique
resource keys, table-specific nullability, and composite consistency keys.
The template-interface correction further records noncontradictory source-file
nullability, local/catalog campaign namespaces, field-level compatibility
exports, and multi-file processing lineage.
The implementation-contract closure adds exact apparatus/signal/calibration
bindings, a fraction parent and deterministic chemistry presentation,
partition-specific compatibility packages, typed canonical resources with
terminal rights, distinct row-value and file-assembly operations, and exact
synchronized-time-series and terminal-mass selection rules. The deterministic
schema/export audit is required before commissioning readiness; commissioning
is not authorized here.
The final machine-contract audit additionally covers every identifier and
resource field, package/partition identity and summary reconciliation,
registered temperature export, exact and two-sample source provenance,
fraction/chemistry package state, and exactly-one-grid/export-operation
cardinality. No scientific or experimental execution is part of this check.
The final export-contract audit additionally verifies conversion-domain
separation, mutually exclusive processing scopes, record/sample/literal
provenance, package content-mode nullability, byte-reproducible Puckworks
scalars, realized termination-event linkage, edge ordering, filenames, row
keys, row state, and campaign/site/apparatus consistency.
The compatibility-serialization audit additionally verifies closed typed
resource-member mappings, sealed-envelope schemas and non-submission status,
canonical YAML/CSV ordering and field paths, exact `raw`/`processed` mappings,
and nonrecursive file/package manifests. It performs no evidence validation.
The state-and-serialization audit additionally verifies all four package
modes, disjoint full/sealed operation branches, reachable status values,
total row-state mapping, byte-deterministic apparatus calibration YAML, and
exact equality between package-QA and source-manifest identities.

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
