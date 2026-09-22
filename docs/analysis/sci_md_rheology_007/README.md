# Reproduction

Use the accepted external 006 root (`C_ART`), new 007 root (`ART`), read-only
accepted Puckworks analysis checkout (`PW`) and Foundation OpenFOAM 12 environment.
Machine-local paths are retained in external LOCATIONS.json. Accepted root identity
is hash-bound by 006 FREEZE.json; executable, tables, full cases and intervals by
006 RUNS.json and its external CASE_FILE_MANIFESTS.json. No restricted inputs,
binaries, raw fields or logs are distributed in Git.

```sh
# Historical preparation, before the immutable freeze:
python3 -m tools.sci_md_rheology_007.prepare --artifacts "$ART" \
  --accepted "$C_ART" --puckworks "$PW"
python3 -m tools.sci_md_rheology_007.short --artifacts "$ART"
python3 -m unittest tests.test_sci_md_rheology_007 -v
python3 -m tools.sci_md_rheology_007.prepare --artifacts "$ART" --freeze
# Independent G1 audit must bind this exact freeze before execution:
python3 -m tools.sci_md_rheology_007.run --artifacts "$ART"
# Complete interval-based reduction and unsmoothed figures:
python3 -m tools.sci_md_rheology_007.analyze --artifacts "$ART" \
  --accepted "$C_ART" --output "$OUT"
python3 -m tools.sci_md_rheology_007.plot --artifacts "$ART" \
  --accepted "$C_ART" --output "$OUT"
```

The runner accepts `--slot` for a declared matrix slot and `--recovery-reason`
only after terminal failure in that slot. Completed slots are hash-verified and
reused; no overwrite or new task label for C. Full raw file manifests live in
science/INVOCATIONS.jsonl. Public RUNS.json carries the ledger and manifest hashes.
The frozen 28 full slots, six short slots and four recovery reserve are not a
reproduction authorization for another campaign. Frozen preparation refuses a
replacement freeze; any material pre-score correction must remain documented.

P is a derived representation with times in seconds, Q in m3/s, volumes in m3,
masses in kg, share dimensionless and TDS discrepancies in percentage points.
Native flux applies over [start,end]; viscosity uses the beginning-of-step state;
remaining inventory, dissolved storage and native cumulative delivery are end
states. Preserve every native increment including the zero-mass origin. The
004 comparator's first label C maps to P here, and its second label R maps to
reference C; denominator is therefore reference C. Zero-mass TDS is undefined.

50-digit Decimal independently recomputes from the exact represented binary64
native values. Only an endpoint excess <=1e-14 kg caused by floating summation
can snap to a terminal Decimal breakpoint; this is the inherited arithmetic mass
floor, not extended physical support. Its discrepancy enters u_arithmetic.

See [protocol](PROTOCOL.md), [freeze](FREEZE.json), [reuse](REUSE.json),
[compatibility](COMPATIBILITY.json) and [short fixtures](SHORT_CHECKS.json).
Physical validation remains NOT_ESTABLISHED. No production/default/lock changes,
Puckworks write, adoption, merge, laboratory action or successor.
