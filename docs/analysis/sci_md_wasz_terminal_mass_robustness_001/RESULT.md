# Waszkiewicz terminal beverage-mass robustness

**The declining high-pressure response persists in all three fixed terminal mass windows and every relevant single-brew deletion.** Low-pressure response remains positive. All windows have recorded support for all 56 physical brews across the unchanged 11 conditions. This is a robust descriptive feature of recorded terminal beverage-mass increments, conditional on the acquisitions; it is not a calibrated physical-significance claim.

G1 / NO_GOVERNING_PHYSICS_CHANGE. RESEARCH_ONLY / RETROSPECTIVE / SOURCE_INTERNAL / TARGET_EXPOSED. [Protocol](PLAN.md); [full unrounded result](RESULT.json). Issue [#208](https://github.com/trbrewer/espresso-whole-pull/issues/208).

## Fixed result vector

Slopes use equal physical-brew means and unweighted condition regression against frozen accepted endpoint **measured line-pressure** means. LOW: conditions 1, 2, 3.5, 4, 5 (27 brews); HIGH: 9, 11, 13 (15 brews). These numbers identify groups; filenames and nominal pressures are not explanatory coordinates.

| Observer | Coverage | Low slope (g/s/bar) | High slope (g/s/bar) | Low difference from historical | High difference from historical |
|---|---:|---:|---:|---:|---:|
| historical_endpoint | 56/56 | 0.504206839400 | -0.065506412628 | 0.000000000000 | 0.000000000000 |
| q10 | 56/56 | 0.500459536271 | -0.070789817239 | -0.003747303129 | -0.005283404611 |
| q5 | 56/56 | 0.501605586079 | -0.069375819216 | -0.002601253321 | -0.003869406589 |
| q20 | 56/56 | 0.496239627735 | -0.069756131065 | -0.007967211665 | -0.004249718437 |

q10 is primary; q5 and q20 are fixed sensitivities. All four peak at WASZ-COND-6.0 (accepted measured line pressure 6.0047500000000005 bar). Canonical counts in increasing condition order are **5, 4, 3, 10, 5, 6, 4, 4, 5, 4, 6**. Every observer has these counts. [CONDITION_RESULTS.csv](CONDITION_RESULTS.csv) retains all 44 means, sample SDs (n−1), coordinates and identities; [BREW_RESULTS.csv](BREW_RESULTS.csv) retains all unrounded outcomes. Full and common-support cohorts are identical. There are no unavailable outcome pairs. None of the eight baseline slopes is near zero at the predeclared floating-arithmetic bound; physical near-zero significance is **not calibrated**.

Historical differences above are arithmetic paired contrasts with the immutable accepted table. The historical operator lineage caveat below prevents attributing these differences to the source truncated endpoint algorithm.

## A. Historical endpoint reconstruction

**Source formatter: PASS. Accepted historical label: a different operator; original producer provenance remains unresolved.** Independently reconstructed all 57 source representations, including all 56 canonical brews, at all 1000 grid points for pressure, mass, flow and basket pressure. Maximum discrepancy against Puckworks per-brew data is 5.00000000069889e-6, inside half the 5-decimal serialization unit plus 1e-10 numerical slack. Every published 57-record mean and SEM across 11,000 grid rows matches within half its 6-decimal unit plus that slack. The 4-decimal debug export is never reloaded. These tolerances describe file precision, not sensor error.

The algorithm uses the full p2 median, nearest-half-bar rounding and manual corrections for `1-2`, `2-3` and `2-5`; strict tolerance bounds; the global violation guard and exact reversed **indices 500 through 0 inclusive** search; START_IDX=last selected index+1; millisecond subtraction followed by multiplication by 0.001; truncation <=100 s; `np.gradient` with edge_order=1; SG(31,1) with actual default `mode="interp"`; and `np.interp` onto 1000 points. Of 56 physical brews, 55 hold their last retained point at 100 s; `9-1` has an exact 100-s sample. Last retained times range 99.912–100 s. [RECONSTRUCTION.csv](RECONSTRUCTION.csv) records each alignment, pressure correction, sample count, gradient/filter support, endpoint behavior and discrepancy.

The accepted SCI-MD-010/011 flow target is **`equilibrium_windows.csv`**, whereas accepted line pressure is `traces_per_brew.csv` at index 999. Their flow endpoints are not interchangeable. All 57 accepted equilibrium flow and basket-pressure values, and their 2/3-sample counts, numerically reproduce when averaging the **untruncated** SG derivative over actual acquisitions in [99.9,100.1] s. Maximum flow discrepancy is 4.569781785423999e-6 g/s and basket discrepancy 4.8545048656478684e-6 bar. This identified numerical rule is an inference from retained data; the original equilibrium-table producer is absent from inspected source/history. It does not uniquely establish historical code provenance. No new mass-window sensitivity or Pc/Qc calibration was run.

Using the accepted table reproduces historical slopes exactly: +0.5042068394004887 and −0.06550641262782862 g/s/bar. By contrast, the independently reconstructed source truncated observer gives 0.5021564419650943 and -0.06780227155227087 on those same fixed pressure coordinates. These are lineage diagnostics, not additional analysis arms. The largest source-truncated versus accepted brew difference is 0.23687365277326466 g/s (`6-5`). This discrepancy is an **operator difference**, not identity mapping or rounding.

The 57/56 distinction is separate: `12-8-6.txt` has 1447 lines exactly matching the prefix of `12-8-6_alt.txt`; the alias adds 42 later samples. Count it once. At condition 13, source-truncated flow averages 1.5874891060512708 g/s with seven records (published 1.587489), versus 1.5805710145435607 with six physical brews. Duplicate weighting explains that difference, but cannot explain the accepted-table discrepancies across all 11 conditions. No accepted observation was altered. A fully qualified paired contrast identifying the accepted historical observer with the original truncated formatter is **not established**; the independent mass-window result remains supported.

## B. Endpoint operator order properties

An ideal common nonnegative kernel preserves pointwise **discharge** order on a common physical interval. Cumulative mass order alone does not suffice: M_A=t and M_B=min(2t,100) obey M_B>=M_A on [0,100], yet terminal q10 is 0 for B and 1 for A.

The original truncated composite is not generally a positive discharge average. SG mode="interp" fits a line to the final 31 derivative samples and evaluates its edge; some weights are negative. Combining with the nonuniform-grid gradient produces negative interval-rate weights in the actual brew grids (retained per brew). The deterministic synthetic test starts with unit discharge, adds nonnegative discharge only on [70,71] s, and changes the truncated endpoint from 1 to 0.9445564516129027 g/s despite pointwise discharge and cumulative mass ordering. All three declared terminal mass averages preserve order in that illustration. This is a synthetic counterexample, **not evidence that processing caused the empirical downturn**.

The numerically inferred accepted-table operator has different order properties: its 2/3 near-100 derivative samples are all in the interior of the untruncated acquisition. Interior SG(31,1) is equal-weight averaging; the irregular-grid gradient is a positive combination of adjacent interval slopes. This gives a nonnegative interval-rate average on each observed grid. The kernels and physical times differ between brews, so it does not by itself provide the common-kernel premise of the theorem. The source-truncated edge-weight counterexample must not be attributed to that accepted operator.

Empirically, retaining later samples and evaluating the full filtered derivative at 100 s changes individual source-truncated endpoints by −0.17720746834953083 to +0.236743096484066 g/s. This one prescribed operator diagnostic is retained per brew, not another slope-selection window. Mass-window signs and deletion results stand independently of that diagnostic.

## C/D. Acquisition support and pressure-sign decisions

All 224 evaluation timestamps are directly sampled or bracketed within their own continuous acquisition; three are exact. Nonexact brackets are 0.093–0.095 s wide. Complete raw timestamps are strictly increasing, with no duplicates or nonfinite measurements and a maximum raw interval of 0.095 s. No anomalous long acquisition gap or scale reset crosses the required 80–100 s support. No maximum-gap or sensor-resolution acceptance rule is invented. Linear interpolation is calculable and locally supported; its error and the instrument response remain uncalibrated.

`7-1` has one incomplete final JSON record (row 1295) with p2 but no t/m. Its p2 remains in the source pressure median; no missing mass/time is fabricated. The last complete measurement reaches aligned 116.398 s, beyond all needed brackets and filter support. [ACQUISITION_SUPPORT.json](ACQUISITION_SUPPORT.json) retains this exception and every endpoint’s actual left/right time, mass, width and fraction, plus negative-step and gap diagnostics.

Later large downward scale changes occur in `12-8-6`, `2-4`, `4-2`, `4-3b`, `5-5`, `9-1` and `9-5`; the earliest of these is around 119.6 s, outside the declared windows. The alias extends the same later scale-clearing record. Smaller negative mass steps occur within terminal data (especially low-flow brews) and are retained without clipping or isotonic correction. No sensor-resolution explanation is asserted.

**C: negative high-pressure signs persist for q10/q5/q20 with full recorded support. D: positive low-pressure signs persist separately for q10/q5/q20.** Both decisions survive all relevant deletions; no preferred sensitivity was selected.

## E. Paired physical-brew influence

Exactly 56 deletions are paired across all four observers, retaining the original condition-mean line-pressure coordinates. [INFLUENCE.csv](INFLUENCE.csv) contains all 448 observer×region records, changes, signs and applicability. There are 15 relevant high-pressure and 27 relevant low-pressure deletions per observer. Deleting a brew outside a subset leaves that slope unchanged and supplies no additional robustness evidence.

| Observer | Low deletion range (g/s/bar) | High deletion range (g/s/bar) | Sign reversals |
|---|---:|---:|---:|
| historical_endpoint | [0.498569005155, 0.510973199711] | [-0.076253409037, -0.056504003816] | 0 |
| q10 | [0.496214041220, 0.505572699048] | [-0.079892092088, -0.062068995243] | 0 |
| q5 | [0.496851125108, 0.506823023555] | [-0.077983206726, -0.060562178925] | 0 |
| q20 | [0.491857222802, 0.501019513793] | [-0.078196071198, -0.061811282240] | 0 |

The largest absolute low-slope change is caused by `5-5` for every observer. For high slopes it is `9-5` for historical/q10/q20 and `9-1` for q5. Full ranked influences and extremal identities are retained in JSON/CSV. These ranges describe this finite cohort; they are **not confidence intervals or population uncertainty estimates**.

## F. Physical applicability and disposition

Retain declining high-pressure terminal beverage-mass delivery, and rising low-pressure delivery, as robust descriptive requirements on these recorded acquisitions. The result weakens an explanation confined to the original truncated endpoint derivative, but does not identify an empirical artifact or physical mechanism. The historical observer naming/provenance limitation remains explicit. This task is complete without a follow-on.

Terminal mass increments are averaged **scale-observed beverage outflow**, not instantaneous discharge or hydraulic flux through the puck. Linear interpolation does not correct instrument lag, filtering or calibration. Aligned time origins differ across brews (raw acquisition timestamps at alignment range 1.526–11.529 s), and do not establish common physical-origin time. Material/preparation and initial-state variation are not controlled into a common initial state. There is no independent source, predictive scoring, physical measurement-uncertainty model, or mechanism identification. PR #207’s scalar impossibility theorem remains valid under its assumptions; its physical application and full spatial/stochastic Mo2021 behavior are not established by these data.

## Reproduction and evidence

Data: Waszkiewicz, Myck, Białas, Puciata-Mroczynska, Dzikowski, Szymczak and Lisicki (2025), [Zenodo 18046315](https://zenodo.org/records/18046315), data CC-BY-4.0. The Zenodo API confirms that data license; accompanying software is GPLv3. No upstream source code was copied or executed. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) authenticates every consumed original file against Git objects, plus read-only Puckworks and EWP authorities, with SHA-256 and relative paths. Original acquisition retrieval succeeded. The initial local Puckworks clone lacked the supplied main object; fetching that exact revision resolved it.

Use Python 3.12.3, NumPy 1.26.4, SciPy 1.11.4, pandas 2.2.3 (recorded environment; the implementation parses JSON itself). Keep source checkouts and any rerun output outside the EWP checkout:

```bash
git clone --depth 1 --branch v1.0.1 https://github.com/RadostW/espresso.git "$EVIDENCE/upstream"
git -C "$EVIDENCE/upstream" rev-parse HEAD
# Must equal fbc33d3380a9c8cff2467bae70fec7137a6ed46f.
git clone https://github.com/trbrewer/puckworks.git "$EVIDENCE/puckworks"
git -C "$EVIDENCE/puckworks" checkout --detach 58075bbbce548e63d94106c96b918c1464221514
python3 tools/sci_md_wasz_terminal_mass_robustness_001/analyze.py \
  --puckworks-root "$EVIDENCE/puckworks" --source-root "$EVIDENCE/upstream" \
  --output "$EVIDENCE/rerun"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sci_md_wasz_terminal_mass_robustness_001 -v
```

The seven generated CSV/JSON files are deterministic; compare their bytes with this bundle. [Implementation](../../../tools/sci_md_wasz_terminal_mass_robustness_001/analyze.py), [focused tests](../../../tests/test_sci_md_wasz_terminal_mass_robustness_001.py), [verification receipts](CHECKS.json), [independent scientific review](REVIEW.md). Live final-head hosted CI and PR lifecycle receipts belong in the PR description so that adding a receipt cannot invalidate the head it describes. Production dependency lock and prior scientific artifacts are byte-for-byte unchanged.

PHYSICAL_VALIDATION=NOT_ESTABLISHED
