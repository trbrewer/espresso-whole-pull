# Project State

- Current released version: `v0.2.0`
- Current merged `main` at VAL-001 branch start: `34bd440f87d7b4ba6a955e54f40122d28f760ae3`
- Current merged tree at VAL-001 branch start: `6d18e29b99ea5ec24d6cef7615deb541cf4737ff`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule
- Public source verification: 196/196 PASS
- Active candidate: `VAL-001_SOURCE_SPECIFIC_VALIDATION_ADAPTERS`
- Physical validation: `NOT_ESTABLISHED`
- Experimental commissioning: `NOT_AUTHORIZED`
- Protected or holdout scoring: `NOT_AUTHORIZED`

The exact source-manifest count and aggregate are generated in
[`SOURCE_PACKAGE_MANIFEST.json`](../SOURCE_PACKAGE_MANIFEST.json).

## Completed sequence

- **WP-0.1:** reference whole-pull implementation — complete.
- **WP-0.1H:** numerical hardening and frozen R0 qualification — complete,
  frozen and qualified.
- **WP01R:** source-linked reconstruction and residual assessment — complete
  with a structural residual; not independent physical validation.
- **WP02-001:** optional dissolution-indexed effective permeability — complete.
- **WP02-002:** lumped machine/headspace compliance and emergent basket
  pressure — complete.
- **WP02-003:** saturated Darcy–Forchheimer resistance and regime diagnostics
  — complete.
- **WP02-004:** static radial permeability heterogeneity with zone-resolved
  flow and extraction — complete.
- **WP03-001:** saturated finite-porosity quasi-static compaction — complete.

WP03-001 changes mechanical porosity and hydraulic permeability under
effective stress and composes with the machine operating-point calculation.
It is inactive during wetting and uses a fixed reference mesh. It does not
solve solid displacement or couple mechanical porosity to transport storage,
and it excludes transient Biot storage, plasticity, hysteresis, swelling,
fines, damage and dynamic channeling. Its tested cases are numerically
verified; physical validation is not established.

## Current merged capabilities

The solver includes dry-puck sharp-front wetting, first drip, prescribed or
lumped-machine pressure boundaries, upstream resistance and compliance,
Darcy and Darcy–Forchheimer saturated flow, uniform/axial/radial permeability
profiles, optional dissolution-indexed effective permeability, quasi-static
compaction, conservative one-solute transport, spatial extraction diagnostics,
cup accumulation, and water/solute conservation reporting.

R0 remains frozen and unchanged. Source-linked and synthetic mechanism
diagnostics are not improved predictions merely because they add complexity.

## Active next program phase

The open VAL-001 correction candidate implements the source-specific adapter
framework without changing governing physics. Three prospectively declared
current-head OpenFOAM cases completed. The one authorized corrected real-data
comparison invocation failed after in-memory score exposure and remains
invalidated. Under separate human-owner replacement authority, the minimal
Python Boolean defect was repaired and exactly one replacement invocation
produced the governed V2 bundle. The replacement reused the three verified
OpenFOAM artifacts without rebuild or rerun. PR #38 remains open and awaits
independent re-adjudication; it does not authorize a next-physics increment.

See the concise
[solver development and validation roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
and the
[post-WP03-001 validation and mechanism-discrimination plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md).

General whole-solver physical validation remains `NOT_ESTABLISHED`.

## Open VAL-001 candidate

VAL-001 adds enforced source adapters, semantic validation, evidence/rights
and calibration/comparison ledgers, synthetic adversarial tests, historical
re-expression records, campaign provenance, and a fail-closed evidence-gap
adapter. The initial PR arithmetic remains verified for ten in-domain points,
but its prospective-governance status is invalidated. The corrected invocation
failed after score exposure and remains invalidated. The separately authorized
replacement is `POST_OBSERVATION_REPRODUCTION`, `NOT_BLIND`, and
`NOT_INDEPENDENT`; it produced one governed result without a new OpenFOAM run.
No protected or holdout data, retuning, physics, threshold, or scientific
configuration change occurred. See the
[VAL-001 report](validation/VAL_001_SOURCE_ADAPTERS_AND_COMPONENT_COMPARISONS.md).

Final post-result hardening consumes all remaining real-data execution
authority. The original result remains arithmetic-correct but prospectively
invalidated; the first corrected invocation remains failed after score
exposure; and V2 remains the successful post-observation, non-blind,
non-independent descriptive reproduction. V2 was not rewritten. Quantitative
discrimination and mechanism uniqueness were not assessed;
`ADDITIONAL_DATA_REQUIRED_BEFORE_NEW_PHYSICS` is a conservative evidence-policy
decision. Three earlier current-head OpenFOAM runs qualify the framework but
did not produce the V2 pressure-sweep columns.

The registry, synthetic transaction, and journal-to-summary gaps are closed on
the open PR #38 candidate. The summary
ledger is byte-derived from the four-event journal and the production runner
refuses the final consumed authority before source access. Independent
read-only re-adjudication is still required before merge. The former 4/60
deep-schema gap is closed through 45 taxonomy-derived schema families and
direct validation of current and immutable historical records.
## VAL-001 PR #38 administrative remediation

The final candidate directly enumerates and validates 86 governed JSON/JSONL
records with no exclusions, cycles, or orphans. The administrative freeze is
bound by a canonical consumed lock containing the complete freeze commit and
tree. Recursive schema-AST validation and explicit semantic profiles replace
observed-instance authorization semantics. V2 remains descriptive,
post-observation, non-blind, and non-independent. No new scoring, solver run,
fit, protected access, experiment, or physics change occurred.
