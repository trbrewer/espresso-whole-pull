# Reproduce SCI-MD-003 C1

From this repository root, with the exact accepted Puckworks v5 export named in the pin:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.sci_md_003_atlas run --atlas /path/to/atlas_export.json
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.sci_md_003_atlas verify --atlas /path/to/atlas_export.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_md_003_atlas
```

The run reads retained JSON only. It does not invoke OpenFOAM.
