# Reachable Git History Audit

Status: **PASS**

This audit covers every existing reachable object plus every blob in the
staged final-correction tree. The exact reachable-object scan is rerun after
that commit and before bundling.

- Candidate reachable commits: 4
- Local tags: 2 (`v0.1.4-public-source` and `v0.1.4-public.1`)
- Git-note refs: 0
- Candidate unique reachable blobs: 142
- Candidate total reachable blob bytes: 1,434,017
- Generated OpenFOAM product path findings: 0
- Oversized blobs: 0; largest blob: 123,244 bytes

Exact-token and regular-expression scans found zero occurrences in reachable
blob content for either approved private token category, absolute home paths,
private workspace names, personal email addresses, private keys, GitHub tokens,
common cloud credentials, or password assignments.

The approved `Tim Brewer` public email occurs only in Git author, committer, and
tagger metadata. It does not occur in repository-file content.

`gitleaks` was not installed. Therefore this report does not claim a gitleaks
PASS; it records the explicit scan as PASS and the missing detector as a tooling
limitation.

This audit caused no governing-physics or scientific-configuration change.
