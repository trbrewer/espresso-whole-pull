# Reproduce or inspect SCI-MD-RHEOLOGY-010

Use accepted Foundation OpenFOAM 12, Python 3.12.3 and NumPy 1.26.4.
Resolve external ART010, ART009 and PUCKWORKS_SOURCE using the retained private
receipts; no raw native products or source tables belong in this checkout.
The actual executable is the retained 009 `bin/espressoWholePullFoam`, SHA256
`3de93829850829db53927e5a079a855d1c09922f238a3a330f5d01f32f9eb1fb`.
It is used in place, with no rebuild. `LOCATIONS.json` records its private path.
Source OpenFOAM's environment first; the wrapper restores receipt-bound solver
library resolution (including accepted zlib) ahead of the auxiliary tool paths.

The following documents the completed preparation sequence, not permission to
overwrite its immutable freeze or launch duplicate runs:

```bash
source "$OPENFOAM_BASHRC"
python3 -m tools.sci_md_rheology_010.prepare --artifacts "$ART010" --accepted "$ART009" --puckworks "$PUCKWORKS_SOURCE"
python3 -m unittest tests.test_sci_md_rheology_010 tests.test_sci_md_rheology_009 tests.test_sci_md_rheology_008 tests.test_sci_md_rheology_007 tests.test_sci_md_rheology_006
python3 -m tools.sci_md_rheology_010.short --artifacts "$ART010"
RHEOLOGY010_ARTIFACTS="$ART010" python3 -m unittest tests.test_sci_md_rheology_010
python3 -m tools.sci_md_rheology_010.prepare --artifacts "$ART010" --freeze
```

A genuine independent reviewer must inspect and approve that exact freeze before
full execution. The audit is agent scientific review, distinct from protected
GitHub approval or external human review. Then execute the declared sequence:

```bash
python3 -m tools.sci_md_rheology_010.run --artifacts "$ART010" --stage C --workers 8
python3 -m tools.sci_md_rheology_010.analyze --artifacts "$ART010" --stage support
python3 -m tools.sci_md_rheology_010.run --artifacts "$ART010" --stage E2 --workers 4
python3 -m tools.sci_md_rheology_010.analyze --artifacts "$ART010" --stage analyze
python3 -m tools.sci_md_rheology_010.plot --artifacts "$ART010"
```

Workers execute independent serial cases; MPI is only the declared short fixture.
Incidental elapsed times are not benchmarks. Completed native slots are verified
by full retained manifests before reuse. An actual-launch ledger includes every
solver/MPI invocation and keeps preparation failures separate. Failed native
attempts never retry automatically. Infrastructure-only recovery requires an
explicit evidence-bound record, unchanged configuration/executable and the global
two-attempt reserve; numerical failures cannot consume that reserve.

To verify retained identities without native execution:

```bash
python3 - "$ART010" <<'PY'
import sys
from pathlib import Path
from tools.sci_md_rheology_010.common import verify
verify(Path(sys.argv[1]), frozen=True, audited=True)
PY
```

Historical 009 evidence is never written. The new common support and scores are
010 comparisons. PHYSICAL_VALIDATION = NOT_ESTABLISHED. No merge or successor.

The separately authorized sectioning diagnostic is applied only after retained
base fields exist; it is not in the scientific acceptance freeze:

```bash
python3 -m unittest tests.test_sci_md_rheology_010_sections
python3 -m tools.sci_md_rheology_010.sections --artifacts "$ART010"
```

[SECTIONING.md](SECTIONING.md) defines compartment semantics, actual mesh/partial
cell treatment, E2 spatial-resolution limits and source-specific assay gaps.
The diagnostic consumes only stored final fields, and historical E2 is labeled.

After scoring and sectioning, format the complete decision tables and publish
the run-accounting projection (private command/error text stays in the immutable
external ledger; hashes, statuses and all counts are retained):

```bash
python3 -m tools.sci_md_rheology_010.report
```
