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

The registry also machine-inherits the frozen WP-0.3A campaign requirements:
independence, preregistration and blinding, at least two pressure groups, at
least five independent shots per group, a pre-execution sample-size adequacy
justification, required hydraulic channels, geometry, timing, uncertainty and
metadata, machine/headspace discrimination requirements, fixed WP02
parameters, and no holdout fitting. These are governing requirements rather
than unresolved inputs.

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

Readiness is evaluated only from a complete, exact registry mapping with
explicit authority. A complete set of resolved human inputs stops at
`HUMAN_INPUTS_COMPLETE_AWAITING_GOVERNED_REVIEW`; Stage 0 cannot emit
`READY_FOR_CALIBRATION_PLANNING`.

A resolved public input must bind a nonempty public value to an evidence
digest and accountable evidence role. A resolved private input exposes no
private value; it binds a nonempty private-package digest to a custody record
and custodian role. Status-only resolution, unknown keys, and malformed
bindings fail closed.
