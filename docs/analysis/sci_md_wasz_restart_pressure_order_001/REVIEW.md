# Independent scientific review — SCI-MD-WASZ-RESTART-PRESSURE-ORDER-001

Verdict: **PASS within the declared nominal recorded/interpolant and conditional-error scope. No material correction requested.** This is independent AI scientific review, not a human GitHub approval, independent acquisition or physical validation. Review date: 2026-10-22.

Reviewed scientific candidate: `b34d7edaa29a6779c688616f96ee8e283c95eb85`, tree `2265c4c547ef80322f2c59deafbb91f07b2a6c8a`; actual base `aace2cc6b6c2a393d2dbfb0274104192ca6c7203`, tree `cb713f8229075fe4f3f1e05d1eca77868e5692ae`. The candidate worktree was clean at review intake. Scientific artifact hashes below bind this disposition; later review/QA/PR administrative changes do not require repeating unchanged science. Repository-wide QA and hosted CI remain separate outcomes owned by the implementing agent.

The review inspected the complete new plan, producer, 19 focused tests, source manifest, result prose and machine artifacts; the full retained comparison and witness contents were independently checked computationally. Relevant #211 result/review, original source-observer implementation/constants and retained episodes/intervals/result/manifest were inspected. EWP instructions, governance/data-first/available-data and claim-scope guidance, current programme/ledger entries and Puckworks data/development-guide and Waszkiewicz-card sections were read. Current Puckworks sections were read by `git show` at `d4eb54ce4bd0eb21a0968d3c37f43ad4ef8ccd16` after initially reading the prior `58075bbb` authority checkout; Puckworks was not modified. Other data families were context/catalog evidence only. No corpus-exhaustion claim is made. The upstream plotting script was read only for lineage and units, never executed or copied into repository code.

## Independent source and observation audit

The independent script imports neither the new producer, the previous observer nor upstream analysis code. It authenticates raw bytes using SHA-256 and the Git object-header hash, checks the pinned tree and source checkout HEAD, parses source decimal tokens as exact Fractions, independently groups ACTIVE acquisitions and scans source intervals for interpolation support.

The source revision is `fbc33d3380a9c8cff2467bae70fec7137a6ed46f`. Acquisition bytes are 163514, Git blob `7940d6aa008e7cae37bb1bf8ceece44fa07d0bff`, SHA-256 `e82430cde25574140d2026882a883fba21a0f0ac6d9588b15df22571836f68e9`. Plotting-script bytes are 1783, blob `f93c4c2abb6847d70b21df669bd6940089c226b3`, SHA-256 `aa35ade18cc8b6946164279d6e2e82337435c3165698be932ff3d0f32b47cd74`. Both exactly match the pinned tree and both new and #211 manifests. The established CC-BY-4.0 data attribution and separate GPLv3 software treatment are preserved.

All 1818 original acquisitions remain on the original 126–170031 ms clock. Every adjacent gap is 93–95 ms; there are no documented discontinuities. Pressure-only segmentation exactly reproduces E0–E5 and their original row indices. Source units are t/1000 seconds, p2/100 bar and m grams; p1 and the other fields are unused. All 18 retained later intervals reproduce the prescribed duration/guard, endpoint times, original brackets/exact-sample flags and retained supported decisions. The maximum exact-source rate difference from #211 decimal float serialization is `24849/1457000000000000000` g/s, approximately 1.706e-14 g/s, solely arithmetic reconciliation.

Code inspection confirms no extrapolation, skipped invalid rows, nonfinite support, nonincreasing clock, gaps above 95 ms, documented-discontinuity crossing or episode-crossing brackets silently supply observations. The 95 ms limit is correctly described as a software support condition. The new observer implements the prior observation contract without smoothing, regular regridding, mass repair, a pressure correction, a new window or lag search.

## Independent full-family arithmetic

The reviewer recomputed **all 27 unique comparisons**, including every original elapsed-time knot of both trajectories, all support interpolation weights and values, all segment extrema and all attaining global witnesses. Every stored exact rational agrees. All 30 reporting rows and the three explicit B(E1,E0) duplicate links agree. Family A has lower/higher/crossing counts 3/4/8; B has 6/3/6. There are 9 contrary reporting rows but **6 unique contradictions**, exactly E1/E0 and E5/E4 under the three designs, from **one puck**. All remaining unique cases retain NOT_EXCLUDED_BY_PAIRWISE_ORDER_TEST.

Representative independently recomputed values, presentation-rounded only:

| Comparison | min(P_R−P_C), bar | max(P_R−P_C), bar | delta_q, g/s | min elapsed ms | max elapsed ms |
|---|---:|---:|---:|---:|---:|
| PRIMARY E1/E0 | 0.008250000000 | 0.094626670213 | 1.409188527225 | 1475 | 167 |
| SENSITIVITY_A E1/E0 | 0.008250000000 | 0.112024666667 | 1.374298566308 | 2475 | 0 |
| SENSITIVITY_B E1/E0 | 0.021604838710 | 0.112024666667 | 1.388779892473 | 2000 | 0 |
| PRIMARY E5/E4 | 0.000734042553 | 0.058727007550 | 0.076981235235 | 1475 | 2000 |
| SENSITIVITY_A E5/E4 | 0.000734042553 | 0.058727007550 | 0.044060146420 | 2475 | 3000 |
| SENSITIVITY_B E5/E4 | 0.008999000000 | 0.046397368421 | 0.007747202796 | 1260 | 512 |
| PRIMARY E3/E0 | −0.162702127660 | 0.023952117021 | 2.061657167124 | 1850 | 166 |

At PRIMARY E1/E0's minimum, C is original sample 976 at 91388 ms, pressure 33479/4000 bar, and R is sample 799 at 74838 ms, pressure 4189/500 bar; their difference is exactly 33/4000 bar. At PRIMARY E5/E4's minimum, C at 164794 ms uses samples 1760/1761 with weights 1/94 and 93/94, giving 1588321/188000 bar; R is sample 1534 at 143569 ms, 33797/4000 bar. Their difference is exactly 69/94000 bar.

The crossing control PRIMARY E3/E0 has minimum −7647/47000 bar at s=1850 ms and maximum 2251499/94000000 bar at s=166 ms. At its minimum, C uses samples 1348/1349 with weights 93/94 and 1/94, and R is sample 803. At its maximum, C is sample 1330 and R uses samples 784/785 with weights 1/94 and 93/94. This crossing is retained as unexcluded; no existence claim is made. Complete exact results and both extremal witness records for every unique pair are in the external receipt.

## Theorem and robustness review

The theorem is valid. A finite nondecreasing F on the closed observed pressure range is bounded and Borel measurable; its composition with continuous piecewise-linear pressure is integrable. Pointwise C≤R implies F(C)≤F(R) and therefore qbar_C≤qbar_R for equal positive duration. The symmetric higher-pressure case, identical-pressure equality and permission for flat F under strict pressure order are handled correctly. The union of both original shifted knot sets is sufficient because the difference is linear on each intervening segment. Exact Fraction signs avoid any tolerance-driven order certificate. One contrary pair rules out a common F for the declared set; the absence of such a pair does not establish existence.

For each ordered actual pair I independently subtracted its adverse differential pressure margin from every signed, correctly oriented knot difference: the minimum becomes exactly zero, so equality preserves weak order. An arbitrarily larger adverse correction can create a reversal. The half-margin per-trajectory boundary correctly requires separate equal absolute bounds and does not assume independence. Zero-margin nominal weak order has no positive adversarial reserve.

The delivery error bound is also correct: an adverse contrast correction strictly below |delta_q| preserves its contrary sign; equality can remove it. Endpoint-box eta=D|delta_q|/4 assumes fixed timing and interpolation. I independently derived and aggregated every distinct original-sample coefficient and checked exact reconstruction of delta_q, coefficient sum zero and L1 norm. Every actual comparison has norm 4/D, so the generic endpoint bound is attained here. For each contrary comparison, a raw-sample error vector at eta=|delta_q|/L1 exactly cancels its contrast; this is a separate per-pair worst-case construction, not a simultaneous correction or measured accuracy. Synthetic tests correctly cover cancellation and reinforcement from shared raw samples.

Common additive mass offset cancels; positive common mass gain preserves contrast sign; common constant pressure offset and common positive pressure gain preserve order. Differential drift and dynamic response need not cancel. The report correctly leaves latency, storage, transit, timing and interpolation-model error unbounded and separates numerical precision from unestablished measurement uncertainty. Shared observations preclude independent-experiment interpretations.

## Verification, figure and interpretation

All **19 focused tests pass** independently. A separate offline execution of the candidate producer reproduces SOURCE_MANIFEST.json, RESULT.json, PRESSURE_ORDER_WITNESSES.json, COMPARISONS.csv and PRESSURE_ORDER.svg **byte for byte**. Logs and hash receipt are external. A reviewer-script self-check initially divided an integer p2 token with Python `/`, producing a floating result only in that check; explicit Fraction conversion fixed the review harness. No candidate artifact or scientific assumption changed.

The rendered pressure-order figure was visually inspected. It displays all 27 unique ranges and contrasts, labels recorded/interpolant evidence, separates crossing/unexcluded cases, and makes the small E5/E4 margins and conditional boundaries legible in a dedicated detail panel. Its lack of inferred physical error bars is explicit.

The leading claim and development consequence are appropriately bounded. This excludes one common finite time-independent nondecreasing response **under the retained pressure interpolants and interval mass mapping**. It does not establish physical pressure order, calibrated sensor applicability, interruption-specific causality, chemical exhaustion, channels, steady state or a permeability law. Fixed nonmonotone responses and pressure-driven memory models remain outside the exclusion. Response shape, evolving state/conditions or a supported observation contribution can account for a reproducing model's discrepancy; the calculation does not identify which is responsible.

The candidate's diff preserves #211's unrestricted-F result and the historical #207/#209/#213 artifacts, accepted cohort and production lock. No model fit, solver campaign, Puckworks modification, adoption or successor is introduced. PHYSICAL_VALIDATION remains NOT_ESTABLISHED. No material scientific, claim-scope or source-provenance correction is requested.

## Artifact bindings

Paths below are EWP-root-relative; SHA-256 values bind the reviewed scientific content.

| Artifact | SHA-256 |
|---|---|
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/COMPARISONS.csv` | `be69cbf0492a178068be9271bb1fc2fe2c1c4f1f0a0460b9236a8b68780f97dc` |
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/PLAN.md` | `0dca355a15ff15a28a32bff68d4cbc466f5f202e54755b3f8f6a58f629cf2994` |
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/PRESSURE_ORDER.svg` | `d6b7197a4eb593f21c28925ae677d3ae28799c12b762adec8be74c95093906bb` |
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/PRESSURE_ORDER_WITNESSES.json` | `e2308e03c319a3f7871a132eb3d516eff76472a0d7353eb79a7ec662360c7d07` |
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/RESULT.json` | `b435e7ab3158bc2fc03402915d83eca0adfbc961eff05e56d6c9f209053d7404` |
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/RESULT.md` | `05f66d8f4bedd9951136129929d36036f2ed01a690bbb60c6a5048401455ba17` |
| `docs/analysis/sci_md_wasz_restart_pressure_order_001/SOURCE_MANIFEST.json` | `ab8960726b41fc73301a4b105ff66b38ab7957dc0536730921171431e277227e` |
| `tests/test_sci_md_wasz_restart_pressure_order_001.py` | `535a27b103d0e1e923e33020796ac1f680e85a834587f5f9a87af46876daec0f` |
| `tools/sci_md_wasz_restart_pressure_order_001/analyze.py` | `97d0eb83b48b5be30a2b43fa54388a12eb96c5eb2178a4b9cafe605ef1b0f8a2` |

External evidence locators are relative to the task evidence root. Raw source locators remain source-root-relative in SOURCE_MANIFEST.json; no raw payload is added here.

| External locator | SHA-256 |
|---|---|
| `independent-recompute.py` | `82728870028f3d3564931e1ed007c94376457af1997423df65b7cc259affa795` |
| `independent-recompute-receipt.json` | `b4a5dae09d7ce90ccd5880ef67a6c417279844ca8cab0f98c992fc012e4e71a3` |
| `independent-recompute.log` | `e1e7e67dc19c2b07ffed9a6e6e47b22212346cb96159b36acc2a41ab54298a1f` |
| `independent-focused-tests.log` | `f85aec530530cd9c618e4dd97a71499c6612953bd9736d00623aa6efabb2394b` |
| `independent-reproduction.log` | `d4cc3694e85800424cbee1d4f25fddf3b055ab95de4a6f6e5c626fff52724631` |
| `independent-reproduction-hashes.json` | `454083bd0bd49a9403b94becfd4421b13250e6335c97f3b43558a178f6c64b0a` |

## Implementer verification and administrative closeout

The scientific candidate above also passed the complete local Python suite:
**1,696 tests run, 1,675 passed, 21 existing environment/retained-artifact skips,
zero failures or errors**, 493.974 seconds. Python 3.12.3, NumPy 1.26.4,
SciPy 1.11.4 and jsonschema 4.23.0 match the current workflow. Existing historical
Puckworks test authority was read at a3428a4d4ad571ef3168a70e8a04620fca5d3520,
with 2058d0e947ee9eb92c52d64f6165b810f1fb4732 available, separately from the
read-only research main and production lock.

All normal local checks passed: source manifest (1,462 entries at scientific
candidate), static package validation (39 gates), historical baseline integrity,
active governing-change boundary, rheology 005/006 validators, XSV-PRESSURE
contract, release contract/integrity, WP03 A/B/C boundaries, externally pinned
VAL-001 administrative identity, shell syntax, JSON syntax, diff whitespace and
generated-artifact/secret/path boundaries. Commands match the current workflows;
full logs remain external. No OpenFOAM or archival Allrun/Allverify/Allclean was
executed. The task producer uses only the standard library.

Five generated artifacts reproduced byte for byte in a separate implementer
execution as well as the independent review execution. All six exposed margin/
delivery cross-checks agree at their twelve-decimal presentation precision.
Git-object comparisons verify unchanged #207/#209/#211/#213 bundles, accepted
cohort analysis, production lock and solver. There were no candidate scientific
or repository-check failures requiring correction. The independent review's
self-check-only float conversion correction is recorded above and did not touch
the candidate.

The active main rules were read directly from the GitHub rules API, rather than
inferred from legacy branch protection: protect_main ruleset 19901931 requires
source-and-boundary and inexpensive-checks. Its snapshot and all check receipts
below are bound by SHA-256. The nine scientific file hashes above remain the
scientific review binding; later edits only add this review and refresh package
manifest bookkeeping. Final administrative checks and hosted CI are attributed
to the final tested head in the PR handoff, avoiding recursive self-binding here.
The PR is to remain open/draft/unmerged with auto-merge disabled.

External locators below are relative to the task evidence root. `local-qa.json`
contains exit codes and SHA-256 for each full `<check>.log`, with check names as
keys; it binds the complete local check logs without copying them into Git.

| External locator | SHA-256 |
|---|---|
| `independent-review-report.md` | `9f342e8764218be89d2f580e2d095a2ccc77b4afefc7f594b84a888058f90ad4` |
| `full-suite.log` | `71d7c5da7b45d7a1585d0135d319f4f2f33d55a4bf0e92ead6ce57b2b1bde373` |
| `local-qa.json` | `e4df56f01c511a01f3486ac839af8bc83bc9e2c7dde496e3fb4f600a0b86ee0e` |
| `run_qa.py` | `5367d17952d266b3cdba3fd5383a5f70970bbc98a5ae05625fca8324132a48fc` |
| `focused-tests.log` | `ce0ae965db3ba21be4361f5285e4f1b6b4e2e8655fb69ffa0f252c0ec4ed06e3` |
| `execution.log` | `d4cc3694e85800424cbee1d4f25fddf3b055ab95de4a6f6e5c626fff52724631` |
| `reproduction-hashes.json` | `014b16f75cb0aff33640000cb994a0bcc039d5465e040e76dd00cb94dc22f8a6` |
| `exposed-crosschecks.json` | `9792da079cbeb5c6c9ca985f94340d3e4bc7f0080b178978d6790b6570666264` |
| `preservation.json` | `81c5e79c7ef53d549c4e6c75a9a56259feb7608f32ba7807de41637d1e71f4d9` |
| `main-rules.json` | `b1db53cb21755f153eae12a999e1267643094f6c794a56f960970618b72a6ef6` |
| `rulesets.json` | `f4aa74e7415e77dcf7499ffd95bed738d338fac113edf2717e427459ed3e090a` |
