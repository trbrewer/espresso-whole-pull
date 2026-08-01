# Validation Review Checklist v1

Use this checklist for one proportionate independent review. Record evidence,
not merely `PASS` labels.

## Review object

- [ ] Exact repository, base, branch, candidate commit, and tree are recorded.
- [ ] Required checks belong to that exact candidate.
- [ ] Evidence class and intended claim were frozen before execution.
- [ ] Framework version, evidence manifest, protocol, and rights state are pinned.

## Scientific and evidence review

- [ ] Arithmetic and implementation behavior are adequate for the declared case.
- [ ] Calibration, reconstruction, independent comparison, holdout, and transfer roles remain distinct.
- [ ] Evidence provenance, rights, admissibility, exclusions, units, and uncertainty are represented accurately.
- [ ] The interpretation does not exceed the evidence class or claim ceiling.
- [ ] Protected or holdout evidence was accessed only under explicit authority.

## Materiality test

For every finding, ask whether it can materially affect:

- [ ] numerical correctness or scientific interpretation;
- [ ] evidence provenance, rights, or admissibility;
- [ ] calibration leakage, holdout leakage, independence, or material reproducibility;
- [ ] the claim ceiling or authorization boundary.

If none apply, the finding must not block the scientific result. Classify a
useful framework improvement as `VALIDATION_INFRASTRUCTURE_BACKLOG`, or a
presentation-only defect as `MINOR`.

## Non-retroactivity guard

- [ ] Every blocking requirement existed in the frozen protocol/checklist, or exposes a material risk above.
- [ ] No new nonmaterial requirement was introduced as a blocker after execution.
- [ ] Hypothetical extra mutations or governance layers were not treated as mandatory without a demonstrated material bypass.
- [ ] Machine-readable governance records were not recursively promoted to scientific evidence.

## Correction and cadence

- [ ] Findings are routed through the standard correction matrix.
- [ ] No more than one bounded correction cycle occurred unless a prior material blocker remained or the correction introduced a new material defect.
- [ ] General framework hardening was moved to a separate `VAL-INFRA-xxx` task.

## Required disposition

Record all three:

```text
SCIENTIFIC_RESULT_DISPOSITION:
  <disposition and bounded rationale>

VALIDATION_FRAMEWORK_DISPOSITION:
  <disposition and any nonmaterial backlog references>

CLAIM_CEILING:
  <strongest supported claim and explicit unestablished/unauthorized claims>
```

- [ ] Human-owner disposition is requested after the independent review.
