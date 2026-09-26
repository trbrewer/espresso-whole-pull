# SCI-MD-MASS-DELIVERY-002 research handoff

**Conditioning complexity is not earned:** TESTED_CONDITIONING_FAMILY_INADEQUATE.
MTF fails PRED-C01, and its balanced RMSE is slightly worse than frozen M0.
The setting-aware empirical model also fails adequacy and is not established as preferable.
G1 / NO_GOVERNING_PHYSICS_CHANGE. One audited scoring pass completed; M0 replay
matches every condition and balanced R/B/abs(B) exactly. No post-score fitting,
model selection or implementation change.

Cells below are mean shot RMSE / mean absolute shot bias, TDS percentage points,
then adequacy. All models retain 12 physical shots and all 72 eligible intervals.

| Condition | M0 | MT | MF | MTF (primary) | SETTING_AWARE_EMPIRICAL |
|---|---|---|---|---|---|
| PRED-C01 | 1.356431 / 0.534279 FAIL | 1.306770 / 0.515730 FAIL | 1.344773 / 0.529563 FAIL | 1.295798 / 0.511070 FAIL | 1.241255 / 0.513331 FAIL |
| PRED-C02 | 0.894086 / 0.189383 PASS | 0.940394 / 0.240510 PASS | 0.890037 / 0.177624 PASS | 0.935481 / 0.228570 PASS | 0.892596 / 0.177307 PASS |
| PRED-C05 | 0.772350 / 0.171814 PASS | 0.788508 / 0.188244 PASS | 0.932751 / 0.285847 PASS | 0.950758 / 0.302265 PASS | 1.066530 / 0.242885 FAIL |
| PRED-C06 | 1.080891 / 0.190768 FAIL | 1.095653 / 0.206470 FAIL | 0.958784 / 0.074983 PASS | 0.970717 / 0.080008 PASS | 1.012994 / 0.104060 FAIL |
| Balanced | 1.025939 / 0.271561 | 1.032831 / 0.287738 | 1.031586 / 0.267004 | 1.038188 / 0.280478 | 1.053344 / 0.259396 |


MTF decision axes A absolute adequacy, B material gain over M0, C empirical
competitiveness and D empirical superiority all FAIL. Its comparative 0.10 pp
margins against empirical pass, but C also requires absolute adequacy. No threshold
is numerically unresolved. MT/MF remain diagnostic ablations, not replacement
primary winners. Ramps C03/C04/C07/C08 are NOT_ADJUDICATED_VARIABLE_SETTING_INPUT.

The producer verifies both nominal source-design contracts, full measured mass
prefixes and analyte-specific TDS identities. FIT uses five settings/15 shots/90
assays at grind 1.7 and dose 20 g. Its three within-setting replicate CV folds
retain 29/30/30 supported intervals, and select empirical K=5/lambda=0; K=9/lambda=0
is excluded for rank deficiency. Partial CV support is not an adequacy claim.
Exactly 192 nonlinear starts/13,207 actual residual calls and 124 linear solves;
zero failed starts. Maximum primary integration allowance 1.392e-14 kg, below
1e-9 kg. Parameter identification and causal recipe effects are not established.

The consumer adds explicit M0/MT/MF/MTF/SETTING_AWARE_EMPIRICAL selection,
constant nominal-temperature/source-code inputs, interval solute/TDS and
conditional stopping-mass queries. It verifies exact producer commit/tree and
all wrapper/kernel/model hashes in an isolated namespace. No installed-package
fallback, implicit candidate choice or EWP runtime default. See [README.md](README.md).

Producer runtime commit `cec97741e72b126f04f05b73691d9223bbdb148f`, tree
`1b30d6d6152baedc28fab42419a2c33d61b8694b`. The immutable
[complete producer report](https://github.com/trbrewer/puckworks/blob/029b57c00a17d298f45728216f0168a6bcfc082f/docs/analysis/sci_md_mass_delivery_002/RESULT.md)
contains source qualification, all selection/coverage/rank/conditioning diagnostics,
per-site mass extents and borrowed shape support, numerical checks, decision details
and permissioned-data reproduction commands. [HANDOFF.json](HANDOFF.json) binds
runtime and result-record identities separately; no production lock is advanced.

Source and numerical statuses: qualified for the declared constant nominal-code,
mass/TDS contract. Scientific status: tested MTF family inadequate. Independent
pre-score audit: APPROVED; final exact-head/owner review separate. Software: 77
producer and seven consumer focused tests pass; initial full-suite environment/
manifest failures and passing affected reruns are retained in SOFTWARE_QA.json.
Local source/static/historical/change/shell/JSON/boundary checks pass; hosted CI
status must be read from live exact-head checks on
[Puckworks #280](https://github.com/trbrewer/puckworks/pull/280) and
[EWP #186](https://github.com/trbrewer/espresso-whole-pull/pull/186).
Both task PRs remain OPEN/UNMERGED for owner disposition. Predecessor #278/#184
were live-verified merged; their source/results/artifacts were not rewritten.

SOURCE_INTERNAL; TARGET_EXPOSED; RETROSPECTIVE_MODEL_DEVELOPMENT_COMPARISON.
Task choice used exposed predecessor results; March is not newly blind.
Nominal source codes are not measured flow, and temperature is not a local puck
measurement. No pressure, flow, time, mass attainment, inventory, mechanism or
universal coffee/grinder-transfer claim. Modeled gaps are not measured cup totals.

Source-derived models/aggregates retain Pannusch/Schmieder attribution and
CC-BY-NC-3.0 treatment, [Mendeley DOI 10.17632/y2tz67f6ry.1](https://doi.org/10.17632/y2tz67f6ry.1),
distinct from first-party software licensing. No restricted raw or row-level
measurements/predictions are committed.

```text
PHYSICAL_VALIDATION = NOT_ESTABLISHED
NATIVE_EWP_RUNS = 0
PRODUCTION_DEFAULTS_CHANGED = false
PRODUCTION_DEPENDENCY_LOCK_CHANGED = false
NO_SUCCESSOR_AUTHORIZED
```
