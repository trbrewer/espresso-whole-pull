# Espresso Whole-Pull

OpenFOAM-based research solver for espresso-puck wetting, porous flow, extraction, and multiscale integration with Puckworks.

> **Research software:** v0.1.4-public.1 is a sanitized public derivative of a numerically qualified bounded R0 calibration scenario. Physical validation is **NOT_ESTABLISHED**.

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

[Puckworks](https://github.com/trbrewer/puckworks) is the public evidence/model/data dependency. It is locked by full commit SHA and checked out with `tools/checkout_puckworks.sh`; it is not a submodule. A fresh Puckworks `main` alignment review is the first post-bootstrap scientific task.

## License

The solver and repository code are licensed under GPL-3.0-or-later. See `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md`, and `docs/LICENSING.md`. This licensing audit is informational and not legal advice.
