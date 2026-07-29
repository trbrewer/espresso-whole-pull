# Espresso Whole-Pull

OpenFOAM-based research solver for espresso-puck wetting, porous flow, extraction, and multiscale integration with Puckworks.

> **Research software:** v0.2.0 finalizes WP-0.2A. It
> adds one optional governing-physics closure while preserving the immutable
> v0.1.4-public.1 R0 baseline and constant R1 control. Physical validation is
> **NOT_ESTABLISHED**.

The approximately 40 g beverage endpoint at 30 s was used in the saturated-permeability calibration. It is not an independent prediction or validation target. The software does not yet predict taste.

## Current scope

The current Foundation OpenFOAM 12 model represents initially dry sharp-front wetting, saturated Darcy flow, one-solute conservative transport and extraction, retained inventories, and cup accumulation.

Evolving structure, fines migration, channeling, thermal coupling, and multispecies chemistry are roadmap capabilities, not implemented or validated capabilities of R0. Taste and transfer across coffees, grinders, baskets, machines, and recipes are not yet predicted.

The frozen archival R0 baseline is `FROZEN / QUALIFIED` at the numerical and provenance levels. The public source is not byte-identical to that offline archive because host and path metadata were sanitized. The 19-file scientific-input bundle and governing physics are unchanged.

Full generated fields, uncleaned runs, processor directories, compiled executables, and qualification work directories are not stored in Git.

## Evidence and claims

- Public source manifest: `SOURCE_PACKAGE_MANIFEST.json`
- Public derivation: `provenance/PUBLIC_BASELINE_DERIVATION.json`
- Sanitization proof: `provenance/PUBLIC_SANITIZATION_REPORT.json`
- Compact baseline summary: `validation/baselines/v0.1.4/PUBLIC_BASELINE_SUMMARY.json`
- Claim ceiling: `docs/CLAIM_CEILING.md`

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
qualifying independent hydraulic holdout. Its frozen contract authorizes no
execution and no additional mechanism. The next evidence task is to acquire
the independently instrumented pressure/flow campaign specified by that
contract; physical validation remains **NOT_ESTABLISHED**.

## License

The solver and repository code are licensed under GPL-3.0-or-later. See `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md`, and `docs/LICENSING.md`. This licensing audit is informational and not legal advice.
