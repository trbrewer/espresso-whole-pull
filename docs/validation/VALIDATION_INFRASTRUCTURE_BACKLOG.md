# Validation Infrastructure Backlog

This backlog holds nonmaterial improvements to reusable validation tooling and
administrative reporting. Items here do not invalidate a scientific result and
must not trigger another correction cycle for a completed `VAL-CASE` unless a
material bypass is independently demonstrated.

## VAL-INFRA candidates

### VAL-INFRA-002 — Scope the WP-0.3C Stage-0 verifier to frozen artifacts

**Source:** Independent review of VAL-CASE-001 / PR #42

**Classification:** `VALIDATION_INFRASTRUCTURE_BACKLOG`

The historical Stage-0 verifier required the entire repository diff from the
old WP-0.3C baseline to equal a permanently growing path allowlist. Unrelated,
authorized later work therefore failed the verifier even when the Stage-0
contract, artifacts, and semantic boundaries were unchanged. This limitation
did not affect VAL-CASE-001 arithmetic, evidence, execution, admissibility,
reproducibility, or claim ceiling.

VAL-INFRA-002 repairs the boundary by pinning the historical Stage-0 commit,
tree, and original permitted-path contract, deriving the protected Stage-0
artifact scope from that contract, and checking those artifacts directly.
Unrelated later paths are outside this historical boundary and need no
enumeration. Mutation, deletion, addition, replacement, or rename inside the
protected scope remains fail-closed. Governed scientific execution and scoring
are prohibited.

### VAL-INFRA-001 — Unify schema-document count semantics

**Source:** Final proportional adjudication of PR #38 / VAL-001

**Classification:** `VALIDATION_INFRASTRUCTURE_BACKLOG`

VAL-001 had 31 checked-in governed schema documents and 31 assignments to the
schema-document family, while one taxonomy report counted 25 records whose
record-class label was exactly `SCHEMA`. Define a single prospective
schema-document counting rule and generate all reporting fields from it.

This is an administrative reporting inconsistency. It did not affect schema
selection or validation, semantic enforcement, evidence admissibility,
execution authority, scientific interpretation, or the VAL-001 claim ceiling.

## Entry format

Future entries should state:

- source case or review;
- observed limitation;
- why it is nonmaterial to that case;
- proposed synthetic fixture or documentation change;
- explicit prohibition on governed scientific scoring.
