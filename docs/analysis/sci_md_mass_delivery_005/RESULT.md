# SCI-MD-MASS-DELIVERY-005 consumer result

TWO_ASSAY_MASS_INADEQUATE_ON_DECLARED_OBSERVED_WINDOWS.

G1 / NO_GOVERNING_PHYSICS_CHANGE. The supplied-two-assay JSON consumer is implemented and verified against the exact producer runtime in [HANDOFF.json](HANDOFF.json). Production dependency lock/defaults remain unchanged. [Puckworks full result](https://github.com/trbrewer/puckworks/blob/research/sci-md-mass-delivery-005/docs/analysis/sci_md_mass_delivery_005/RESULT.md) records all condition/arm metrics, feasibility, numerical allowances, solute sums, fraction/horizon errors, identities and evidence hashes.

| Restricted axis | PRED | FIT-transfer |
|---|---|---|
| AXIS_A absolute adequacy | FAIL | FAIL |
| AXIS_B rate value vs fixed MASS | FAIL | FAIL |
| AXIS_C same-information competitiveness | FAIL | FAIL |
| AXIS_D two-assay fixed empirical vs first-only | FAIL | FAIL |
| AXIS_E MASS shape vs exponential | PASS | FAIL |

Primary balanced R / mean abs B is 1.082831 / 0.940604 pp (PRED) and 1.504431 / 1.398935 pp (FIT). Fixed MASS R is 0.836980 / 0.777754 pp. The primary earns neither adequacy nor rate-adaptation complexity. No comparator passes every condition in either panel; none replaces the primary or is adopted.

There are 42 shots, 14 conditions and 84 conditioning observations. The fixed primary support is 48 PRED + 113 FIT = 161 windows; all 252 states and 966 supported arm/window predictions qualify numerically. All 1008 intended records retain the seven source/domain gaps per arm. Full intended suffix status is INADEQUATE_WITH_INCOMPLETE_COVERAGE: definite failures survive missing coverage; original three-shot denominators remain. FIT-C01 restricted R / mean abs B = 1.328346 / 1.258551 pp; its full-suffix complete-shot mean abs B lower bound is 0.768421 pp, independently proving failure. Historical 004 remains FROZEN_EMPIRICAL_TRANSFER_INADEQUATE.

Actual estimation: 84 two-parameter updates, 168 analytical amplitudes, 84 primary scalar solves + 84 tighter qualification solves, 8567 scalar calls. Zero global curve refits/hyperparameter searches. The primary's local TDS sensitivities are [-0.980921,-0.075567] pp/pp to assay 1 and [0.162192,1.734369] pp/pp to assay 2. These are numerical sensitivities, not assay SDs or physical identifiability. Maximum primary solute allowance 9.9607822e-15 kg qualifies; numerical success does not establish predictive adequacy or real-time feasibility.

The independent pre-score receipt approved the exact frozen predictions before one exclusive scoring pass. [QA.md](QA.md) separates local software, hosted CI and final review. [README.md](README.md) documents actual synthetic/supplied-JSON consumer and producer prepare/freeze/score/report commands. Runtime pin remains 2fd6cc46b53cf52e7f0b2798d5ce43d7bfe0869e, tree8798d84d007674ceb5434744f183a4200eb6feda, distinct from later result commits.

SOURCE_INTERNAL / TARGET_EXPOSED / RETROSPECTIVE_TWO_ASSAY_CONDITIONED_COMPARISON. Pannusch/Schmieder source-derived results retain CC-BY-NC-3.0 treatment (Mendeley 10.17632/y2tz67f6ry.1), separate from software licensing. Raw observations, states, row predictions, per-shot results and full logs remain private. Source dates and UNKNOWN coffee-lot/roast confounding remain. Assayed-support sums are not measured whole-cup totals. No causal grind, kinetics or recipe-to-hydraulics claim.

PHYSICAL_VALIDATION=NOT_ESTABLISHED; GLOBAL_CURVE_REFITS=0; LOCAL_PARAMETER_ESTIMATION=84_TWO_PARAMETER_UPDATES_AND_168_AMPLITUDE_UPDATES; NATIVE_EWP_RUNS=0; PRODUCTION_DEFAULTS_CHANGED=false; PRODUCTION_DEPENDENCY_LOCK_CHANGED=false; FULL_INTENDED_SUFFIX_STATUS=INADEQUATE_WITH_INCOMPLETE_COVERAGE; PRS=OPEN_UNMERGED; MERGE_AUTHORIZED=false; LABORATORY_ACTION_AUTHORIZED=false; NO_SUCCESSOR_AUTHORIZED.
