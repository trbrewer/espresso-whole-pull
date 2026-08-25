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
