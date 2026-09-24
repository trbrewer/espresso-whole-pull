# SCI-MD-MAILLE-TRANSFER-001 development decision

**BLOCKED_SOURCE_CONTRACT.** Puckworks implemented and executed the source
adapter/audit. The predictive question remains unanswered for caffeine, 3-CQA,
citric acid, malic acid and quinic acid. Adequacy of MAILLE_E0/ES/DS/B2/P2,
two-rate gain and the source-phi increment are all **NOT_ADJUDICATED**.

G1 / `NO_GOVERNING_PHYSICS_CHANGE`. Await owner disposition; linked PRs stay
OPEN/UNMERGED. `NO_SUCCESSOR_EXECUTION_AUTHORIZED`.

## Source and decision

Table 5.10 contains all 105 empirical tabulations: three materials × five
analytes × seven nominal times. Seventy-five early comparative entries have
approximate clocks and unresolved replicate selection; 30 late entries average
three normalized replicates. All 15 curves have five early and two late values.
Three whole-material folds were planned, but **zero were executed**: no fits,
optimizer attempts, held-material predictions or model scores were produced.

The source normalizes each extraction experiment by its own maximum measured
concentration, usually at 300/600 seconds and sometimes at 60/180 seconds.
The required B/C replicate denominator/reference-time joins and selection-error
information are absent from the inspected files. Table 5.11's pooled means and
SDs cannot reconstruct this operation. Substituting their maximum gives a
0.0502762431-unit discrepancy for B quinic acid at 180 seconds. That is a
source-mapping check, not a prediction error or experimental error bound.

**FILES_INSPECTED:** Puckworks Tables 5.1/5.4/6.3/5.10/5.11 and provenance,
the five A figure CSV headers, the public thesis methods and table pages, and
the owner-held Maillé directory (20 files byte-identical to packaged files).
**CATALOG_ONLY:** Remaining Maillé material/transport subsets; no extra dataset
is inferred from catalog entries. Tables 6.4/6.5 remain excluded historical
source fits. Detailed locators, identities, source classes, rounding, missing
lineage and the common-roast/treatment-redaction limitation are in the exact
Puckworks producer report identified by [HANDOFF.json](HANDOFF.json).
The public source is Maille (2024), University of Sheffield,
[White Rose thesis record](https://etheses.whiterose.ac.uk/id/eprint/36281/).
No thesis PDF, private original or new raw-data dump is committed.

**Development decision:** retain current implementation and defaults. This task
earns no two-rate coupling and rejects no kinetic family. Resolving the named
source contract would require the original replicate normalization lineage and
a defensible treatment of maximum-selection uncertainty; no recovery project,
measurement campaign or successor execution is authorized. This is a bounded
existing-data gap, not a blanket claim that Maillé or the corpus is exhausted.

The requested predictive curves, error comparisons, early residuals and A-held
figure overlay were not produced because no eligible prediction freeze exists.
They are not replaced by historical source-rate fits. No source/observer
treatments or optimizer choices were frozen after viewing scores: no scores
exist. The independent G1 pre-scoring audit was not reached or self-certified.

## EWP compatibility and provenance

The actual aggregate extraction source was inspected in
`solver/espressoWholePullFoam/espressoWholePullFoam.C`: beginning-of-step release
is proportional to remaining extractable inventory, wet mask and a nonnegative
saturation-capacity factor, then capped by available inventory over the step.
It feeds the transport equation and reduces the remaining inventory. The Maillé
normalized batch-analyte observer is not that aggregate effective-solute law.
This blocked analysis cannot falsify it or identify total solids, EY, TDS,
initial extractable inventory, permeability or an espresso boundary.

Fetched starting EWP main was `3ca164871cb4cdfdd2958f1ef34c6e62a8d8bb35`, tree
`329dac55b06f2a946c4b0a746ba5b83ecea68a8c`; starting Puckworks main was
`1648fa095f1aca133616b8a4bb07dcae569a91d2`, tree
`df57a459b9b40e4e7adb5a026502da37eee5a974`. Dedicated task worktrees preserve
unrelated changes and predecessor work. Prior Maillé reproduction, shell-depth,
model-generated timescale portability, Smrke transfer and radial-observation
results were not restarted. No duplicate whole-material task was found.

The exact producer is [`e950540ba3b421950e9103f383ba7d9740cf00f7`](https://github.com/trbrewer/puckworks/tree/e950540ba3b421950e9103f383ba7d9740cf00f7),
tree `a8a58371231408e8e44e72d11bd426394231ec84`. HANDOFF.json binds this commit/tree and compact artifact
hashes; it is a task-specific scientific receipt, not a production dependency
update. The source views and complete QA logs remain in private evidence.

## Reproduction and separate statuses

At the Puckworks commit recorded in HANDOFF.json:

```bash
python tools/analyze_maille_transfer.py --output /tmp/maille-transfer-audit
python -m pytest -q tests/test_maille_transfer.py tests/test_maille2024.py tests/test_maille2024_component.py
```

The CLI regenerates the long-form source view, late-reference summary view,
compact result and their hashes. The two source views remain outside Git.
There are no prediction/parameter/residual artifacts to replay.

Scientific result: source-contract blocked. Puckworks existing quick suite:
4,571 passed / 33 skipped / 65 deselected; 26 new adapter tests passed separately.
There are 65 distinct focused and existing Maillé tests. EWP broad run: 1,572
tests, initially two failures and one class setup error (nine skipped). The
required pinned-authority environment was supplied and 21 affected tests passed;
manifest metadata was refreshed and its check passed. Initial logs are retained.
Source/static/historical/active-boundary/shell/JSON checks pass. Hosted CI and
independent review remain separate dispositions recorded on the PRs.
Independent final exact-head/base review is **pending**, not approved.
Passing software checks does not pass the scientific hypothesis.

Native OpenFOAM builds **0**; native integrations **0**. Solver behavior,
production defaults and `dependencies/puckworks.lock.json` are unchanged.
Physical validation remains **NOT_ESTABLISHED**. No merges, laboratory work,
new measurements, protected-comparison reopening or successor execution.
