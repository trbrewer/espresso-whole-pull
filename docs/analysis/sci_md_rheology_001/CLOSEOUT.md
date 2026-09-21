# PR #150 bounded post-result CI correction

Governance: **G0**, `NO_GOVERNING_PHYSICS_CHANGE` for this correction.
The complete research PR retains `SOURCE_SCENARIO_CHANGE_ONLY`.

The initial live candidate was `1c4d5dff1732b73894e60a611817e64b6c314efe`,
tree `6b14828ec50c752257729e4b4630d7a30e4d2eaf`, on
`research/sci-md-rheology-001`; its worktree was clean. The base was
`ac49fe939f9e7fb38ba4eabc95d65e2fa47ee666`. PR #150 was open.
Required `inexpensive-checks` failed, required `source-and-boundary` passed;
`exact-producer-handoff` also passed. There was no subsequent attempt.

## Cause and bounded correction

[Run 35630604472](https://github.com/trbrewer/espresso-whole-pull/actions/runs/35630604472)
reported one error, no assertion failures: `unittest.loader._FailedTest.test_sci_md_rheology_001`.
`report.py` attempted `from analysis import DOC, ...`; earlier test discovery
had already loaded the repository's unrelated `analysis` namespace package.
Expected: the rheology analysis module. Actual: `ImportError: cannot import
name 'DOC' from 'analysis' (unknown location)`. The runner had the same bare
import. Python resolves an already imported module before searching `sys.path`.
This is a packaging/test-discovery defect, not a numerical assertion failure.
The hosted run executed 1,419 tests, with one error and seven skips.

The failure reproduces at the initial candidate by importing
`analysis.sci_data_fusion_001.audit` before `tests.test_sci_md_rheology_001`,
using Python 3.12.3, NumPy 1.26.4, SciPy 1.11.4 and jsonschema 4.23.0.
Both workflow source-root variables point to the historical Puckworks authority
at `a3428a4d4ad571ef3168a70e8a04620fca5d3520`, with the SCI-MD-012 commit
`2058d0e947ee9eb92c52d64f6165b810f1fb4732` available in that object database.

Report and runner now import `tools.sci_md_rheology_001.analysis` explicitly,
with the repository root on the search path. Existing launchers still work
from outside the checkout. Six new regression tests exercise import ordering,
module identity, all launchers and amendment integrity. The original 23 tests
are unmodified; all 29 focused tests passed in the pinned environment.
No assertions, dependencies, workflows or scientific thresholds were weakened.

## Original authority and evidence reuse

[FREEZE.json](FREEZE.json), [AUDIT.json](AUDIT.json), [AUDIT.md](AUDIT.md),
the original tests and all scientific result artifacts remain byte-identical.
The original accepted pre-result commit is recorded in
[POST_RESULT_AMENDMENT.json](POST_RESULT_AMENDMENT.json). No replacement freeze
was generated. That explicitly **post-result** amendment records the original
and amended SHA-256 for exactly three implementation files. `check_freeze`
verifies that amendment against the original freeze and checks the resulting
file hashes, retaining the original audit, source and runtime-lock checks.
This is the bounded amendment allowed by governance sections 6–9, not a new
scientific attempt or a replacement pre-result approval.

AST comparison against the initial candidate finds every scientific function
unchanged, including mapping, property treatment, profile reduction, local
resistance, reference-only alpha, metrics, numerical estimates and classification.
Only `check_freeze` changes within function bodies; report and runner changes
are import setup. The solver, executable, source data, scenarios, twelve retained
runs and original result bundle are reused. No solver invocation is needed.
A report replay from those retained fields and an exact comparison of outputs
supply the additional numerical reuse check; its final outcome is recorded in
the exact-candidate PR evidence.

The historical [QA.json](QA.json) and [MANIFEST.json](MANIFEST.json) are preserved,
including the earlier full-suite/subset timing. They are not final-candidate
integration evidence. Final complete-suite results, skips, commands, exact
head/tree, required hosted checks and the bounded review addendum are recorded
on [PR #150](https://github.com/trbrewer/espresso-whole-pull/pull/150).

Reproduction commands (external paths supplied by the operator):

```sh
# Python 3.12.3; numpy==1.26.4 scipy==1.11.4 jsonschema==4.23.0
export EWP_POROSITY_PERMEABILITY_PRIOR_PUCKWORKS_ROOT="$PRIOR_ROOT"
export SCI_MD_012_PUCKWORKS_ROOT="$PRIOR_ROOT"
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest tests.test_sci_md_rheology_001 tests.test_sci_md_rheology_001_imports -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/static_validate.py --root .
python3 scripts/verify_source_manifest.py --root .
python3 scripts/verify_v0_1_4_baseline_integrity.py --root . --output "$EVIDENCE/baseline.json"
python3 scripts/verify_governing_physics_change.py --root . --output "$EVIDENCE/boundary.json"
python3 scripts/report_sci_md_rheology_001.py --puckworks "$PUCKWORKS" \
  --runs "$RUNS" --audit docs/analysis/sci_md_rheology_001/AUDIT.json --output "$EVIDENCE/replay"
```

No successor, coupled calculation, merge or new scientific conclusion is
implemented or authorized by this correction.
