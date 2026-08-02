# VAL-CASE-001 independent-review disposition

## Review object

- Issue: `#41`
- Branch: `validation/val-case-001-hydraulic-identifiability`
- Base: `39c7bf0658c344728258ba1b4f8b935a4e889d7d` / `85711011a96ebaa46a77b5165aec0ab46e676542`
- Protocol: `b5ffc581b79adfc9807face27777a0ae9dc582f8` / `85827508b6b5c23eaca020c8e36ae20b54023aa0`
- Corrected result commit/tree: `cb8118a429d73e5ff17801960f3d41008d8d3d66` / `b616fdb5bef1cbf477d6e8be7f18318194982d68`
- Evidence class: `EXPLORATORY`
- Independent exact-head review: `APPROVED`
- Human-owner disposition: `ACCEPT_CORRECTED_RESULT_AND_AUTHORIZE_EXACT_HEAD_MERGE`

## Evidence to review

- Confirm framework and operating-standard pins and zero diffs.
- Confirm solver-source and baseline-configuration zero diffs from base.
- Recalculate selected physical-unit finite differences, fixed-scale
  normalized sensitivities, SVD spectra, tolerance-dependent ranks, and
  correlations from the reduced bundle and external trace hashes.
- Confirm 47 valid runs, two invalidated completed endpoints, two failed
  pre-launch preparations, and 49 total OpenFOAM launches.
- Assess the bounded correction causal path and unchanged-arithmetic endpoint
  mapping against the operating-standard materiality test.
- Check that measurement precision values are experimental-design targets,
  not validation thresholds or invented uncertainty.
- Confirm no external observation, protected/holdout evidence, fitting,
  retuning, experiment, framework change, or new physics.

## Findings

| Finding | Materiality basis | Classification | Action |
|---|---|---|---|
| `FROZEN_PROTOCOL_CENTERED_CORRELATION_REPLACED_BY_UNCENTERED_COSINE` | Correlation and derived near-collinearity interpretation changed | `RESULT_AFFECTING_METHOD_OR_DATA_DEFECT` | `CORRECTED_PENDING_EXACT_HEAD_INDEPENDENT_REVIEW` |

No more than one further correction cycle is permitted unless an unresolved
material blocker or a newly introduced material defect is demonstrated. Any
general reusable improvement is `VALIDATION_INFRASTRUCTURE_BACKLOG` and is out
of scope for this case.

## Required disposition

```text
SCIENTIFIC_RESULT_DISPOSITION:
  VALIDATION_SUPPORT_ONLY

VALIDATION_FRAMEWORK_DISPOSITION:
  PINNED_FRAMEWORK_USED_UNCHANGED

CLAIM_CEILING:
  VALIDATION_SUPPORT_ONLY_PHYSICAL_VALIDATION_NOT_ESTABLISHED
```

`CORRECTION_STATUS: CORRECTED_PENDING_EXACT_HEAD_INDEPENDENT_REVIEW`

`HUMAN_OWNER_DISPOSITION: UNRESOLVED_PENDING_CORRECTED_EXACT_HEAD_REVIEW`

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`

## Final exact-head and merge disposition

```text
INDEPENDENT_EXACT_HEAD_REVIEW:
  APPROVED
HUMAN_OWNER_DISPOSITION:
  ACCEPT_CORRECTED_RESULT_AND_AUTHORIZE_EXACT_HEAD_MERGE
CORRECTION_STATUS:
  CORRECTED_APPROVED_AND_MERGED_EXACT_HEAD
APPROVED_HEAD:
  a9b02e48d460cb072529ebcdb3660418c88af9d7
APPROVED_TREE:
  2c42f23215cd7f07a7b693ac22e8399a537c1bbd
MERGE_COMMIT:
  c2c3136e5aae74306f37f8389f945139a9d9009f
MERGE_TREE:
  2c42f23215cd7f07a7b693ac22e8399a537c1bbd
ISSUE_41:
  CLOSED
PR_42:
  MERGED
SCIENTIFIC_RESULT_DISPOSITION:
  VALIDATION_SUPPORT_SENSITIVITY_AND_IDENTIFIABILITY_SCREENING
VALIDATION_FRAMEWORK_DISPOSITION:
  PINNED_FRAMEWORK_USED_UNCHANGED
CLAIM_CEILING:
  VALIDATION_SUPPORT_ONLY_PHYSICAL_VALIDATION_NOT_ESTABLISHED
PHYSICAL_VALIDATION:
  NOT_ESTABLISHED
STRUCTURAL_IDENTIFIABILITY:
  NOT_ASSESSED
```

The approved review and merge status do not alter the finding or correction
history above, the corrected result, or any scientific claim boundary.
