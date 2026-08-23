# Reproduce

With the exact artifact in `PUCKWORKS_ANALYSIS_PIN.json`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.sci_md_003_atlas run --atlas /path/to/atlas_export.json
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.sci_md_003_atlas verify --atlas /path/to/atlas_export.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_md_003_atlas -v
```

No OpenFOAM command is used.
