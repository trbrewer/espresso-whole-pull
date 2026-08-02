# Project State

- Current released version: `v0.2.0`
- Current merged `main` at VAL-001 branch start: `34bd440f87d7b4ba6a955e54f40122d28f760ae3`
- Current merged tree at VAL-001 branch start: `6d18e29b99ea5ec24d6cef7615deb541cf4737ff`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule
- Public source verification: 226/226 PASS
- Active validation case: `NONE`
- Active data-planning task: `VAL-DATA-001`
- Physical validation: `NOT_ESTABLISHED`
- Experimental commissioning: `NOT_AUTHORIZED`
- Protected or holdout scoring: `NOT_AUTHORIZED`

The exact source-manifest count and aggregate are generated in
[`SOURCE_PACKAGE_MANIFEST.json`](../SOURCE_PACKAGE_MANIFEST.json).

VAL-CASE-001 is complete, exact-head approved, and merged. Its corrected v2
result remains validation-support sensitivity and practical-identifiability
screening; it does not establish physical validation. VAL-CASE-002 is
`NOT_STARTED`.

The next scientific gate is `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`: either an
admissible independent dataset or the synchronized pressure, flow/mass,
deformation, machine-side pressure, timing, and preparation measurement
package identified by VAL-CASE-001. No acquisition, commissioning, or new
governing physics is authorized by the administrative closure.

VAL-DATA-001 is an active non-commissioning planning task for the synchronized
measurement package. `EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED`,
`GOVERNING_PHYSICS_CHANGE: NONE`, and VAL-CASE-002 remains `NOT_STARTED`.
Its exact-head review correction status is
`VAL_DATA_001_REVIEW_STATUS: CORRECTED_PENDING_EXACT_HEAD_REVIEW`; the future
evidence route still requires prospective human-owner selection.
The final schema correction restores exact frozen VAL-CASE-001 parameter
classifications, makes partition rules route-conditional, closes all declared
foreign keys, and assigns measured pressure to one authoritative signal table.
The referential-integrity correction binds complete pressure-sample keys,
global resource keys, table-specific null rules, and cross-table campaign and
route invariants; status remains `CORRECTED_PENDING_EXACT_HEAD_REVIEW`.
The template-interoperability correction separates local campaign instances
from catalog IDs, adds deterministic Puckworks exports, and represents
processing lineage as an acyclic multi-input/multi-output edge graph.
The implementation-contract closure binds samples and deformation to the
shot apparatus and signal registry, makes calibration applicability
registry-controlled, adds fraction parents and partition-isolated
compatibility packages, types resource payloads with terminal rights, and
separates row-value processing from file assembly and exact synchronized
exports. Commissioning remains unauthorized.

VAL-INFRA-002 is a merged reusable-infrastructure repair that scopes the
legacy WP-0.3C Stage-0 verifier scope. It changes no scientific result,
framework pin, operating standard, solver, configuration, dependency, or claim
ceiling and performs no scientific execution. Its exact-head correction binds
protected Git modes and object types, rejects symbolic-link substitution, and
requires the pinned Stage-0 merge to be an ancestor of the candidate.

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

VAL-001 and PR #38 are merged. The source-specific adapter framework was added
without changing governing physics. Its governed V2 comparison remains a
post-observation, non-blind, non-independent descriptive reconstruction; it is
not physical validation and does not authorize a next-physics increment.
VAL-OPS-001 now proposes a concise prospective operating standard for
proportionate validation cases and reusable infrastructure work.

See the concise
[solver development and validation roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
and the
[post-WP03-001 validation and mechanism-discrimination plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md).

General whole-solver physical validation remains `NOT_ESTABLISHED`.

## Completed VAL-CASE-001 validation-support case

VAL-CASE-001 applies the merged Validation Operating Standard v1 without
changing the solver or reusable validation framework. Its prospectively
frozen local campaign completed 47 valid Foundation OpenFOAM 12 cases, with
two completed probe endpoints transparently invalidated under one bounded
correction. The result screens hydraulic and compaction sensitivities,
practical identifiability, existing model-form separation, and future
measurement information value. It performs no fitting or external-data
scoring and establishes no physical validation. Independent exact-head review
approved the corrected result, and PR #42 merged as
`c2c3136e5aae74306f37f8389f945139a9d9009f`. See the
[case report](validation/cases/VAL_CASE_001_HYDRAULIC_COMPACTION_IDENTIFIABILITY_RESULTS.md).

## Merged VAL-001 framework

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

The registry, synthetic transaction, and journal-to-summary gaps were closed by
PR #38. The summary
ledger is byte-derived from the four-event journal and the production runner
refuses the final consumed authority before source access. The former
deep-schema gap is closed through 68 registry-referenced normative schema
families and direct validation of 105 current and immutable historical records.
## VAL-001 PR #38 administrative remediation

The merged candidate directly enumerates and validates all governed JSON/JSONL
records with no exclusions, cycles, or orphans. The administrative freeze is
bound by a canonical consumed lock containing the complete freeze commit and
tree. Recursive schema-AST validation remains active. Sixty-eight normative
contracts regenerate governing schemas without governed instances, all 48
earlier inferred families have transition provenance, and immutable registry
assignments select 18 executable profiles. The 340-entry mutation inventory
executes one-to-one. Final candidate closure additionally requires externally
supplied exact head and tree identities. No comparison or OpenFOAM execution
occurred in this correction. V2 remains descriptive,
post-observation, non-blind, and non-independent. No new scoring, solver run,
fit, protected access, experiment, or physics change occurred.
