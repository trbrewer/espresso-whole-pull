# VAL-CASE-001 independent-review disposition

## Review object

- Issue: `#41`
- Branch: `validation/val-case-001-hydraulic-identifiability`
- Base: `39c7bf0658c344728258ba1b4f8b935a4e889d7d` / `85711011a96ebaa46a77b5165aec0ab46e676542`
- Protocol: `b5ffc581b79adfc9807face27777a0ae9dc582f8` / `85827508b6b5c23eaca020c8e36ae20b54023aa0`
- Candidate commit/tree: `CORRECTED_RESULT_COMMIT_PENDING_CURRENT_COMMIT`
- Evidence class: `EXPLORATORY`
- Independent reviewer: `UNRESOLVED_HUMAN_INPUT`
- Human-owner disposition: `UNRESOLVED_PENDING_CORRECTED_EXACT_HEAD_REVIEW`

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
