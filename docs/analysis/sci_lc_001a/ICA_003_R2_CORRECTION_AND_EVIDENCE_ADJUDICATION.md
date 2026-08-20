# ICA-003 R2 correction and evidence adjudication

Authorization: `SCI-LC-001A-ICA-003-R2-F01-F03-BOUNDED-CORRECTION-AND-EVIDENCE-ADJUDICATION-2026-08-17`.
The R2 review examined HEAD `e8e73f9f163bdc72d41e2c52f2a07cdc31de0bb6`
and tree `c7be0e779d471dd7740b5820cb019a27e17fcdf2`.

## Owner path adjudication (ICA003-R2-F01)

The earlier authorization incorrectly named nonexistent top-level files
`SCI_LC_001A_PARAMETER_MATRIX.json` and `SCI_LC_001A_PROTOCOL.json`. The actual
canonical generated files are
`validation/cases/sci_lc_001a/SCI_LC_001A_PARAMETER_MATRIX.json` and
`validation/cases/sci_lc_001a/SCI_LC_001A_PROTOCOL.json`. The top-level names do
not exist. The owner ratifies only these two actual canonical generator outputs
for this bounded work. The historical literal-path discrepancy remains visible;
no other path is ratified.

## Canonical classification integrity (ICA003-R2-F02)

Canonical publication starts only at an authorized run root. It reloads and
validates the run manifest, exact repository and generated authority, frozen
3,666-key plan, result checksum ledger, and each eligible `COMPLETE` real Stage-A
result. An actual ledger-bound executed result is required for every published
`BASE` classification. Architecture, scope, case, profile, row hash, backend,
evidence kind, ordinary classification, qualified classification, scientific
admissibility, and canonical status are derived rather than caller assertions.

The public record builder and low-level serializer are permanently synthetic,
test-only mechanisms. They cannot claim canonical status. Canonical publication
validates the complete record set before atomically installing the single
`classifications` directory. Failed validation leaves no canonical JSONL,
summary, report, ledger, or completion marker. Summary and report generation
consume validated classifications and never reclassify raw results.

## Historical evidence adjudication (ICA003-R2-F03)

A bounded provenance search covers the immutable correction bundle, its named
command paths, lane-specific directories below the external SCI-LC-001A run root,
and clearly lane-named surviving temporary paths. If the original intermediate
full-suite stdout and stderr are not recoverable with provenance, the status is
`ORIGINAL_RAW_LOGS_IRRECOVERABLE_AFTER_BOUNDED_PROVENANCE_SEARCH`. That gap
remains permanently visible: it is an evidence-retention deficiency, not proof
that later exact-head reruns were invalid. Every material command in this lane
retains raw stdout, raw stderr, timing, exit status, and hashes for forward
adjudication.

## Continuing authority boundary

The narrower accurate change statement is
`NO_PHYSICS_BEARING_SOLVER_CASE_OR_NUMERICAL_AUTHORITY_BEHAVIOR_CHANGED`.
Stage-A scientific execution remains unauthorized. D4 and X1 remain deferred
and unauthorized; robustness and bistability remain unadjudicated; physical
validation is not established. This implementation and owner adjudication are
pending an independent read-only R3 exact-head review.
