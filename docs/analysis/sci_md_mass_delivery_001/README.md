# Run the thin research consumer

Use an explicit Puckworks checkout at the revision recorded in HANDOFF.json.
Create the checkout at a destination you choose, with NumPy/SciPy available:

```bash
git clone https://github.com/trbrewer/puckworks "$PRODUCER"
git -C "$PRODUCER" checkout --detach d59cec8ab8314e2697837c6752d296d20f4dc370
python3 scripts/research_mass_delivery.py --producer "$PRODUCER" --stop-kg 0.04
python3 -m unittest discover -s tests -p test_research_mass_delivery.py
```

`PRODUCER` is the explicit checkout destination, not the production dependency.
The command validates its commit/tree, kernel and artifact hashes, SI units,
identity and supported domain. Queries are synthetic requested intervals and a
mass-only stopping request; the fitted artifact is source-specific. Outputs
include conditional-use, source and rights labels. It predicts no elapsed time,
pressure or flow. An unsupported stop mass raises an error.

Canonical implementation, fit/predict/score runner, synthetic example, model
artifacts and complete scientific result belong to Puckworks. The handoff binds
the producer revision separately from later result-record commits, avoiding a
self-referential manifest. EWP contains no numerical-kernel copy and does not
change `dependencies/puckworks.lock.json`.

See [RESULT.md](RESULT.md) for condition failures and [HANDOFF.json](HANDOFF.json)
for source-specific identity and claim limits. Source-derived model/result
artifacts retain CC-BY-NC-3.0, Pannusch/Schmieder, Mendeley
[10.17632/y2tz67f6ry.1](https://doi.org/10.17632/y2tz67f6ry.1); they are not MIT.
Physical validation remains NOT_ESTABLISHED. No automatic successor.
