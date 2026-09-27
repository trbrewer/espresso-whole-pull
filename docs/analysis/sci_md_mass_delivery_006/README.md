# Learned tail delivery research consumer

SCI-MD-MASS-DELIVERY-006. G1 / NO_GOVERNING_PHYSICS_CHANGE.
[EWP issue #193](https://github.com/trbrewer/espresso-whole-pull/issues/193);
[Puckworks issue #287](https://github.com/trbrewer/puckworks/issues/287).

The changed question learns early-to-late interval delivery from all 45 FIT
shots, including the 30 former FIT-transfer comparison shots reclassified as
training for this task only. The fixed C2 primary uses two early assays; C0
uses measured early masses and C1 adds only the first assay. Five logit hats,
four lambdas and three deterministic starts are predeclared. No per-query fit
or rate inversion. 005's rejection and all 001–005 artifacts remain unchanged.

This thin consumer loads the exact evaluated Puckworks commit/tree and model/
runtime hashes in HANDOFF.json. It copies no predictor and changes no production
dependency lock. The runtime identity is separate from later publication commits.

```bash
python3 scripts/research_conditional_tail_delivery.py --producer "$PRODUCER" --synthetic
python3 scripts/research_conditional_tail_delivery.py --producer "$PRODUCER" \
  --arm C2 --early-inputs "$EARLY_JSON" --queries "$QUERY_JSON" \
  --stop-kg 0.04 --output "$PRIVATE_OUTPUT_JSON"
SCI_MD_MASS_DELIVERY_006_PRODUCER="$PRODUCER" \
  python3 -m unittest discover -s tests -p 'test_research_conditional_tail_delivery.py'
```

Early input JSON has `arm`, `values`, `input_class`, `mass_unit`,
`concentration_unit`, `basis`. `values` contains exactly `m1_kg,m2_kg` for C0,
adds `q1` for C1 and `q2` for C2. Units are `kg`, `kg/kg`, `MASS`.
Concentrations are mass fractions (source percent /100). `input_class` is
`SUPPLIED_EARLY_ASSAYS`, `SOURCE_EARLY_INPUT` or `SYNTHETIC`. Query JSON is a
list of objects containing only `start_kg,end_kg`, both cumulative measured
beverage mass from the original source collection origin. The forecast anchor
is m1+m2. Zero width gives zero solute and undefined average TDS. Before-anchor,
unknown or out-of-domain coordinates fail. Feature extrapolation is reported,
never a claim of accuracy. Remaining solute integrates from the anchor, including
modeled unassayed gaps; this is not a measured whole-cup total or inventory closure.

Source preflight inspected accepted original Pannusch arrays/workbooks locally:
45 FIT shots, 90 early assays, 177/180 eligible suffix windows (three unknown
measured prefixes); 24 PRED shots, 48 early assays, 96 intended suffix slots.
Primary C01/C02/C05/C06 is 48/48; temperature C03/C04 is 24/24; flow C07/C08
is 23/24 on the final FIT domain. Preserve original denominators and explicit
unsupported status. A larger training domain is not evidence of better accuracy.

Source campaign exposure influenced earlier development. This is RESEARCH_ONLY,
SOURCE_INTERNAL, TARGET_EXPOSED,
RETROSPECTIVE_CAMPAIGN_SEPARATED_CONDITIONAL_PREDICTION; not fresh blind or
independent validation or physical mechanism identification. Supplying beverage
mass does not predict hydraulics. PHYSICAL_VALIDATION=NOT_ESTABLISHED.
Pannusch/Schmieder, Mendeley 10.17632/y2tz67f6ry.1, source-derived CC-BY-NC-3.0
treatment is separate from first-party software licensing. Original workbooks,
observations, row predictions, states and detailed training logs remain private.

Independent exact-freeze review precedes one new-task score. Models cannot be
selected or retuned using PRED outcomes. No production adoption, merge, native
OpenFOAM, new data acquisition, laboratory operation or successor is authorized.
