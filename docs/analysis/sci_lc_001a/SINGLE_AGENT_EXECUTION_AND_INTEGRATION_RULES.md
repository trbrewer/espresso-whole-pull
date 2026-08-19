# SCI-LC-001A single-agent execution and integration rules

Exactly one mutating agent and one family controller are permitted. Autonomous
retry, a second launcher, and concurrent shared-metadata writers are forbidden.
Independent review is sequential and read-only; an author may not certify
independence.

Every attempt transition requires an OS-level exclusive lock and an immutable
authority-bound reservation. Prose alone cannot launch. The family hold is
checked before allocation, reservation, root creation, unit generation,
service launch, first and subsequent dispatch boundaries, retry, replacement,
resume, recovery, classification, and publication. Any code, configuration,
matrix, diagnostic, launcher, or authority change invalidates exact-head
review and owner authority.

Attempt lineage is append-only. Attempts 01--03 are quarantined and cannot be
reused, resumed, replayed, imported, or combined. No silent replacement is
allowed, and Attempt 05 requires new explicit owner authority.

The controller owns authoritative terminalization for normal completion,
failure, signals, systemd stop, supervisor loss, and pre-dispatch abort. A
terminal manifest overrides stale lease text, but a live process must never be
silently relabeled stale. Liveness requires PID plus OS start time, executable,
command digest, working directory, unit, attempt, root, and authority identity.

Emergency containment first sets/preserves the family hold, positively
identifies the exact process and owning service, uses the owning systemd stop
path when applicable, then SIGINT/SIGTERM only if needed. Evidence is preserved
and terminalization verified. Quarantined roots are read-only and never edited.

SCI-ED serializes shared metadata first. Integration uses normal descendant
commits and history-preserving merges; no rebase, squash, force push, amendment,
or branch-protection bypass is permitted. Closure requires terminal manifests,
closed leases, immutable evidence, archived hashes, accurate GitHub state, and
explicit authority for every merge or branch cleanup.
