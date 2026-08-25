# Contributing

Contributions are welcome through focused issues and pull requests.

## Choose the governed issue form

Use the **Evidence or governance task** form for evidence inventories,
dependency reviews, source dossiers, calibration or validation contracts,
rights reviews, scientific decision records, and similar tasks that declare
`NO_GOVERNING_PHYSICS_CHANGE`.

Use the **Scientific change proposal** form for source-scenario,
numerical-method, or governing-physics changes. It may also record a
no-physics change when a scientific-change review is specifically appropriate.

One governed issue should normally map to one principal pull request. Complete
each form field with the information it asks for; do not paste the same task
description into multiple fields. Every pull request must identify its
principal issue and select exactly one change declaration.

Before proposing a change:

Scientific-development governance follows
`docs/governance/MINIMUM_NECESSARY_GOVERNANCE_STANDARD.md`.
Controls must remain proportional to the declared governance class; stricter
controls require an explicit owner exception tied to a named risk.

1. Read `docs/ONBOARDING.md`, `docs/CLAIM_CEILING.md`, and the controlling strategy.
2. State the change declaration and evidence role.
3. Keep calibration inputs separate from protected comparisons.
4. Run the inexpensive validation suite.
5. Do not commit generated OpenFOAM products or private/local metadata.

Generated fields, meshes, processor directories, executables, runtime logs,
uncleaned runs, and other OpenFOAM products remain outside Git. Record their
external identities when a governed task produces them.

Scientific changes require a reviewed rationale, affected equations/configuration, tests, provenance, and claim-impact assessment. Passing tests do not establish physical validation.

R1 implementation may not begin until its source/evidence and
calibration/protected-comparison contracts have been reviewed and accepted.

Contributions are provided under the repository’s applicable licenses.
