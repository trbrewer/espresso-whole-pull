# Empirical transfer research handoff

SCI-MD-MASS-DELIVERY-004; G1 / NO_GOVERNING_PHYSICS_CHANGE.
The [producer protocol](https://github.com/trbrewer/puckworks/blob/research/sci-md-mass-delivery-004/docs/analysis/sci_md_mass_delivery_004/PROTOCOL.md)
fixes the ten FIT conditions, five arms and axes A–E. ANCHORED_EMPIRICAL is
primary only for 004; predecessor candidates/results remain unchanged.

HANDOFF.json keeps the accepted 003 numerical runtime pin and all three transitive
runtime files, with unchanged 001 MASS/EMPIRICAL model bytes. Evaluation code and
qualification have separate identities. The old consumer's complete three-model
manifest is retained for compatibility; SETTING_EMPIRICAL is not an arm or a new
004 qualification. No second predictor or production dependency change.

Create an explicit producer checkout at producer_commit in HANDOFF.json. Set
PRODUCER to that checkout. With NumPy and SciPy:

```bash
python3 scripts/research_anchored_mass_delivery.py --producer "$PRODUCER" \
  --handoff docs/analysis/sci_md_mass_delivery_004/HANDOFF.json --model EMPIRICAL
python3 scripts/research_anchored_mass_delivery.py --producer "$PRODUCER" \
  --handoff docs/analysis/sci_md_mass_delivery_004/HANDOFF.json --model MASS
python3 -m unittest discover -s tests -p 'test_research_*mass_delivery.py'
```

Both examples are SYNTHETIC_ANCHOR_INPUT, never reproductions of source shots.
The existing isolated loader verifies exact commit/tree/files, units, support,
rights and transitive numerical imports, with no installed fallback. Previous
003 behavior and consumer regression tests are unchanged.

Qualified use can only concern tested source regimes, measured fraction-1 TDS
and mass, and supplied supported future mass intervals. No universal grinder
mapping, recipe-only prediction, mass/time attainment, real-time controller,
identified inventory, independently validated physics or production adoption.
Source-derived artifacts retain Pannusch/Schmieder, CC-BY-NC-3.0,
DOI 10.17632/y2tz67f6ry.1; first-party software licensing remains separate.
Native EWP runs=0; production defaults and dependency lock unchanged;
PHYSICAL_VALIDATION=NOT_ESTABLISHED; MERGE_AUTHORIZED=false; NO_SUCCESSOR_AUTHORIZED.
