# Reproduce

From a clean checkout of the recorded espresso-whole-pull commit:

```bash
python3 scripts/generate_home_lab_evidence_audit.py \
  --output /tmp/home-lab-evidence-audit
diff -ru docs/planning/home_lab_existing_evidence_audit /tmp/home-lab-evidence-audit \
  --exclude HOME_LAB_EVIDENCE_AUDIT.md \
  --exclude REVISED_BRONZE_SEQUENCE.md \
  --exclude REPRODUCE.md
python3 -m json.tool docs/planning/home_lab_existing_evidence_audit/RESULT.json >/dev/null
python3 -m json.tool docs/planning/home_lab_existing_evidence_audit/VISUALIZER_LOCAL_CORPUS_INTEGRITY.json >/dev/null
python3 -m json.tool docs/planning/home_lab_existing_evidence_audit/VISUALIZER_MARGINAL_VALUE.json >/dev/null
```

The three narrative files are reviewed planning documents; all CSV and JSON artifacts are deterministic generator outputs. The generator contains aggregate facts only and does not read or emit raw Visualizer records. If a local store is later restored, use Puckworks' current `visualizer_harvest reconcile` and latest-version readers in a separate authorized rerun; do not overwrite that store or substitute tracked `aggregate_stats.csv` for it.

