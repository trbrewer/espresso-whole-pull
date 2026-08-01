# VAL-001 PR #38 correction boundary

Human-owner direction dated 31 July 2026 authorizes an additive correction
cycle on the existing issue #37, branch, and PR #38. Existing commits remain
unchanged in history.

The original result at
`validation/val001/results/VAL_001_FIRST_COMPONENT_COMPARISONS.json` is
retained byte-for-byte for audit. Its arithmetic is
`VERIFIED_CORRECT_FOR_TEN_IN_DOMAIN_ROWS`, while its prospective-governance
status is `INVALIDATED` because the original authority record was incomplete
and real-data invocation accounting was ambiguous. It is
`SUPERSEDED_FOR_GOVERNANCE`, `RETAINED_FOR_AUDIT`, `NOT_BLIND`,
`NOT_INDEPENDENT`, and not physical validation or a current-head solver
comparison.

At least three pre-correction real-data computations are established: the
retained output-producing execution and CI test executions at results commit
`5f648e4e80579caf83487d2953db3fbc0d4e02eb` and candidate commit
`0fb619884d1854a57eff30426ed93a16f97cb3c3`. The exact historical local count
is not reconstructable from committed evidence. No corrected score has been
computed at this boundary.

The correction will deepen and enforce schemas, implement fail-closed
semantics, replace real-data unit tests with synthetic fixtures, complete the
authorized historical-adapter and planning scope, freeze corrected methods,
bind a separate authority record, build and activate the unchanged solver,
execute the bounded three-case matrix, and perform exactly one corrected
real-data comparison invocation.

Physical validation remains `NOT_ESTABLISHED`. Protected or holdout scoring,
experimental commissioning, and new governing physics remain unauthorized.

## Corrected execution outcome

The three prospectively declared current-head OpenFOAM cases completed, but
the one authorized corrected real-data invocation failed after computing
metrics in memory and before writing a result. The frozen runner used the JSON
literal `false` in Python source, causing the retained `NameError` recorded in
`VAL_001_CORRECTED_EXECUTION_FAILURE.json`.

The partial score exposure counts as one corrected real-data comparison
invocation. It produced zero governed result bundles and is invalidated. The
prospective rule prohibits a silent retry, so this cycle stops with
`VAL001_PR38_CORRECTION_EXECUTION_OR_VALIDATION_FAILED`; PR #38 is not ready
for re-adjudication.
