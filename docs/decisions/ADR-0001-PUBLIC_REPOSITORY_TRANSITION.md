# ADR-0001: Public Repository Transition

- Status: Accepted
- Date: 2026-07-28
- Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`

## Decision

Development moves to `espresso-whole-pull` with clean public history. The root is a sanitized derivative tagged `v0.1.4-public.1`, not an exact-byte publication of the private archive.

Five historical files had host/path strings replaced deterministically. One packaging tool was adapted to separate the fixed 106-file source scope from public governance and CI metadata. Scientific inputs, equations, configuration, calibration, numerical schemes, and thresholds are unchanged.

Puckworks remains an external locked dependency without a submodule. Full OpenFOAM runs remain manual and release-gated.

## Consequences

The public aggregate differs from the archival aggregate. Both identities and the derivation proof are retained. Exact archival bytes remain offline and never enter public Git history.
