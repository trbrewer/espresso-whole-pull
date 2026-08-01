# VAL-INFRA-002 WP-0.3C Stage-0 verifier scope repair

**Issue:** #43

**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`

## Defect

The prior verifier compared every path changed since the pre-Stage-0 baseline
with a manually extended `EXPECTED_PATHS` set. Every later work package
therefore had to add its unrelated paths to a historical verifier. PR #42
exposed the limitation without affecting its scientific arithmetic, evidence,
execution, admissibility, reproducibility, or claim ceiling.

## Repaired boundary

The verifier now pins the merged Stage-0 commit
`f43bf2166f60f984e4ca5ca7f30c791a68c6259e`, tree
`6b812f61bb4e0630d80dc0fb4a0922d63554a704`, and original contract SHA-256
`88aee87865e5ea1cd9542432bad36809773cc62c8b24a3be30e043296ef3c613`.
It derives the protected Stage-0 artifact scope from that historical
contract's `permitted_changed_paths` and the Stage-0 campaign, tooling,
contract, and public input-guide namespaces. Exact path membership and bytes
are compared with the pinned historical tree.

Unrelated present or future work-package paths are not inputs to this
historical boundary. Within the protected scope, mutation, deletion, addition,
replacement, and rename remain failures. Existing canonical aggregate,
registry, template, privacy, unresolved-input, execution, holdout, dependency,
scientific-identity, and claim-ceiling checks remain active.

## Boundaries

No workflow, branch protection, validation framework, operating standard,
solver, scientific configuration, result, evidence, Puckworks lock, or claim
ceiling changed. No OpenFOAM, scientific scoring, fitting, retuning, protected
access, holdout access, or experimental work occurred.
