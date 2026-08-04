# VAL-CORPUS-002 Stage B2 final-package correction

Authorization `VAL-CORPUS-002-B2-PRODUCTION-SCORING-2026-08-03` permits one
bounded, no-execution reporting and source-lineage correction within
`EWP_PRODUCTION_AND_SCORING_STAGE_V1`.

The following exact-head findings are frozen before derived reporting changes:

- `CUP_MASSES_LINEAGE_CAVEAT_NOT_CARRIED`
- `FINAL_RESULT_SCHEMA_ONLY_TOP_LEVEL_CLOSED`
- `FINAL_STATUS_AMBIGUOUS_WITH_TYPED_FAILURES`
- `EMBEDDED_BASE_RESULT_AUTHORITY_NOT_MARKED`
- `TARGET_AVAILABILITY_SEMANTICS_AMBIGUOUS`
- `FIGURES_ARE_TEXT_ONLY_NOT_SCIENTIFIC_PLOTS`
- `REPORTING_REDUCER_FAIL_CLOSED_HARDENING_REQUIRED`

This correction does not alter any calibration, production, sensitivity,
parity, source, configuration, trace, log, or external execution artifact.
The approved scientific result and every numerical value remain unchanged.

```text
numerical artifacts: UNCHANGED
scientific result: UNCHANGED
OpenFOAM: PROHIBITED
sensitivity rerun: PROHIBITED
refit: PROHIBITED
protected scoring: PROHIBITED
new governing physics: NOT_AUTHORIZED
VAL-CASE-002: NOT_STARTED
merge: NOT_AUTHORIZED
```

The correction may only add the persistent cup-mass lineage authority, carry
that lineage through existing consumers, close and clarify derived machine
records, harden reporting-time verification using already-approved operators,
replace text summaries with deterministic plots, and reconcile current-state
records.

## 2026-08-03 exact-head figure-semantics review

Reviewed head `4765f6fdde10f277c70b4a4b50d5333d58c9f629`, tree
`458af5c6e6ed8c8ca1d80f4d42f30ac467bd869b`, under authorization
`VAL-CORPUS-002-B2-FIGURE-SEMANTICS-CORRECTION-2026-08-03`.

Finding `B2-FIG-001` is
`SCIENTIFIC_FIGURE_SEMANTIC_LEGIBILITY_AND_PLOT_BOUNDS_NOT_CLOSED`.
The three observed manifestations are:

1. overlays or anonymous cells prevent unambiguous experiment/run/series
   identification without consulting JSON;
2. quantitative axes, governed labels, and sensitivity row/column identities
   are incomplete; and
3. plot geometry and long labels are not contained by explicit,
   non-overlapping title, legend, plot, lower-label, axis-title, annotation,
   and caption bands.

This is a reporting-only correction. The frozen P2 rate, 45 production
identities, 27 PASS dispositions, 18 typed target-coverage failures, 21 H1
PASS identities, 9/9 sensitivity result, 1500/1500 parity result, scientific
interpretation, claim ceiling, source evidence, and all numerical/external
artifacts are immutable. OpenFOAM, sensitivity execution, calibration,
refitting, protected scoring, mechanism work, VAL-CASE-002, and merge are
prohibited.

Closure identities, changed generated hashes, qualification results, and the
final correction head/tree will be appended after deterministic regeneration
and qualification. Until then:

```text
review_status: CORRECTION_AUTHORIZED_IN_PROGRESS
merge_status: NOT_AUTHORIZED_PENDING_CORRECTED_EXACT_HEAD_REVIEW
```

### Figure-semantics correction closure

The reporting implementation commit is
`8cd8b5431cdaceda7242f975d90f09f142ee8850`, tree
`ff881ce3c5d7e2e8da9aa5a5ffff128de1ba1dc9`. It replaces the overlay and
anonymous-cell figures with seven experiment small multiples, six frozen-axis
contrast panels, a governed 45-run availability matrix, two quantitatively
labeled fixed-clock panels, and a fully labeled sensitivity/singular-value
diagnostic. Every plotted primitive is bounded by its declared plot rectangle;
all layout bands are explicit and non-overlapping; and repeated generation is
byte-identical.

```text
reporting reducer: 50fc3ac6a74ab16b6edb460fb21005704032c4f56d26bcba81195423624d1cf2
figure manifest: 7dfff8c964e30a8a5179acff6540fa33eb558a889ca8b34a5bb287bd96eebee8
figure aggregate: f755c6aea99134671edf0e23868d3e10a5c1b66063b93516bf5b450887b2faec
final report manifest: 4a7fa7235ad2f2faddaec16f058846f3f30f4c986d5ac3adf442c0c5d4e00ab6
Python: 445/445 PASS
focused Stage B2: 36/36 PASS
static gates: 38/38 PASS
source manifest: 272/272 PASS
review_status: VAL_CORPUS_002_STAGE_B2_FIGURE_SEMANTICS_CORRECTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW
merge_status: NOT_AUTHORIZED_PENDING_CORRECTED_EXACT_HEAD_REVIEW
```

All scientific and numerical identities listed above remain unchanged.

## 2026-08-03 sensitivity colour-key exact-head review

Reviewed head `f0ceaa8b3307f2c380a64f17b6e1d240d2c9481b`, tree
`83f56c1853b94e3c4361f9db3b3b5256185d3566`, under authorization
`VAL-CORPUS-002-B2-SENSITIVITY-COLOUR-KEY-CORRECTION-2026-08-03`.

Finding `B2-FIG-002` is
`SENSITIVITY_COLOUR_KEY_DOES_NOT_MATCH_CELL_ENCODING`. The current mapping
assigns the three near-zero negative elasticities
`-0.00020477941226442888`, `-0.00022668882225069568`, and
`-0.00023192355395433323` a pale-yellow fill because the blue channel jumps
from `255` to `135` solely on sign. The legend instead declares a pale-blue
neutral swatch. Consequently, the cells and key do not share one continuous,
neutral-centered signed-magnitude mapping.

This correction is reporting-only. The other four accepted SVG files are
byte immutable at hashes `c243c06a9fd46eafe27e1934e8c3be40e2b9589fa33309e47996a0bdbb204872`,
`d35aa0f9d005c70e0476b16f3a6bb3120e483c39a5e1b8f5b9be7908db31e394`,
`0292810de091bede23ba284f2d25720516f106e87c77bb55595ca20c0cd8723c`,
and `8f4b7bce271bfe97557b8adae37e0f528d77534d30f784f464caa582ae1ce8fa`.
The sensitivity matrix, singular values, rank, scientific interpretation,
claim ceiling, and every numerical/external artifact remain immutable.

```text
review_status: CORRECTION_AUTHORIZED_IN_PROGRESS
merge_status: NOT_AUTHORIZED_PENDING_CORRECTED_EXACT_HEAD_REVIEW
```

Closure identities, the old and new sensitivity hashes, dependent manifest
hashes, and qualification results will be appended after implementation and
qualification. The existing B2-FIG-001 record remains unchanged.

### Sensitivity colour-key correction closure

The reporting implementation commit is
`cd6529487865a5c729b0380a7f30877803f25fc8`, tree
`eecb5099278fa05a908a8589b1708e84d83d785c`. One authoritative helper now
interpolates continuously from the neutral RGB value to distinct negative or
positive endpoints using normalized absolute magnitude. The 12 cells and all
three key swatches call that helper and carry deterministic machine-readable
value, normalized-magnitude, sign-class, and fill attributes.

```text
old sensitivity SVG: ea3bbabaa222d97fd90038724c45c2837d47ececcfab99f3f55671f8e4ee7dba
new sensitivity SVG: 5ba16412f89040ce7e62069e9af9df71197656b8daefc82e8efe06c9f1ef1197
reporting reducer: 12d2517c9304f562c9395023f5b6fe9a609fcac7becca70bf0fca55a09fe84fb
figure manifest: 1cde29b7558c71451453b243861d015b8b3be0982e424680b9e9666183c64a0e
figure aggregate: 77e080b59fd94e27030d280f3f2054c71a67d57d3a5be1de4c17ef31ab068330
final report manifest: 86855f3e77ac6723cf02b327b82e812a6141f0e8c94d9165c4f48c97d33aab0e
Python: 448/448 PASS
focused Stage B2: 39/39 PASS
static gates: 38/38 PASS
source manifest: 272/272 PASS
continuous neutral-centred colour mapping: PASS
accepted four-figure byte parity: PASS
deterministic repeat generation: PASS
review_status: VAL_CORPUS_002_STAGE_B2_SENSITIVITY_COLOUR_KEY_CORRECTION_COMPLETE_PENDING_EXACT_HEAD_REVIEW
merge_status: NOT_AUTHORIZED_PENDING_CORRECTED_EXACT_HEAD_REVIEW
```

The sensitivity values, labels, singular values, rank, interpretation, other
four SVG files, and every scientific and numerical identity remain unchanged.
