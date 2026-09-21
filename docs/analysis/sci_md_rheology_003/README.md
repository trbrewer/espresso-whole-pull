# Reproduction

Run from the EWP task checkout. Use a clean detached Puckworks analysis checkout
at 2058d0e947ee9eb92c52d64f6165b810f1fb4732. Required external artifacts are the
accepted SCI-MD-RHEOLOGY-002 `science` directory with all manifest-bound inputs,
intervals and logs, its accepted corrected executable (SHA256 in FREEZE.json),
and the six task-qualified tables. Do not advance the runtime dependency lock.
Set shell variables to those owner-retained locations:

```sh
# ART: new external task root; PW: clean analysis checkout
# BASELINE: accepted 002 science root; EXE: accepted corrected executable
# OF_BASHRC: installed Foundation OpenFOAM 12 etc/bashrc
source "$OF_BASHRC"
mkdir -p "$ART/bin"
c++ -std=c++11 -O2 tools/sci_md_rheology_002/evaluator.cpp -o "$ART/bin/evaluator"
python3 -m tools.sci_md_rheology_003.export --puckworks "$PW" \
  --output "$ART/tables-qualified" --evaluator "$ART/bin/evaluator"
python3 -m unittest tests.test_sci_md_rheology_003 -v
```

Export refuses existing output directories. Table identities are deterministic;
recompiled evaluator executable identities can differ by build environment and
must be reported honestly. The accepted native scientific executable is reused
by exact hash, rather than relabelling a new executable as identical.

The single prospective freeze was created with:

```sh
python3 -m tools.sci_md_rheology_003.freeze --executable "$EXE" \
  --tables "$ART/tables-qualified" --baseline "$BASELINE" --output "$ART/qualification"
```

This command refuses to replace an existing FREEZE.json. Historical reproduction
uses the committed freeze, not a new freeze. Review receipt AUDIT.json must be a
genuine independent PASS bound to its SHA256, reviewer and reviewed commit.
After the required audit:

```sh
python3 -m tools.sci_md_rheology_003.run --short --artifacts "$ART/short" \
  --baseline "$BASELINE" --executable "$EXE" --tables "$ART/tables-qualified" \
  --audit docs/analysis/sci_md_rheology_003/AUDIT.json
python3 -m tools.sci_md_rheology_003.run --artifacts "$ART/science" \
  --baseline "$BASELINE" --executable "$EXE" --tables "$ART/tables-qualified" \
  --audit docs/analysis/sci_md_rheology_003/AUDIT.json
python3 -m tools.sci_md_rheology_003.analyze --artifacts "$ART/science" \
  --baseline "$BASELINE" --output "$ART/analysis"
```

Each attempt is append-only and counted before invocation. Do not retry a failed
full attempt or rerun in a new root to evade the 24-attempt task ceiling. Analysis
can be repeated into a fresh external output directory without solver invocation.
No scientific campaign runs in ordinary CI. Missing artifacts/environment block
execution, not tooling implementation; no replay or fabricated trajectory.
