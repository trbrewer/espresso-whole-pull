# VAL-CORPUS-002 Stage B2 final-package correction

Authorization `VAL-CORPUS-002-B2-PRODUCTION-SCORING-2026-08-03` permits one
bounded, no-execution reporting and source-lineage correction within
`EWP_PRODUCTION_AND_SCORING_STAGE_V1`.

The following exact-head findings are frozen before derived reporting changes:

- `CUP_MASSES_LINEAGE_CAVEAT_NOT_CARRIED`
- `FINAL_RESULT_SCHEMA_ONLY_TOP_LEVEL_CLOSED`
- `FINAL_STATUS_AMBIGUOUS_WITH_TYPED_FAILURES`
- `EMBEDDED_BASE_RESULT_AUTHORITY_NOT_MARKED`
- `TARGET_AVAILABILITY_SEMANTICS_AMBIGUOUS`
- `FIGURES_ARE_TEXT_ONLY_NOT_SCIENTIFIC_PLOTS`
- `REPORTING_REDUCER_FAIL_CLOSED_HARDENING_REQUIRED`

This correction does not alter any calibration, production, sensitivity,
parity, source, configuration, trace, log, or external execution artifact.
The approved scientific result and every numerical value remain unchanged.

```text
numerical artifacts: UNCHANGED
scientific result: UNCHANGED
OpenFOAM: PROHIBITED
sensitivity rerun: PROHIBITED
refit: PROHIBITED
protected scoring: PROHIBITED
new governing physics: NOT_AUTHORIZED
VAL-CASE-002: NOT_STARTED
merge: NOT_AUTHORIZED
```

The correction may only add the persistent cup-mass lineage authority, carry
that lineage through existing consumers, close and clarify derived machine
records, harden reporting-time verification using already-approved operators,
replace text summaries with deterministic plots, and reconcile current-state
records.

## 2026-08-03 exact-head figure-semantics review

Reviewed head `4765f6fdde10f277c70b4a4b50d5333d58c9f629`, tree
`458af5c6e6ed8c8ca1d80f4d42f30ac467bd869b`, under authorization
`VAL-CORPUS-002-B2-FIGURE-SEMANTICS-CORRECTION-2026-08-03`.

Finding `B2-FIG-001` is
`SCIENTIFIC_FIGURE_SEMANTIC_LEGIBILITY_AND_PLOT_BOUNDS_NOT_CLOSED`.
The three observed manifestations are:

1. overlays or anonymous cells prevent unambiguous experiment/run/series
   identification without consulting JSON;
2. quantitative axes, governed labels, and sensitivity row/column identities
   are incomplete; and
3. plot geometry and long labels are not contained by explicit,
   non-overlapping title, legend, plot, lower-label, axis-title, annotation,
   and caption bands.

This is a reporting-only correction. The frozen P2 rate, 45 production
identities, 27 PASS dispositions, 18 typed target-coverage failures, 21 H1
PASS identities, 9/9 sensitivity result, 1500/1500 parity result, scientific
interpretation, claim ceiling, source evidence, and all numerical/external
artifacts are immutable. OpenFOAM, sensitivity execution, calibration,
refitting, protected scoring, mechanism work, VAL-CASE-002, and merge are
prohibited.

Closure identities, changed generated hashes, qualification results, and the
final correction head/tree will be appended after deterministic regeneration
and qualification. Until then:

```text
review_status: CORRECTION_AUTHORIZED_IN_PROGRESS
merge_status: NOT_AUTHORIZED_PENDING_CORRECTED_EXACT_HEAD_REVIEW
```
