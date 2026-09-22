# Reproduction and evidence locations

Use the task checkout and the owner-retained external artifact roots. The handoff
contains actual absolute paths; these must not be committed. Required inputs:

- BASELINE: accepted 002 `science`, including scenarios, full intervals, input files and logs.
- COUPLED: accepted 003 `science`, including the same records for SW C.
- EXE: accepted 002 parser-corrected `bin/espressoWholePullFoam`.
- TABLES: accepted 003 `tables-qualified`.
- ARTIFACTS: this task's frozen external `science` root.
- OUTPUT: a fresh external analysis directory.

The source/build and table hashes are in FREEZE.json; the original science
executable and accepted corrected build are distinguished in PROTOCOL.md and the
002 POST_RESULT_AMENDMENT.json. Source authority is Puckworks commit
2058d0e947ee9eb92c52d64f6165b810f1fb4732; runtime lock is unchanged.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_md_rheology_004 -v
# Read-only reuse qualification / predecessor metric reproduction:
python3 -m tools.sci_md_rheology_003.analyze --baseline "$BASELINE" \
  --artifacts "$COUPLED" --output "$REPRODUCTION"
# Source the installed Foundation OpenFOAM 12 etc/bashrc before native execution.
# Historical command, ONCE per allowed identity; never replay consumed attempts:
python3 -m tools.sci_md_rheology_004.run --identity "$IDENTITY" \
  --baseline "$BASELINE" --coupled "$COUPLED" --artifacts "$ARTIFACTS" \
  --executable "$EXE" --tables "$TABLES" \
  --audit docs/analysis/sci_md_rheology_004/AUDIT.json
# Reduction is repeatable into a fresh OUTPUT; no native execution:
python3 -m tools.sci_md_rheology_004.analyze --baseline "$BASELINE" \
  --coupled "$COUPLED" --artifacts "$ARTIFACTS" --output "$OUTPUT"
```

Allowed identities are exactly the eight in FREEZE.json. STARTED is fsynced
before invocation; failures consume their attempt and duplicate identities or
existing run directories are refused. No new C/W or predecessor execution.
The freeze was finalized and independently audited before attempts/scoring; do
not regenerate it to reproduce results. Support metadata is written before
metrics. Full raw histories, fields, binaries, property tables and logs remain
external. Committed output is compact derived evidence only.

TR's piecewise-linear table is exact for the accepted law, so its property term
is zero. SW property N uses its own reference alpha and refined observer table.
Observe-mode table viscosity is diagnostic, not the applied constant viscosity.
