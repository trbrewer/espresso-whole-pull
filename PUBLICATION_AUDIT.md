# Publication Audit

Overall disposition: **PASS with HUMAN_REVIEW_REQUIRED**

Mandatory technical publication gates pass. Human review remains required for legacy-file authorship/license provenance and for the final GitHub repository creation decision.

## Identity and scientific gates

- Public source verification: 106/106 PASS
- Current public aggregate: `7aa09c0846608945a480cc54e610d62eb0becfc7e01a073f5ad0186315aebf2b`
- Archival aggregate: `182f14a036e1fc92db8f40f6025bda164ced32f108368e7aa674abd6b032508e`
- Scientific inputs: 19/19 byte-identical; aggregate `d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a`
- No-physics contract: 28/28 PASS; governing-physics change `false`
- Scientific-configuration change: `false`
- Static validation: 32/32 PASS
- Python tests: 36/36 PASS

## Publication-boundary scans

- Private home-path token: 0
- Private hostname token: 0
- Absolute home paths: 0
- Private workspace directory names: 0
- Personal-email content: 0
- Credential/token/private-key/password patterns: 0
- Generated OpenFOAM products: 0
- Files over 10 MiB: 0
- Files over 50 MiB: 0
- Broken local Markdown links: 0
- JSON parsing: PASS
- YAML/CFF parsing: PASS
- Shell syntax: PASS

The approved public email appears only in local Git commit/tag metadata, not repository files.

`gitleaks` was not installed; an explicit regex scan covered common token, private-key, cloud-key, and password forms. This is a residual tooling limitation.

## Licensing

License disposition: **PASS with HUMAN_REVIEW_REQUIRED**.

The custom solver declares GPL-3.0-or-later and the repository includes the GPLv3 text. Puckworks is external and MIT-licensed. No Puckworks code/data, third-party binary, archived executable, paper text, or restricted dataset was identified.

Only the main solver source presently carries an SPDX header. Human review should confirm authorship and rights for all legacy scripts, tests, documentation, and sanitized evidence before publication. This automated audit is not legal advice.

## GitHub check

GitHub CLI was unavailable, so an authenticated account could not be reported. An unauthenticated public URL check returned 404 for the proposed repository. This establishes that no public repository is visible at that URL; it cannot rule out a private repository.

No repository, remote, branch, tag, or asset was published.
