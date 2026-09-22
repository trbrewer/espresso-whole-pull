# Reproduction

Use a clean EWP checkout and explicit external artifact locations. Runtime
fields, meshes, logs, tables and executables remain outside Git. The external
handoff supplies owner-local paths; committed receipts bind their hashes.

- ART: this task's external artifact root (science child bound in FREEZE).
- BASELINE: accepted 002 science; COUPLED: accepted 003 science.
- CONTEXT: accepted 004 science; PW: clean analysis checkout at 2058d0e.
- ACCEPTED_TABLES: qualified 003 table directory.
- BASE_EXE: accepted parser-corrected 002 executable (9dea02fc…).

Build copied solver source with Foundation OpenFOAM 12 and task-local
FOAM_USER_APPBIN. Use the exact frozen executable for reproduction of these
attempts; a new environment's binary hash is not silently equivalent.

```sh
python3 -m unittest tests.test_sci_md_rheology_005 -v
python3 -m tools.sci_md_rheology_005.short --output "$ART/short" \
  --executable "$ART/bin/espressoWholePullFoam" --baseline "$BASE_EXE"
# Historical pre-execution command; refuses an existing freeze:
python3 -m tools.sci_md_rheology_005.prepare --artifacts "$ART" \
  --baseline "$BASELINE" --coupled "$COUPLED" --context "$CONTEXT" \
  --puckworks "$PW" --accepted-tables "$ACCEPTED_TABLES"
```

The accepted freeze must not be regenerated after scoring. One actual
independent PASS audit binds its hash. After audit, the historical full command
was invoked once for each identity in FREEZE.full_matrix, C controls first:

```sh
python3 -m tools.sci_md_rheology_005.run --identity "$IDENTITY" \
  --artifacts "$ART/science" --executable "$ART/bin/espressoWholePullFoam" \
  --tables "$ART/tables"
```

Completed identities are not replayed. A documented nonsemantic failed slot
can use --recovery-reason within the four-attempt reserve; changed science is
not authorized. The ledger is appended/fsynced before launch and failures are
retained. No recovery was used. Missing accepted evidence blocks its comparison;
it does not authorize replacement campaigns.

Analysis is repeatable into a new external output directory without native runs:

```sh
python3 -m tools.sci_md_rheology_005.analyze --artifacts "$ART/science" \
  --baseline "$BASELINE" --coupled "$COUPLED" --context "$CONTEXT" --output "$OUTPUT"
python3 -m tools.sci_md_rheology_005.plot --artifacts "$ART/science" --output "$OUTPUT"
python3 scripts/validate_sci_md_rheology_005.py --root .
```

The observer/metrics come from frozen source. Plots consume native histories and
metrics; plotting never supplies score samples. Numeric JSON contains every
paired set and separate empirical-allowance contribution. Historical 004 N/W
remains context only, with frozen alpha; no G calibration.

Maintained generation accepts `aggregate_viscosity: {mode: bulkCoupled,
 table: EXTERNAL_TABLE, purpose: scientific}`. Native dictionary uses
`aggregateViscosityMode bulkCoupled`. See PROTOCOL for supported configurations,
lag timing, diagnostics and exact units. C/W/N interval columns retain their
historical meaning. In G only, Q_cont is applied bulk flow; mu extrema/dilute
fractions are counterfactual local-law diagnostics. The G companion trace carries
applied mu and its actual stored-mass input explicitly.
