# Two-assay research consumer

SCI-MD-MASS-DELIVERY-005. G1 / NO_GOVERNING_PHYSICS_CHANGE.
EWP [#191](https://github.com/trbrewer/espresso-whole-pull/issues/191), producer
[#285](https://github.com/trbrewer/puckworks/issues/285). The bounded owner task
authorizes research software and a single independently audited comparison.
No production adoption, lock change, native OpenFOAM run, laboratory work, merge
or successor is authorized. PHYSICAL_VALIDATION=NOT_ESTABLISHED.

[HANDOFF.json](HANDOFF.json) binds the evaluated producer commit/tree and every
transitive first-party numerical module and both frozen 001 models. This research
pin is separate from the unchanged production dependency lock and later result
commits. The consumer uses explicit isolated loading, without installed fallback.

```bash
# PRODUCER must be the exact runtime checkout identified in HANDOFF.json.
python3 scripts/research_two_assay_mass_delivery.py --producer "$PRODUCER" --synthetic --stop-kg 0.04
python3 scripts/research_two_assay_mass_delivery.py --producer "$PRODUCER" \
  --observations "$PRIVATE_PAIR_JSON" --queries "$PRIVATE_QUERIES_JSON" \
  --arm TWO_ASSAY_MASS --stop-kg 0.04 --output "$PRIVATE_RESULT_JSON"
SCI_MD_MASS_DELIVERY_005_PRODUCER="$PRODUCER" python3 -m unittest discover -s tests -p 'test_research_two_assay_mass_delivery.py'
```

Observation JSON is an object with `first` and `second`. Each contains `shot_id`,
`source_id`, `fraction_id` (1 or 2), `start_kg`, `end_kg`, `tds_percent`,
`mass_basis` (`MEASURED_MASS_G_CONVERTED_TO_KG`), `rights`, `input_class`
(`MEASURED_SOURCE_TWO_ASSAY_INPUT`), `tds_basis` (`MASS`) and `tds_unit` (`percent`).
Pair shot/source/rights must match and intervals must be ordered, nonoverlapping,
positive-width and in domain. Provenance IDs select no coefficient.
Queries are a JSON list of objects containing only `start_kg` and `end_kg`.
No future chemistry is accepted. The output path must be new and outside Git.
Synthetic examples are explicitly labeled `SYNTHETIC_TWO_ASSAY_INPUT`.

The primary estimand is PREDECLARED, MEASURED-PREFIX, IN-DOMAIN FUTURE ASSAY
WINDOWS: 48 PRED and 113 FIT-transfer windows, all 42 shots/14 conditions.
Fractions 1 and 2 condition the predictor; only fractions 3,5,7,10 are scored.
A separate full-intended-suffix assessment retains 168 slots, including three
unavailable prefixes and four out-of-domain windows. No arm failure shrinks the
primary mask. Original 001 fitting shots are excluded and its artifacts frozen.
004 is historically FROZEN_EMPIRICAL_TRANSFER_INADEQUATE; the new restricted
assessment cannot reverse it. Live 001–004 PRs were verified merged at task start.

Source-qualified prepare/freeze/score/report commands and contracts are in the
[producer task](https://github.com/trbrewer/puckworks/tree/research/sci-md-mass-delivery-005/docs/analysis/sci_md_mass_delivery_005).
Exactly six arms are evaluated, with TWO_ASSAY_MASS retained as primary after
scoring. Up to 84 two-parameter updates and 168 analytical amplitude updates;
actual counts and numerical refinement calls are reported. Zero global refits.
SOURCE_INTERNAL / TARGET_EXPOSED / RETROSPECTIVE_TWO_ASSAY_CONDITIONED_COMPARISON.
A and k are conditional empirical parameters; no identified physical kinetics,
assay robustness, real-time feasibility, universal grind map or hydraulic claim.
Assayed-support solute sums are not measured whole-cup totals. Raw sources,
observations, states, row predictions, per-shot results and logs stay private.
Pannusch/Schmieder source-derived artifacts retain CC-BY-NC-3.0 treatment and
Mendeley 10.17632/y2tz67f6ry.1 attribution, separate from software licensing.

Executed result: [RESULT.md](RESULT.md); separate [QA/review status](QA.md). Actual estimation was 84 two-parameter updates and 168 analytical amplitude updates.
