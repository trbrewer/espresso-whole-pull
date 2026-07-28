# Publication Audit

Overall disposition: **PASS**

Mandatory technical publication gates pass. Tim Brewer supplied the
owner/rightsholder attestation; authorship and rights provenance is
`OWNER_ATTESTED`, and repository publication is `APPROVED_BY_OWNER`.

## Identity and scientific gates

- Public source verification: 106/106 PASS
- Current public aggregate: `ad6f9b84e69b6178d77f867a085198908dcda4afe2360ec840824faadc793267`
- Archival aggregate: `182f14a036e1fc92db8f40f6025bda164ced32f108368e7aa674abd6b032508e`
- Scientific inputs: 19/19 byte-identical; aggregate `d70399a76b0023d93985d76c1c83a9a42b7148b3d71d16d1b5f88275be1ebe7a`
- No-physics contract: 28/28 PASS; governing-physics change `false`
- Scientific-configuration change: `false`
- Static validation: 32/32 PASS
- Python tests: 41/41 PASS
- Git-mode portability: PASS across non-executable `0644` and `0664`
  layouts; executable-bit, content, missing-path, and added-path changes are
  detected.
- Candidate reachable Git history: PASS (4 commits, 2 tags, 142 unique blobs,
  1,434,017 reachable blob bytes including the staged owner-attestation tree).

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

License disposition: **PASS**.

The custom solver declares GPL-3.0-or-later and the repository includes the GPLv3 text. Puckworks is external and MIT-licensed. No Puckworks code/data, third-party binary, archived executable, paper text, or restricted dataset was identified.

Only the main solver source presently carries an SPDX header. Tim Brewer
supplied the good-faith owner/rightsholder statement recorded in the
attestation. Remaining provenance exceptions: none. This automated audit is
not legal advice and provides no automated legal opinion.

## GitHub check

GitHub CLI was unavailable, so an authenticated account could not be reported. An unauthenticated public URL check returned 404 for the proposed repository. This establishes that no public repository is visible at that URL; it cannot rule out a private repository.

No repository, remote, branch, tag, or asset was published.
