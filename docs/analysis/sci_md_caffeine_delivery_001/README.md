# Caffeine research consumer

SCI-MD-CAFFEINE-DELIVERY-001. [Protocol](PROTOCOL.md), [model card](MODEL_CARD.md),
[exact handoff](HANDOFF.json). Puckworks #289 / EWP #195.
G1 / NO_GOVERNING_PHYSICS_CHANGE. PHYSICAL_VALIDATION=NOT_ESTABLISHED.

Use an isolated checkout at HANDOFF.json's exact producer_commit, with an existing
NumPy/SciPy environment. The thin consumer checks its commit/tree, all runtime and
model file hashes, model content hashes and immutable 006 parent identity. It
loads the explicit producer files without using an installed Puckworks fallback.
The production dependency lock/defaults/physics remain unchanged.

```bash
python scripts/research_conditional_caffeine_delivery.py --producer "$CAFFEINE_PRODUCER" --synthetic
python scripts/research_conditional_caffeine_delivery.py --producer "$CAFFEINE_PRODUCER" \
  --arm S2 --early-inputs "$EARLY_INPUTS" --queries "$QUERIES" --output "$PRIVATE_OUTPUT"
SCI_MD_CAFFEINE_DELIVERY_001_PRODUCER="$CAFFEINE_PRODUCER" \
  python -m unittest discover -s tests -p test_research_conditional_caffeine_delivery.py
```

Early input schema has explicit kg and kg/kg units, mass basis, input class and
named fields m1_kg/m2_kg/q1/q2 for share arms. D0 accepts m1_kg/m2_kg only.
Queries contain only start_kg/end_kg. Caffeine targets and later TDS are forbidden
query fields. Optional --stop-kg computes modeled remaining caffeine from the
anchor to that specified mass. Zero intervals return zero mass and undefined
concentration. Extrapolation is explicitly flagged as diagnostic.

Output kg, mg, mg/g and numerical allowances describe modeled interval delivery.
They do not establish analytical uncertainty, measured whole-cup or whole-suffix
caffeine, physical chemistry closure or transfer to another coffee/apparatus.
S1 indirectly uses early TDS through C2. Caffeine is a component of TDS; it is
never added to EWP total-solute/density/viscosity/extraction terms.
SOURCE_INTERNAL / TARGET_EXPOSED /
RETROSPECTIVE_CAMPAIGN_SEPARATED_CONDITIONAL_PREDICTION.
Source-derived model artifacts retain Pannusch/Schmieder Mendeley
10.17632/y2tz67f6ry.1, CC-BY-NC-3.0 separately from software licensing.
MERGE_AUTHORIZED=false; PRODUCTION_ADOPTION_AUTHORIZED=false;
NATIVE_EWP_RUNS=0; NO_SUCCESSOR_AUTHORIZED.
