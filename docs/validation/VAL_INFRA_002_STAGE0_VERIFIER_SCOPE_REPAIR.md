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

## Exact-head review correction

The first PR head, `af021af6aa5a04f361d5f5050f6733accf2e0dfa`,
compared protected path names and followed-target bytes. It did not distinguish
a regular file from a symbolic link to an identical external copy and did not
require the pinned Stage-0 merge to be an ancestor of candidate `HEAD`. That
head was therefore not fully fail-closed for Git object replacement.

The corrected verifier reads recursive NUL-delimited entries from the pinned
and candidate Git trees. Each protected entry binds path, Git mode, Git object
type, object identity, and content SHA-256. It separately requires the pinned
merge to be an ancestor of `HEAD` and rejects any protected staged, unstaged,
or untracked worktree state. `lstat()` checks every protected path component,
so neither a protected file nor an intermediate protected directory may be a
symbolic link. The protected scope remains 16 paths with canonical path
aggregate
`8f21a12285d93cc5ee24730c892d6da6db7cdad9948b2c76dd60bc0c1e5dce7c`.

## Boundaries

No workflow, branch protection, validation framework, operating standard,
solver, scientific configuration, result, evidence, Puckworks lock, or claim
ceiling changed. No OpenFOAM, scientific scoring, fitting, retuning, protected
access, holdout access, or experimental work occurred.
