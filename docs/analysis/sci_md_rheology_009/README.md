# Reproduce SCI-MD-RHEOLOGY-009

Use Foundation OpenFOAM 12 and the accepted Python environment (Python 3.12.3,
NumPy 1.26.4). Set external `$ART`, `$C_ACCEPTED`, `$E_ACCEPTED`, and `$PUCKWORKS`
to receipt-bound directories; never place runtime artifacts in Git.

```bash
source "$OPENFOAM_BASHRC"
mkdir -p "$ART/bin"
FOAM_USER_APPBIN="$ART/bin" wmake solver/espressoWholePullFoam > "$ART/build.log" 2>&1
python3 -m tools.sci_md_rheology_009.prepare --artifacts "$ART" --accepted "$C_ACCEPTED" --accepted-e "$E_ACCEPTED" --puckworks "$PUCKWORKS"
python3 -m unittest tests.test_sci_md_rheology_009 tests.test_sci_md_rheology_008 tests.test_sci_md_rheology_007 tests.test_sci_md_rheology_006
python3 -m tools.sci_md_rheology_009.short --artifacts "$ART"
python3 -m tools.sci_md_rheology_009.reject --artifacts "$ART"
python3 -m tools.sci_md_rheology_009.prepare --artifacts "$ART" --freeze
```

Stop for the required independent pre-scoring audit of the exact freeze.
A missing/failed audit blocks the following commands. The reference-only support
command executes the frozen rule; it cannot choose a new rule or E2 endpoint.

```bash
python3 -m tools.sci_md_rheology_009.run --artifacts "$ART" --stage control
python3 -m tools.sci_md_rheology_009.run --artifacts "$ART" --stage regression
python3 -m tools.sci_md_rheology_009.analyze --artifacts "$ART" --stage compatibility
python3 -m tools.sci_md_rheology_009.run --artifacts "$ART" --stage C
python3 -m tools.sci_md_rheology_009.analyze --artifacts "$ART" --stage support
python3 -m tools.sci_md_rheology_009.run --artifacts "$ART" --stage E2
python3 -m tools.sci_md_rheology_009.analyze --artifacts "$ART" --stage analyze
python3 -m tools.sci_md_rheology_009.plot --artifacts "$ART"
```

Completed slots are hash-verified before reuse. Failed starts are preserved.
The executor fails closed on a failed slot: infrastructure recovery requires
recorded identical configuration and remaining four-attempt budget; scientific
or numerical failure cannot be recovered by changing inputs.
Historical accepted evidence and defaults remain unchanged. Final figures and
result are generated only if the corresponding qualified evidence is available.

The sequence above records preparation of a fresh experiment. Committed freeze
and support records are immutable: do not overwrite them to replay qualification.
For the retained receipt-bound artifacts, verify all identities without rerunning:

```bash
python3 - "$ART" <<'PYTHON'
import sys
from pathlib import Path
from tools.sci_md_rheology_009.common import verify
verify(Path(sys.argv[1]), 'FREEZE.json', audit=True)
PYTHON
```

Full execution in this task used independent serial cases concurrently (up to
eight C workers), and short MPI used two ranks across the radial interface.
The sequential commands above produce the same per-case configuration; timing
comparisons across these incidental launch schedules are not benchmarks.
