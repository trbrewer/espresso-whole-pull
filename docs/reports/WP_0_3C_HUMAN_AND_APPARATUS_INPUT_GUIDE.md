# WP-0.3C Stage-0 human and apparatus input guide

WP-0.3C Stage 0 supplies intake structure only. It authorizes no commissioning,
holdout acquisition, model execution, scoring, fitting, or governing-physics
change. Every unavailable real-world value remains
`UNRESOLVED_HUMAN_INPUT`; values must not be inferred from earlier campaigns.

## Intake sequence

The requirements registry assigns each field an input classification, deadline,
and accountable role ID. Complete protocol-design fields first, followed by
apparatus and calibration-planning fields. Material, preparation, custody, and
blinding inputs must be reviewed before any later final preregistration.

The templates are deliberately non-final. Completing one does not authorize an
experiment. Commissioning and final preregistration require separate owner
authorization and review.

## Public repository package

The public package may contain role IDs, campaign design, public-safe location
classes, equipment make and model, opaque equipment IDs, sensor specifications,
calibration methods, uncertainty requirements, protocol state, hashes, and
non-sensitive provenance.

## Private campaign-custody package

The private package may contain personal names and contact details, a private
laboratory address, sensitive serial numbers, credentials, infrastructure
paths, encryption keys, the condition-code map, and controlled raw data.
Secrets and unnecessary personal information must never enter Git. Where a
binding is needed, the public record carries a digest rather than private
content.

## Deadlines and evidence

Inputs are distinguished as protocol, equipment, private, commissioning,
holdout, derived non-score-bearing, or prohibited. Deadlines distinguish
protocol design, commissioning, final preregistration, acquisition, acquisition
generation, and future WP-0.3D use.

An unresolved field uses a structured object with its deadline, responsible
role, and public/private handling. Fabricated observations, identities,
calibrations, pressure targets, sample sizes, and thresholds are prohibited.

## Current readiness

The current state is
`STAGE0_SCAFFOLD_COMPLETE_AWAITING_HUMAN_INPUTS`. No final preregistration
exists; commissioning and acquisition are not authorized. Physical validation
remains `NOT_ESTABLISHED`.
