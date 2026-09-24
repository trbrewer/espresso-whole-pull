# Reproduce the retained-field diagnostic

Use the exact Puckworks analysis identity in ANALYSIS_SOURCE.json, separately
from the unchanged production Puckworks lock. ART010 is the configured retained
RHEOLOGY-010 artifact directory; its private LOCATIONS.json locates 009. Only the
16 retained 30-second base C/E2 cases in CONTRACT.json are eligible.

```bash
python -m unittest tests.test_sci_md_radial_obs_001
python -m tools.sci_md_radial_obs_001.prepare --artifacts "$ART010"
python -m tools.sci_md_radial_obs_001.observe --artifacts "$ART010" --puckworks "$PUCKWORKS_ANALYSIS"
python -m tools.sci_md_radial_obs_001.report
```

Python requires NumPy; rendering additionally needs matplotlib. Source replay
runs separately in Puckworks and needs openpyxl. None of these commands prepares,
builds or executes a native case. `prepare` only verifies retained ledger and file
hashes. `observe` enforces the independent audited freeze, source module identity,
field/mesh/scenario/trace hashes, historical three-region parity, dimensions,
bounds and inherited mass checks before using each pair of synthetic cuts.
Missing or invalid cases remain named partial results, never regenerated.

The three figures and RESULT.json report conditional computational quantities.
They do not compare experiments with these different coffees, geometry, pressure
histories or 30-second endpoints. Both VST and Sworks formula conventions are
retained, including their distinct denominators. The illustrated recovery and
pore-solute survival assumptions are not measured. Source reconstruction and its
rights/provenance are owned by the linked Puckworks task.

RHEOLOGY-008 qualified its native reduction; 009 and 010 govern their named
output transfer tests. Their accepted results are unchanged. #171 remained
OPEN/UNMERGED at task start; its full conditional E2 was not run and is not in
this diagnostic. Its delivery null is not hydraulic invariance. No new spatial
accuracy/transfer pass or failure can be inferred from base snapshots alone.

PHYSICAL_VALIDATION=NOT_ESTABLISHED; NEW_NATIVE_INTEGRATIONS=0;
NEW_NATIVE_BUILDS=0; PRODUCTION_DEFAULTS_AND_LOCK=UNCHANGED. Both task PRs remain
open/unmerged; no successor or native campaign.

Source reconstruction: [Puckworks PR #266](https://github.com/trbrewer/puckworks/pull/266).
