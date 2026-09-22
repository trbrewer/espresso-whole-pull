# SCI-MD-RHEOLOGY-008 regeneration

Use the accepted 007 external artifact root (`P_ART`), the new task root (`ART`)
and Foundation OpenFOAM 12 environment. Accepted `P_ART/LOCATIONS.json` resolves
C and read-only Puckworks; their frozen location/manifest hashes must match.
`ART/LOCATIONS.json` records local locations externally. No private path, source
table, binary, raw field or full log is distributed here.

Historical preparation and qualification commands (not authorization for a second
campaign):

```sh
python3 -m tools.sci_md_rheology_008.prepare --artifacts "$ART" --accepted-p "$P_ART"
python3 -m unittest tests.test_sci_md_rheology_008 -v
python3 -m tools.sci_md_rheology_008.short --artifacts "$ART"
python3 -m tools.sci_md_rheology_008.prepare --artifacts "$ART" --freeze
# An actual independent audit must bind the freeze before full execution.
python3 -m tools.sci_md_rheology_008.run --artifacts "$ART"
```

The existing task's exact summaries and figures regenerate read-only from retained
native evidence (use a separate `OUT` directory for verification):

```sh
python3 -m tools.sci_md_rheology_008.analyze --artifacts "$ART" --output "$OUT"
python3 -m tools.sci_md_rheology_008.plot --artifacts "$ART" --output "$OUT"
```

The full runner accepts `--slot` and `--recovery-reason` only for a declared slot
with recorded terminal failure. Complete slots are reused only after file hash
verification. A STARTED slot without terminal status must be investigated; it is
never automatically relaunched. Ceilings are 42 science slots / 46 attempts and
12 short slots / 14 attempts. Retain original failures and configurations.

PREPARATION.original.json and original short-invocation.log retain the short QA
failure; PRE_FREEZE_CORRECTION.json describes its nonsemantic correction. The
requalification reused all 12 completed native cases. PREPARATION.json records
the corrected pre-science tooling. No native rerun or outcome score was involved.
TEST_IMPORT_CORRECTION.json records a discovery-only test import fix.
AUDIT_CORRECTION.json records the independent auditor’s support-edge fix; original
pre-audit freezes remain external. Neither changed the protocol, matrix, support
or thresholds, and no science run had started. The single audit binds the final
freeze and these corrections.

The initial unit-test exact-equality failure for binary64 dose reconstruction is
also recorded; its assertion now uses 15-place equality.

Native time intervals include the first interval and use beginning-step viscosity.
Q is m3/s, volume m3, water/solute/inventory kg, concentration kg/m3, share a
fraction. E histories are native full-basket radial totals, without extra weights.
Only historical P constituents use .25/.75 weighting once. Native clock matching
is exact; tolerant final-directory lookup handles floating time-directory labels.
B=W+S starts at zero, and fraction TDS is 100 deltaS/deltaB in percent. Metrics
with E_ prefix are fractional discrepancies; D_ metrics are percentage points.

Independent Decimal uses 50 digits and the exact represented binary64 native
inputs. It recomputes both native shares and cumulative increments, mass
breakpoints and conservative splits without P constituent composition. Inherited
endpoint arithmetic roundoff floor is 1e-14 kg; physical support never shrinks or
extends. Every candidate has fresh time/axial/C-radial/property/arithmetic terms;
inter-candidate E differences are not numerical allowances.

SUPPORT.json is frozen input, copied from exact 007 values. COVERAGE.json adds E
terminal masses without changing that input. METRICS.json gives all 72 decisions,
components, raw variant metrics and support failures. RUNS.json is a sanitized
projection of the complete external durable ledger; its file-manifest hashes
bind external raw fields and logs. QUALIFICATION.json records native gate status.
A failed native gate is inadmissible evidence, not a scientific reduction failure.

PHYSICAL_VALIDATION: NOT_ESTABLISHED. Computational reference comparison only;
no merge, adoption, production/default change or automatic successor.
