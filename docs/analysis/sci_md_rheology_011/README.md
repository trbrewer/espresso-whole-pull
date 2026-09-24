# Reproduce SCI-MD-RHEOLOGY-011

Use Python 3.12.3 / NumPy 1.26.4 and the receipt-bound Foundation OpenFOAM 12
runtime. Source its environment, then let the wrapper restore the exact recorded
library/tool paths (including accepted local zlib). `$ART`, `$ACCEPTED` and
`$PUCKWORKS` are external owner-local directories. Raw paths, restricted tables,
meshes, native fields, executable and logs stay outside Git.

```bash
python3 -m tools.sci_md_rheology_011.prepare --artifacts "$ART" --accepted "$ACCEPTED" --puckworks "$PUCKWORKS"
python3 -m tools.sci_md_rheology_011.legacy --artifacts "$ART" --accepted "$ACCEPTED"
python3 -m unittest tests.test_sci_md_rheology_011 tests.test_sci_md_rheology_009 tests.test_sci_md_rheology_008 tests.test_sci_md_rheology_007 tests.test_sci_md_rheology_006
python3 -m tools.sci_md_rheology_011.short --artifacts "$ART"
python3 -m tools.sci_md_rheology_011.prepare --artifacts "$ART" --freeze
```

Short qualification additionally records native initial class inventories and
final field integrals in SHORT_QUALIFICATION.json; this is read-only reobservation
of the same 14 short runs, not an additional integration. COMPATIBILITY.json
records unchanged legacy physics rendering and A adapter parity. The one
independent exact freeze audit must pass before the next commands.

```bash
python3 -m tools.sci_md_rheology_011.run --artifacts "$ART" --stage C --workers 8
python3 -m tools.sci_md_rheology_011.analyze --artifacts "$ART" --stage support
python3 -m tools.sci_md_rheology_011.analyze --artifacts "$ART" --stage primary
# ONLY if PRIMARY.json reports MATERIAL_ARRANGEMENT_CONTRAST_CONDITIONAL_E2_REQUIRED:
python3 -m tools.sci_md_rheology_011.run --artifacts "$ART" --stage E2 --workers 4
python3 -m tools.sci_md_rheology_011.analyze --artifacts "$ART" --stage analyze
python3 -m tools.sci_md_rheology_011.plot --artifacts "$ART"
python3 -m tools.sci_md_rheology_011.layout
```

Support/primary seals are immutable. The E2 launcher checks both their hashes
and ledger order. Completed attempts are reverified, never automatically rerun.
Failures and preparation failures remain in ATTEMPTS.jsonl; infrastructure retry
requires demonstrated interruption and identical scientific inputs within the
two-attempt allowance. No numerical rescue. Do not run historical preparation
or integration commands to recover missing reference artifacts.

Historical A is exactly 18 009 C traces; no historical support is changed.
This is computational numerical qualification, not experimental validation.
Final exact-head independent review and hosted CI are separate dispositions.

The final layout-only redraw moves overlapping area labels into a legend. It
was added after scoring; frozen preparation, native evidence, scoring code,
thresholds and support/primary seals are unchanged.
