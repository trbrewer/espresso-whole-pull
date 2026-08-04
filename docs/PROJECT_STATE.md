# Project State

- Current released version: `v0.2.0`
- Current merged `main`: `0a5c146078da5d5f88b344b20e7b81042bf27ddb`
- Current merged tree: `12fdbc542270e2765e2071d83c21812951f892e8`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule
- Public source verification: 272/272 PASS
- Active validation case: `VAL_CORPUS_002_STAGE_B2_SENSITIVITY_COLOUR_KEY_CORRECTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW`
- Active data-planning task: `NONE`
- Active solver task: `NONE`
- Physical validation: `NOT_ESTABLISHED`
- Experimental commissioning: `NOT_AUTHORIZED`
- Protected or holdout scoring: `NOT_AUTHORIZED`

The exact source-manifest count and aggregate are generated in
[`SOURCE_PACKAGE_MANIFEST.json`](../SOURCE_PACKAGE_MANIFEST.json).

VAL-CASE-001 is complete, exact-head approved, and merged. Its corrected v2
result remains validation-support sensitivity and practical-identifiability
screening; it does not establish physical validation. VAL-CASE-002 is
`NOT_STARTED`.

WP03-002 is `COMPLETE_APPROVED_AND_MERGED` at merge commit
`0a5c146078da5d5f88b344b20e7b81042bf27ddb`; its approved head was
`78dc278212976a569bf21dda139a98c35756db14` and its executed solver SHA-256 was
`e682bb63d4b54a19133a81e1dc857217132b91918ecceb33ffbc88c35b6b0fd6`.
VAL-CORPUS-002 Stage A and the final Stage-B0 tooling are exact-head approved.
Stage B1 attempt 1 stopped on an infrastructure failure and remains immutable.
The bounded attempt-2 recovery verified all 20 passing evaluations as a
complete cache, replayed the optimizer from its original bounds, and completed
26 fresh evaluations. The exact P2 rate is a frozen candidate pending
independent exact-head review. Its exact-head semantic correction now parses
and independently reduces the retained trace, validates the closed numerical
record, and deterministically reproduces the strengthened governed bundle
without solver or optimizer execution. Stage B2 now has all 45 terminal
production dispositions (27 PASS and 18 immutable typed target-coverage
failures); its numerical campaign and approved scientific interpretation are
unchanged. Final reporting now identifies Schmieder `cup_masses.csv` as
post-fit derived evidence, not an independent measurement. Merge and any next
mechanism remain unauthorized. The corrected Waszkiewicz P2 case passed,
predecessor parity remains
1,500/1,500, and the nine-identity sensitivity inventory passed with one exact
baseline reuse. Frozen governed reductions and deterministic reporting are
complete pending final exact-head review. The result is local reconstruction
only with partial directional transfer, grind-sign reversal, and cross-source
time-shape failure. The fail-closed framework is operational. Calibration
remains closed with no refit. Protected scoring and VAL-CASE-002 remain
unauthorized and have not started.

The next scientific gate is `ADDITIONAL_INDEPENDENT_DATA_REQUIRED`: either an
admissible independent dataset or the synchronized pressure, flow/mass,
deformation, machine-side pressure, timing, and preparation measurement
package identified by VAL-CASE-001. No acquisition, commissioning, or new
governing physics is authorized by the administrative closure.

VAL-DATA-001 is a complete, approved, and merged non-commissioning plan for
the synchronized measurement package. `EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED`,
`GOVERNING_PHYSICS_CHANGE: NONE`, and VAL-CASE-002 remains `NOT_STARTED`.
Its final status is `COMPLETE_APPROVED_AND_MERGED`; the future
evidence route still requires prospective human-owner selection.
The final schema correction restores exact frozen VAL-CASE-001 parameter
classifications, makes partition rules route-conditional, closes all declared
foreign keys, and assigns measured pressure to one authoritative signal table.
The historical referential-integrity candidate correction bound complete pressure-sample keys,
global resource keys, table-specific null rules, and cross-table campaign and
route invariants; its then-current status was
`CORRECTED_PENDING_EXACT_HEAD_REVIEW`. Exact-head approval and PR #48 merge
subsequently closed that candidate state.
The template-interoperability correction separates local campaign instances
from catalog IDs, adds deterministic Puckworks exports, and represents
processing lineage as an acyclic multi-input/multi-output edge graph.
The implementation-contract closure binds samples and deformation to the
shot apparatus and signal registry, makes calibration applicability
registry-controlled, adds fraction parents and partition-isolated
compatibility packages, types resource payloads with terminal rights, and
separates row-value processing from file assembly and exact synchronized
exports. Commissioning remains unauthorized.
The final machine-contract closure completes all field/reference bindings,
makes package identities and summaries partition-specific, adds registered
basket-top temperature, records exact or two-source interpolated export
provenance, adds package-level fraction/chemistry disposition, and enforces
one export grid and one `COMPATIBILITY_EXPORT` operation per time-series
package.
The final export-contract reconciliation separates fixed unit conversion from
flow/density conversion, enforces the three-layer processing graph, separates
time-indexed samples from record/literal provenance, freezes package-mode
nullability and scalar encodings, and binds terminal mass to a realized shot
event. The task remains non-commissioning.
The historical compatibility-serialization closure reconciled typed resource members,
defines a sealed metadata envelope distinct from a Puckworks submission,
freezes row and nested-field ordering, maps local provenance to Puckworks
`raw`/`processed`, and removed recursive manifest dependencies. PR #48 was
subsequently approved and merged; commissioning remains unauthorized.
The state-and-serialization consistency correction makes package-operation
references mode-conditional, gives full and sealed exports disjoint graph
branches, removes unreachable status values, makes row provenance mapping
total, and freezes the apparatus calibration scalar and YAML emitter. Package
QA now binds the current source-manifest identity exactly.

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

VAL-001 and PR #38 are complete and merged. The source-specific adapter framework was added
without changing governing physics. Its governed V2 comparison remains a
post-observation, non-blind, non-independent descriptive reconstruction; it is
not physical validation and does not authorize a next-physics increment.
VAL-OPS-001 provides a merged concise prospective operating standard for
proportionate validation cases and reusable infrastructure work.

See the concise
[solver development and validation roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
and the
[post-WP03-001 validation and mechanism-discrimination plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md).

General whole-solver physical validation remains `NOT_ESTABLISHED`.

## Completed VAL-CORPUS-001 comparison campaign

VAL-CORPUS-001 is complete, approved, and merged. It executed the unchanged
merged solver against a separately authorized read-only Puckworks evidence
snapshot without advancing the runtime
dependency lock. Exact-head review correction preserved the original attempt
history and added 13 prospectively frozen correction runs; all completed. The
corrected static branches exclude dissolution-indexed permeability evolution,
use 965 kg/m3 for Waszkiewicz mass, and use the frozen +3 s alignment without
extrapolation. Final analysis closure independently calculates measured and
nominal ordering, assigns precise anchor/transfer/post-fit roles, corrects
median-log arithmetic, and evaluates 965/997/1000 kg/m3 flow conversion. All
tested Waszkiewicz families reverse the source condition ordering at every
density. The original three finite-porosity compaction runs remain invalidated
as a separate numerical-robustness finding and were not rerun. The completed
campaign establishes neither independent nor general physical validation. See the
[comparison atlas](validation/VAL_CORPUS_001_EXISTING_EVIDENCE_COMPARISON_ATLAS.md).

WP03-002 reproduced all three finite-porosity failures, diagnosed and corrected
an equation-extrinsic convergence-gate defect, and completed the unchanged
source-linked reruns. The recovered branch still reverses the source 5/9/11
bar flow and mass ordering with Spearman `-1.0`. New governing physics is
`NOT_YET_JUSTIFIED`; VAL-CASE-002 is `NOT_STARTED`.

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
