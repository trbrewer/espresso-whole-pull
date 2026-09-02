# Reproduction

Run only after an independent audit record passes the exact-head, exact-tree, and freeze-content-manifest checks:

```sh
python3 -m analysis.sci_data_fusion_001.run execute --root . --puckworks-root "$EWP_SCI_DATA_FUSION_001_PUCKWORKS_ROOT" --output docs/analysis/sci_data_fusion_001 --audit-record /path/to/audit.json
```

Required EWP base: `2bf996596bb7408c2b5e2fc1eb0f7a65e5f5bae2` / `3a3565f8bab605ed706f5ce51bbfed4de039d46b`.
Required Puckworks authority: `2058d0e947ee9eb92c52d64f6165b810f1fb4732` / `a6ffb312473b15be43c1571a893b19873ea47c5a`.

Verify with `verify-freeze`, run the focused and full Python lanes, and use `scripts/replay_sci_data_fusion_001_freeze.py` for deterministic immutable-package replay. Results are written under `docs/analysis/sci_data_fusion_001/`. OpenFOAM and laboratory work are neither required nor authorized.
