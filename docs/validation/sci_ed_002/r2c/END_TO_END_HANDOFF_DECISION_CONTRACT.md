# End-to-end handoff decision

One decision function serves the production CLI and tests. Exact PASS requires every stage. Vendored-only is limited. Production authority pins have no CLI or environment override. Output is atomically replaced, including structured failure output, so stale PASS evidence cannot survive rejection.
