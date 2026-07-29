# Public Repository Agent Rules

- Read `docs/ONBOARDING.md`, `docs/PROJECT_STATE.md`, `docs/CLAIM_CEILING.md`, and the controlling strategy before substantive work.
- Preserve tag `v0.1.4-public.1` and the offline archival identities in `provenance/`.
- Declare every scientific change as `NO_GOVERNING_PHYSICS_CHANGE`, `SOURCE_SCENARIO_CHANGE_ONLY`, `NUMERICAL_METHOD_CHANGE`, or `GOVERNING_PHYSICS_CHANGE`.
- Never describe numerical qualification as physical validation.
- Do not silently reuse comparison or holdout data for calibration.
- Do not commit generated fields, meshes, processor directories, executables, full logs, uncleaned runs, credentials, hostnames, or local absolute paths.
- Keep Puckworks as a locked external dependency; do not copy rights-restricted material.
- Run source, static, Python, no-physics, shell, JSON, boundary, and secret checks before acceptance.
- Full OpenFOAM runs are manual and release-gated; retain complete evidence outside Git.


## Task-specific public-repository authorization — WP-0.3C

The repository owner explicitly authorizes governed work for:

  WP-0.3C — INDEPENDENT HYDRAULIC CAMPAIGN ACQUISITION
              AND PREREGISTRATION

within the public repository:

  /home/tim/espresso-development/espresso-whole-pull

This task-specific authorization supersedes the general
"writes only in solver-private/" restriction solely for WP-0.3C work in the
exact repository path above.

AUTHORIZED BASELINE

Begin from:

  commit:
    258b4b6526acea98346031ae5cc9c9e7b3ee64a9

The baseline must be verified as exact and clean before any branch or file is
created.

AUTHORIZED INITIAL SCOPE

The agent is authorized to:

1. create a dedicated WP-0.3C branch in espresso-whole-pull;
2. create protocol, governance, intake, schema, template, documentation,
   validation, and non-score-bearing tooling files;
3. update current-state and QA documentation;
4. update deterministic source-manifest generation where required;
5. add tests and fixed-boundary verification;
6. run software, static, manifest, shell, JSON, secret, and governance checks;
7. create commits;
8. push the dedicated branch;
9. open an unmerged pull request;
10. respond to review findings through separately recorded commits within the
    same governed task.

AUTHORIZED STAGE

This authorization initially covers only:

  WP-0.3C-0:
    AUTHORITY_AND_INPUT_INTAKE_SCAFFOLD

and:

  WP-0.3C-P:
    PROTOCOL_AND_PREREGISTRATION_PREPARATION

It does not authorize actual holdout acquisition or model execution.

WRITE BOUNDARY

Writes are permitted only within:

  /home/tim/espresso-development/espresso-whole-pull

for paths explicitly governed by the WP-0.3C task contract and independently
fixed boundary verifier.

Do not write a parallel implementation or history under solver-private/.

Do not copy public-repository work into solver-private/ for later export.

Do not create a second checkout for the purpose of bypassing this authority
boundary.

HUMAN INPUT RULE

The agent must not invent:

- human identities;
- role assignments;
- laboratory or acquisition location;
- machine identity;
- sensor identity;
- serial number;
- calibration result;
- commissioning observation;
- coffee or material lot;
- acquisition date;
- sample size;
- pressure target;
- randomization schedule;
- uncertainty;
- exclusion threshold;
- experimental result;
- storage credential;
- encryption key;
- raw experimental data.

Unresolved real-world fields may appear only in non-final intake records with
the explicit status:

  UNRESOLVED_HUMAN_INPUT

They may not appear as fabricated values or as unresolved placeholders in the
final preregistration.

PRIVACY AND SECRET HANDLING

Do not commit:

- personal contact information;
- credentials;
- passwords;
- API tokens;
- encryption keys;
- raw storage credentials;
- private laboratory addresses;
- unnecessary full equipment serial numbers;
- other sensitive operational information.

Use public role IDs and opaque equipment IDs in the repository where
appropriate.

Keep the private identity-to-role map, exact sensitive serial information,
credentials, and decryption material outside Git under human custody.

HARD PROHIBITIONS

This authorization does not permit:

1. OpenFOAM execution;
2. Puckworks code execution;
3. protected-source access;
4. WP02 analyzer invocation;
5. holdout scoring;
6. model/data comparison;
7. model fitting or retuning;
8. modification of governing physics;
9. modification of the WP02 closure;
10. modification of frozen scenarios or traces;
11. creation of real holdout cases;
12. invention of experimental inputs;
13. acquisition of holdout shots before a final merged preregistration;
14. movement or replacement of the v0.2.0 tag;
15. creation of a release;
16. merge of an acquisition PR without separate human authorization.

EXPIRY

This task-specific write authorization expires when the first of the
following occurs:

- WP-0.3C is formally closed;
- the repository owner revokes the authorization;
- the authorized repository path changes;
- work departs from the declared WP-0.3C scope.

Any later authorization for commissioning or holdout acquisition must be
explicitly recorded and must not be inferred from this initial permission.
