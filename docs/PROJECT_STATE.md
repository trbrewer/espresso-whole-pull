# Project State

- Current released version: `v0.2.0`
- Current merged `main`: `f475eef5c7a93f833a51ce03485c557ce0620b8d`
- Current merged tree: `493934e1d9e30461c9ca289dcc82ad43084eaf4b`
- Public baseline: `v0.1.4-public.1`, immutable sanitized R0 derivative
- Archival baseline: WP-0.1H v0.1.4, `FROZEN / QUALIFIED`
- OpenFOAM target: Foundation 12
- Puckworks integration: locked external checkout, no submodule
- Public source verification: 179/179 PASS
- Active phase: `POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION`
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

No governing physics changes and no validation executions occur in this
documentation alignment task. The next recommended implementation is a
source-specific validation adapter framework with first component
comparisons. It will preserve evidence definitions and rights, separate
calibration from comparison, quantify uncertainty and identifiability, compare
existing mechanisms, and recommend one next physics increment from residuals.

See the concise
[solver development and validation roadmap](strategy/SOLVER_DEVELOPMENT_AND_VALIDATION_ROADMAP.md)
and the
[post-WP03-001 validation and mechanism-discrimination plan](validation/POST_WP03_001_VALIDATION_AND_MECHANISM_DISCRIMINATION_PLAN.md).

General whole-solver physical validation remains `NOT_ESTABLISHED`.
