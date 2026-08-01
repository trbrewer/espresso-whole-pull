# Espresso Whole-Pull

OpenFOAM-based research solver for espresso-puck wetting, porous flow, extraction, and multiscale integration with Puckworks.

> **Research software:** Hydraulic integration through static radial
> heterogeneity and saturated quasi-static compaction are merged. The active
> phase is source-specific validation and mechanism discrimination. Physical
> validation is **NOT_ESTABLISHED**.

The approximately 40 g beverage endpoint at 30 s was used in the saturated-permeability calibration. It is not an independent prediction or validation target. The software does not yet predict taste.

## Current scope

The Foundation OpenFOAM 12 model represents initially dry sharp-front wetting,
prescribed or machine-coupled pressure, Darcy and Darcy–Forchheimer saturated
flow, static axial/radial permeability heterogeneity, optional evolving
effective permeability, saturated quasi-static compaction, one-solute
conservative transport and extraction, spatial diagnostics, retained
inventories, and cup accumulation.

The post-WP03-001 roadmap now confronts existing branches with evidence,
uncertainty and identifiability analysis before choosing further governing
physics. Fines migration, dynamic channeling, thermal coupling and multispecies
chemistry remain evidence-selected candidates. Taste and transfer are not
predicted.

The frozen archival R0 baseline is `FROZEN / QUALIFIED` at the numerical and provenance levels. The public source is not byte-identical to that offline archive because host and path metadata were sanitized. The 19-file scientific-input bundle and governing physics are unchanged.

Full generated fields, uncleaned runs, processor directories, compiled executables, and qualification work directories are not stored in Git.

## Evidence and claims

- Public source manifest: `SOURCE_PACKAGE_MANIFEST.json`
- Public derivation: `provenance/PUBLIC_BASELINE_DERIVATION.json`
- Sanitization proof: `provenance/PUBLIC_SANITIZATION_REPORT.json`
- Compact baseline summary: `validation/baselines/v0.1.4/PUBLIC_BASELINE_SUMMARY.json`
- Claim ceiling: `docs/CLAIM_CEILING.md`
- Controlling strategy:
  `docs/strategy/WHOLE_PULL_MODELING_AND_SIMULATION_STRATEGY.md`
- Concise roadmap:
  `docs/strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md`
- Validation action plan:
  `docs/validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md`
- Current project state: `docs/PROJECT_STATE.md`
- VAL-001 correction, retained failure, and governed reproduction record:
  `docs/validation/VAL_001_SOURCE_ADAPTERS_AND_COMPONENT_COMPARISONS.md`

## Development

The current target is OpenFOAM Foundation 12 on 64-bit Linux. Full OpenFOAM execution is manual and release-gated until an isolated reproducible public CI environment is designed. GitHub Actions performs only inexpensive source, static, Python, shell, JSON, boundary, and no-physics checks.

See `docs/ONBOARDING.md` before running or changing the model.

[Puckworks](https://github.com/trbrewer/puckworks) is the public evidence/model/data dependency. It is reviewed and locked at `fc61c4670ec7bf801e40bb391aab16048b8da26b`, checked out with `tools/checkout_puckworks.sh`, and is not a submodule. WP02-001 implements the optional source-linked saturated dissolution-indexed effective-permeability branch selected by WP01R-006. Its governed 9-bar reconstruction and predeclared 8-bar no-retuning same-campaign comparison passed their frozen flow-shape gates without fitting or post-result adjustment. Neither comparison is independent validation, and physical validation remains **NOT_ESTABLISHED**.

WP-0.3A reviewed moving-upstream evidence without advancing the runtime
dependency lock. Its lock disposition is `RETAIN_EXISTING_LOCK`; selected
solver-support evidence is adopted with follow-up, and holdout execution is
not authorized.

The tagged `v0.1.4-public.1` package remains the immutable sanitized public R0
baseline and retains its historical no-governing-physics release contract.
Version 0.2.0 is a software and source-linked reconstruction release, not a
physical-validation release.

The published release and bounded assets are available at
[v0.2.0](https://github.com/trbrewer/espresso-whole-pull/releases/tag/v0.2.0).
WP-0.3A reviewed the moving Puckworks evidence baseline and found no presently
qualifying independent hydraulic holdout. VAL-001 then implemented the
adapter framework and completed three bounded current-head OpenFOAM runs, but
its first corrected real-data invocation failed after score exposure and was
invalidated without retry under that authority. A separately authorized
one-token Python Boolean repair and one replacement invocation produced the
governed V2 bundle. That result is a post-observation, non-blind,
non-independent descriptive reproduction, not authorization for another
mechanism. PR #38 remains open and awaits independent re-adjudication.
Experimental commissioning, protected scoring and holdout execution remain
unauthorized; physical validation remains **NOT_ESTABLISHED**.

The final additive hardening preserves V2 byte-for-byte, marks its replacement
authority consumed, removes caller-selected governed identities, and deeply
validates the retained V2 result and invocation history. It also corrects the
source citation to Waszkiewicz, N. et al., *Physics of Fluids* 38, 063113
(2026), DOI 10.1063/5.0319611. No comparison or OpenFOAM execution occurred in
this hardening cycle. PR #38 remains open for independent read-adjudication.

The completion layer inventories 64 governed machine-readable records,
uses explicit per-record schema treatment, derives the invocation summary
deterministically from the four-event append-only journal, and binds the final
consumed state. It performed no new comparison and no OpenFOAM work; V2 is
unchanged and remains post-observation, non-blind, non-independent, and
descriptive. The prior 4/60 schema gap is closed: every governed record now
uses a direct class-, version-, or record-specific deep schema, with no
sidecar-primary or generic catch-all validation.

## License

The solver and repository code are licensed under GPL-3.0-or-later. See `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md`, and `docs/LICENSING.md`. This licensing audit is informational and not legal advice.
### VAL-001 final administrative closure

PR #38 now uses zero-exclusion enumeration and an acyclic 86-record binding
graph terminating in the canonical lock at the reviewed Git head/tree. Schema
documents receive recursive keyword-value validation and explicit semantic
profiles fail closed for historical, campaign, protected/holdout, fitting,
identifiability, claim, and consumed-authority escalation. The retained V2
result and four-event invocation journal are unchanged. No comparison or
OpenFOAM execution occurred; the prior OpenFOAM bytes are restored read-only
in the external audit store. Physical validation remains not established.
