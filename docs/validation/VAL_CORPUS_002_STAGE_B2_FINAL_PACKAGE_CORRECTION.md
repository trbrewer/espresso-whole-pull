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
