# SCI-MD-006 independent review

## Pre-execution audit

Status: STOP

Reviewed candidate commit: `d2236022fd7cc9e81ee008be7c932ffd32487efc`

Reviewed candidate tree: `f0bbb40a5313d82f97afc3800fea1c95014e09ac`

Review date: 2026-08-25

The adjudicative execution is not authorized. The following pre-execution
defects are material:

1. Pre-fit reduced/full-production parity is absent and ordered incorrectly.
   `execute()` begins the all-data H0/H1 fits and all blocked-fold fits before
   creating `REDUCED_FULL_PARITY.json`; it then records pre-fit parity as
   `NOT_EXECUTED`. There is no frozen target-blind full-production matrix and
   no accepted-harness invocation. The contract requires pre-fit parity to
   pass before any adjudicative fit.
2. The frozen evidence authority is incomplete and the executable loader does
   not consume the frozen Stage-E0-R1 training bundle artifacts. It reconstructs
   observations and inventories from `raw_fractions.csv` and
   `kinetics_fit_params_avg.csv`. The authority manifest omits the frozen
   training contract, fraction table, inventory table, and bundle-manifest
   hashes (including bundle manifest SHA-256
   `112f8b3b943a5cea3399746fde512048e3898f99c8079433dae86bd142db8709`).
   The required exact Puckworks commit/tree are declared correctly as
   `5ce003e751aac516b5de3d9ede4e6910627e2b12` /
   `d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`, but the input closure is not.
3. Identifiability is not implemented to contract. Only a local calculation
   exists; one-dimensional reoptimized profiles are never run, the profile CSV
   is deliberately empty, interval-to-bound truncation is not checked, and
   materially distinct near-optimal modes are not classified or resolved.
4. Numerical qualification is not implemented. The execution path asserts a
   reduced determinism PASS and inherited production qualification without the
   required conservation, boundedness, spatial/time refinement,
   production-reference/fine, serial/parallel, and fraction-boundary evidence.
5. The required automated control surface is substantially incomplete. The 11
   focused unit tests pass, including a synthetic single-experiment prediction
   nesting check, objective/metric arithmetic, optimizer-vector scope, and a
   basic pooled-inventory exclusion check. They do not verify nesting for every
   frozen training condition, whole-experiment/dual-species OOF coverage,
   full-data/fold start isolation from actual execution records, frozen-row
   inventory reproduction, H1 objective nesting for every fit, parity and
   numerical thresholds, historical/solver/Puckworks immutability, Angeloni
   path absence, manifest closure, or report claim-ceiling coverage.
6. The decision implementation does not represent every conjunctive gate
   explicitly. In particular, H1 parity, H1 numerical qualification, and
   evidence-integrity/target-access controls are not independently required by
   the H1 advancement branch; the compact generic `parity`, `numerical`, and
   `governance` booleans cannot preserve the required complete truth table.
7. Exact freeze identity is not closed inside the frozen authority artifacts.
   `AUTHORITY_AND_INPUT_MANIFEST.json` records its candidate commit/tree as the
   pre-freeze starting authority (`434c657...` / `efdf055...`), while the
   pre-execution manifest likewise labels only a before-freeze commit/tree.
   Neither binds the reviewed candidate commit/tree above.

Checks that passed: every file listed by
`PREEXECUTION_FREEZE_MANIFEST.json` matches its declared SHA-256; the production
source hash is
`9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599`;
the listed H0-HIST artifacts have no diff from `origin/main`; no production
solver or historical SCI-MD-004/005 result path is changed by this candidate;
H0 and H1 share one reduced prediction implementation; fitted vector sizes are
exactly two and four; fixed diffusivity and inventory are outside those
vectors; the frozen bounds, log transform, equal-species objective,
concatenated-OOF metric formulas, 15% improvement threshold, 5%
noninferiority threshold, and 0.01 bound-distance criterion are represented.
The exact SCI-MD-006 unit-test command used was
`python3 -m unittest tests.test_sci_md_006 -v` (11 tests, PASS). `pytest` is not
installed in this environment, and full repository QA was not demonstrated by
the candidate evidence reviewed here.

No adjudicative analysis was executed during this review. Angeloni was not
accessed. Puckworks was inspected read-only and was not modified.

## Post-result bounded addendum

Status: NOT_APPLICABLE_BEFORE_EXECUTION

## Corrected pre-execution rereview

SCI_MD_006_CORRECTED_PREEXECUTION_REVIEW_STOP

Scientific freeze F commit: `47994a63dfd1835644d721321e351ae9ae2da12b`

Scientific freeze F tree: `7351e61ff69b62a9d5ecd531d851f952309da6a9`

Binding B commit: `d52376d59599739714f73c45d4316319c4ae2831`

Binding B tree: `ccd43be1b8a8cfb86915b79d8711e1556e03c192`

Review date: 2026-08-25

The prior STOP remains upheld and preserved. The corrected candidate materially
improves the preflight ordering and evidence closure, but adjudicative execution
is still not authorized for these reasons:

1. Binding B is not executable. Its sole added file,
   `validation/sci_md_006/CORRECTED_FREEZE_BINDING.json`, is zero bytes. The
   mandatory `binding()` gate immediately calls `json.loads()` on this empty
   file and therefore cannot read `scientific_freeze_commit`,
   `allowed_delta_paths`, or `scientific_files`. Consequently B does not provide
   the declared nonrecursive F/B execution binding, and no authorized execution
   can pass the freeze/review gate.
2. The post-parity scientific path is not complete. If pre-fit parity ever
   passed, `execute()` would fit and write partial results, then terminate with
   `RuntimeError("POSTFIT_FULL_PRODUCTION_PARITY_REQUIRED_BEFORE_DISPOSITION")`.
   It contains no post-fit reduced/full-production comparison, no complete gate
   population from the fitted evidence, no mechanical eligible/retained/null
   disposition, and no result closure for that path.
3. Numerical qualification remains incomplete relative to the frozen contract.
   The reduced check does not directly inspect dissolved-field nonnegativity,
   per-step source removal versus beginning-step inventory, fraction-boundary
   refinement, production reference/fine behavior, or application-specific
   serial/parallel equivalence. Those required items are text labels such as
   `REQUIRES_POSTFIT_FULL_PARITY` or inherited assertions, not qualification
   evidence or enforced gates.
4. Focused control coverage remains incomplete. Eighteen focused unit tests
   pass, but the required direct tests are still absent for every frozen
   training-condition nesting prediction, whole-experiment dual-species fold
   isolation and exactly-once OOF coverage, actual fold-start provenance,
   every-fit H1 objective nesting, bound/identifiability classification tables,
   parity threshold application to predictions, numerical tolerances,
   immutable authority checks, Angeloni-path absence, result-manifest closure,
   QA-only non-regeneration, and final machine/human claim-ceiling coverage.
   The binding file itself is not parsed or tested.

Verified corrected controls: F has the exact declared commit/tree; B is a
direct child of F with the exact declared commit/tree; all 29 scientific files
listed in F's corrected freeze manifest match their SHA-256 both in F and at B;
the direct frozen Stage-E0-R1 bundle is consumed and its manifest hash is
`112f8b3b943a5cea3399746fde512048e3898f99c8079433dae86bd142db8709`;
the Puckworks authority remains commit
`5ce003e751aac516b5de3d9ede4e6910627e2b12`, tree
`d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`, clean and read-only; the production
source remains SHA-256
`9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599`;
H0-HIST and historical SCI-MD-004/005 result paths are unchanged from
`origin/main`; the corrected preflight evaluates target-blind application
representability before any optimizer call and truthfully records
`CONTRACT_BLOCKED`, `optimizer_call_count: 0`, because the unchanged production
interface lacks the identical prescribed-flow boundary; the loader uses the
frozen fraction-summary and inventory artifacts; explicit decision gate names
now include H0/H1 optimizer, identifiability, bounds, post-fit parity,
numerical, predictive, and integrity controls; two-sided reoptimized profile
code is present.

The focused command `python3 -m unittest tests.test_sci_md_006 -v` passed all 18
tests. No adjudicative `execute` operation was run during this rereview.
Angeloni was not accessed. Puckworks was not modified. No path other than this
continuous independent-review record was modified by the reviewer.

## Final consolidated pre-execution review

SCI_MD_006_FINAL_CONSOLIDATED_PREEXECUTION_REVIEW_STOP

F-final commit: `410319473e97acb871062665ebc8d8f7ecc98297`

F-final tree: `ae1c3890c21409ab17eeafd55cb51925ea714420`

B-final commit: `4ea32581130e348f7dae49a01fc1fa25d6d30103`

B-final tree: `aa574b8eedc0af2421db2a175515fdd28a889ea8`

Review date: 2026-08-25

This final review does not authorize adjudicative execution. The consolidated
candidate repairs the empty binding and executes genuine production cases
before optimization, but the following frozen semantic defects remain:

1. The already frozen real pre-fit parity result is a valid application-contract
   failure, not an application-representability failure. Gauge invariance passes
   and production outlet flow matches each prescribed flow, so the conditional
   Darcy mapping demonstrably represents the fixed-flow application. The parity
   matrix then fails the frozen reduced/full thresholds (for example P01 has
   species prediction NRMSE about 2.563 and endpoint discrepancy about 0.00984;
   P05 also exceeds both thresholds). Nevertheless `blocked_result()` will write
   a final report stating that the unchanged production interface "cannot
   represent" the application. That is contradicted by the frozen gauge and
   production-flow evidence and would create a materially false scientific
   narrative for the expected zero-optimizer terminal result.
2. The nominal parity-success path still does not satisfy the required result
   contract. `FULL_DATA_FITS.json` and `BLOCKED_CV_FITS.json` do not preserve the
   required exact bound-distance classifications; blocked predictions omit
   condition identity, flow/timing, parameter set, source/input hashes, solver
   diagnostics, and conservation diagnostics; no per-fold diagnostic metrics
   are produced; no `SECONDARY_BENCHMARKS.json` is produced; and the success-path
   final report contains only disposition plus claim-ceiling text rather than
   the required model, inventory, blocked-CV, identifiability, parity,
   numerical, sensitivity, and next-work narrative.
3. Application-specific production numerical evidence is not enforced on the
   success path. `postfit_parity()` obtains production application metrics but
   does not retain or gate them. The H0/H1 numerical gates use only
   `numerical.qualify(...)["reduced_pass"]`; production conservation,
   nonnegative state, source-cap behavior, reference/fine behavior, and
   application-specific serial/parallel behavior are therefore not mechanically
   qualified. The generic Stage-C reuse manifest cannot substitute for the
   expressly required application-specific checks where the new conditional
   Darcy case generator and observation mapping are involved.
4. Required direct test and QA evidence remains incomplete. The final focused
   suite has 21 passing tests when the binding check is enabled, but it still
   lacks direct frozen-condition nesting, exactly-once whole-block OOF,
   execution-record start isolation, every-fit nesting inequality, complete
   artifact-schema/manifest closure, numerical/parity failure propagation,
   truthful blocked-report semantics, and claim-ceiling/report-content tests.
   `PACKAGE_QA_STATUS.json` records a generic 975-test repository snapshot but
   contains no SCI-MD-006 full-QA command/result closure for F-final/B-final.

Controls verified as passing: B-final is a direct child of F-final and its JSON
binding is nonempty and parseable; it binds the exact F-final commit/tree,
allowed deltas, immutable authorities, and 35 scientific file hashes; every
bound file matches both the F-final blob and current B-final worktree bytes; the
Stage-E0-R1 bundle manifest and members close; H0-HIST, SCI-MD-004/005 result
paths, and production source are unchanged; Puckworks remains at commit
`5ce003e751aac516b5de3d9ede4e6910627e2b12`, tree
`d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`, clean and read-only; the
conditional-Darcy permeability is fixed from declared flow and gauge rather
than optimized; alternate-gauge evidence passes; the real pre-fit production
matrix ran before any optimizer and truthfully records `pass: false`; the
preflight records `fit_authorized: false` and `optimizer_call_count: 0`; the
success path no longer contains the prior intentional runtime stop; explicit
decision gates include H0/H1 parity, numerical, identifiability, bounds,
optimizer, prediction, and integrity controls.

Focused QA commands used by the reviewer were
`python3 -m unittest tests.test_sci_md_006 -v` (20 pass, one expected binding
test skip) and `SCI_MD_006_REQUIRE_BINDING=1 python3 -m unittest
tests.test_sci_md_006 -v` (21 pass). No adjudicative analysis was executed.
Angeloni was not accessed. Puckworks was not modified. Only this continuous
review record was modified by the reviewer.
