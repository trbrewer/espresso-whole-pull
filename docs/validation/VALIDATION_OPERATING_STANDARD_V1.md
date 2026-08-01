# Validation Operating Standard v1

**Work package:** VAL-OPS-001

**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`

**Status:** Prospective operating standard; human-reviewed documentation, not a machine-enforced governance framework

## Purpose and scope

This standard keeps validation assurance proportionate to the intended claim.
It applies prospectively to new validation work and does not reinterpret prior
historical evidence. Protected, holdout, regulated, or otherwise consequential
assessments may use stronger controls only through explicit human-owner
authority.

Validation seeks sufficient protection against credible failure modes. It does
not require exhaustive proof against every hypothetical mutation of every
administrative record.

## Evidence classes

Every validation case declares exactly one class before execution:

| Evidence class | Intended use | Minimum governance |
|---|---|---|
| `EXPLORATORY` | Hypothesis formation, debugging, or feasibility | Identify inputs, code/configuration identity, limitations, and non-validation status. |
| `RECONSTRUCTION_OR_CALIBRATION` | Reproduce or calibrate against evidence already used in model construction | Separate fitted/prescribed/compared quantities; disclose circularity and prohibit independence claims. |
| `INDEPENDENT_COMPONENT_VALIDATION` | Test a bounded component against admissible evidence not used for calibration | Freeze protocol, evidence and rights; preserve independence; predeclare metrics, exclusions, and interpretation. |
| `HOLDOUT_OR_TRANSFER` | Test sealed evidence or transfer across a materially distinct domain | Require explicit human-owner authority, access controls, leakage protection, prospective protocol, and rights confirmation. |

Governance scales with this declared class and its claim ceiling. A lower-class
case must not acquire a higher claim through post hoc interpretation.

## Required dispositions

Every completed case reports three independent dispositions:

- `SCIENTIFIC_RESULT_DISPOSITION`: what the evidence says about the tested
  scientific question.
- `VALIDATION_FRAMEWORK_DISPOSITION`: whether the reusable validation tooling
  and process were adequate for this case.
- `CLAIM_CEILING`: the strongest claim supported, including explicit claims
  that remain unestablished or unauthorized.

A framework limitation does not automatically invalidate an otherwise sound
scientific result, and a technically sound framework does not establish a
scientific claim by itself.

## Scientific-result blocker test

A finding blocks the scientific result only when it can materially affect at
least one of:

1. numerical correctness or scientific interpretation;
2. evidence provenance, rights, or admissibility;
3. calibration leakage, holdout leakage, independence, or material
   reproducibility;
4. the claim ceiling or authorization boundary.

All other useful framework findings are recorded as
`VALIDATION_INFRASTRUCTURE_BACKLOG`. Editorial defects may be corrected without
changing the scientific disposition.

## Non-retroactivity

Requirements absent from the frozen protocol or its review checklist cannot
become post-execution blockers unless they reveal one of the material risks in
the blocker test. Reviewers may recommend prospective improvements, but may not
retroactively expand a completed case's obligations for nonmaterial assurance.

## Correction routing

| Finding class | Required action |
|---|---|
| `RESULT_AFFECTING_METHOD_OR_DATA_DEFECT` | Invalidate the affected result and rerun under corrected prospective controls. |
| `RIGHTS_PROVENANCE_OR_LEAKAGE_DEFECT` | Stop; do not access, score, or claim until resolved. |
| `SOFTWARE_ASSEMBLY_DEFECT_WITH_UNCHANGED_ARITHMETIC` | Patch, test, and reproduce while preserving adverse and corrective lineage. |
| `METADATA_OR_REPORTING_DEFECT` | Correct by addendum without rerun. |
| `GENERAL_FRAMEWORK_HARDENING` | Move to a separate `VAL-INFRA-xxx` task. |

## Work-package separation

- `VAL-CASE-xxx` covers one scientific comparison. It pins a released
  validation-framework version and may not modify that framework.
- `VAL-INFRA-xxx` develops reusable validation infrastructure using synthetic
  fixtures. It may not score governed scientific evidence.

Infrastructure and scientific comparison changes must not be combined merely
for convenience.

## Standard case artifacts

A validation case normally contains only:

1. protocol;
2. evidence manifest;
3. execution record;
4. result bundle;
5. independent review disposition;
6. correction addendum, only when needed.

Direct artifact hashes plus Git commit and tree identity are the normal
administrative provenance root. Governance records are not recursively treated
as scientific evidence merely because they are machine-readable.

## Review cadence

The normal sequence is:

1. protocol review;
2. execution;
3. one independent result review;
4. at most one bounded correction cycle;
5. human-owner disposition.

A further correction cycle is permitted only when an existing material blocker
was not actually resolved or the correction introduced a new material defect.
New nonmaterial assurance ideas go to the validation-infrastructure backlog.

## Boundaries

This standard does not authorize evidence access, execution, fitting,
commissioning, solver or configuration changes, protected or holdout work, or
scientific claims. Those actions require the authority appropriate to the
declared evidence class and case.
