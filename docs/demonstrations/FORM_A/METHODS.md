# Form A reporting definitions and retained evidence

This closeout performs no refit or CFD rerun. It uses Waszkiewicz et al. (2025), [Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0, with the same 56 source hashes and masks as E1. Saved tuples come from [PW D0](https://github.com/trbrewer/puckworks/blob/dce84b22b99f114225eabb76f29014a5fc3efe5d/docs/research/PRESSURE_PEAK_STAGE_D0/RESULT_TABLE.csv).

The primary matrix is 23 A0 constants plus 23 A1 constants and 56 A1 histories. A2 has ten retained campaign constants, one probe, its step studies and superseded numerical diagnostics; 69 held cases were never started. A2 has no capability grade. Every execution is counted once in the manifest; reused Xc normalization cases carry a second role without additional core-hours. Historical E1 runs are references, excluded from new-task core-hours.

## Observation and censoring

Each raw trace is authenticated against the original E1 hash. PW raw_trace establishes the stable-pressure clock; clean_course and sustained_onset reproduce the original observed onset exactly. Simulated cup beverage mass is resampled onto the original timestamps on common native/source support before mass-to-flow differentiation and the 31-sample, order-1 Savitzky–Golay filter. Initial zero cup mass is the retained fresh-start state at time zero; terminal mass is never extended. The detector requires strict mass >0.5 g and flow >0.1 g/s continuously for at least 2 s and reports the interval start. Form A M remains outlet liquid grams.

A valid trace with no confirmed interval is censored at the latest retained sampled t_j satisfying T_last−t_j≥2 s. Its squared-error contribution is max(0,c_i−observed_i)². Missing/corrupt evidence is unavailable, never a censored brew. Coverage is explicit; an incomplete cohort receives no 56-brew score. Any censor makes the RMSE a lower bound: existing MISSES applies only when that bound exceeds 4.53 s; otherwise NOT_SCORED/unresolved. Intervals for a bound are labeled as such. Front arrival is a separate descriptive quantity, with its own 100-s censor.

| Arm | Available/intended | Detected | Censored | RMSE or lower bound, s | 95% interval | Grade |
|---|---|---|---|---|---|---|
| A0 | 56/56 | 51 | 5 | ≥14.415 | [6.661, 27.285] | MISSES |
| A1 | 56/56 | 52 | 4 | ≥16.293 | [6.499, 29.059] | MISSES |
| E1 | 56/56 | 56 | 0 | 8.570 | [6.163, 10.875] | MISSES |

The separate [native descriptive onset comparison](DESCRIPTIVE_ONSET.md) reports A0/A1 constants, signed condition errors, sharp fronts, grid minima and paired differences of censor-aware RMSE lower bounds. It does not change grades.

All intervals above are conditional on transferred fits; intervals in censored rows describe the RMSE lower bound. Per-brew censor bounds, observation timestamp hashes, detector support and eleven condition medians appear in the onset CSVs. The old A0/E1 matched-constant front-versus-observed-onset RMSE 8.627208878837111 s is preserved solely as a superseded diagnostic, with no grade. The retained E1 history front diagnostic is 8.927776300556106 s, also ungraded.

## Hydraulic comparisons and peaks

Endpoint/trace scoring remains liquid ρQ against scale-derived observed beverage flow. Native instantaneous beverage flow is ρQ/(1−instantaneous TDS); its endpoint difference from ρQ is an ungraded ENDPOINTS.csv diagnostic. Detector flow instead comes from differentiation/filtering of the resampled beverage mass.

The empirical Python A prediction starts M at stable-pressure zero. Its recomputed held-out endpoint score is 0.153001235551 g/s. The two delayed evaluators use ordinary-fold tuples and preserve the original absolute pressure times. The A0 delay is authenticated against retained E1 geometry, initial state, pressure history and clock, with the unchanged R0 front integral as fallback. A1 delay is used only for the A1-delay evaluator. The reduced A0 comparator has no beverage mass, solute history or detector onset.

Primary trace masks are observed onset+2 through 100 s; companion masks are 5 through 100 s. B1, E1, native A0/A1 and all three Python predictions share these masks. D0 full-support trace scores are not substituted. Late-trend windows beyond native support remain unscored. The slope is the inherited regression through the 9/11/13 condition means (mean actual endpoint pressure for histories, nominal for constants). Individual residuals at 1, 2 and 3.5 bar remain visible.

PAIRED_COMPARISONS.csv reports both scores and A1−A0 for endpoint, primary trace and companion trace. Native DESCRIPTIVE_ALL constants are descriptive: the eleven nominal constants are compared with their 56 observed brews; CONSTANT_COMPARISONS.csv retains differences at all 23 native pressures. The held-out comparison uses the reduced A0 comparator, qualified by A0 parity. Each interval is computed from paired differences on the same condition and whole-brew draws: 1,000 resamples, seed 20261103, conditional on transferred fits. Differences of marginal intervals are never used.

D0 capacity peak 5.998561 [5.769911, 6.272472] bar uses saved parameter refits. Solver endpoint peaks use a finite 100-s constant sweep and bracketed three-point quadratic interpolation at 0.25-bar spacing; no statistical interval is inferred for a deterministic sweep. The nominal peak grade is separate and uses E1’s unchanged condition-resample bands. These uncertainty concepts are not interchangeable.

| Arm | Peak at dt=0.0025 / 0.005 s, bar | Maximum endpoint change at 2/6/11, g/s | Maximum front change at 2/6/11, s |
|---|---|---|---|
| A0 | 6.012876163 / 6.012898726 | 6.00037388e-06 | 5.00932629e-13 |
| A1 | 6.009086046 / 6.009062271 | 1.0652782e-05 | 5.00932629e-13 |
| A2 | 6.009076127 / 6.009076116 | 4.78823316e-06 | 0.00097029711 |

A0/E1 constant front times agree within 5.01e−13 s at all eleven nominal pressures, well within one time step ([comparison](A0_FIRST_DRIP_COMPARISON.csv)). The saved G1 uniform saturated check has maximum Python/native endpoint difference 1.19494097e−5 g/s; 14 disabled-path outputs were byte-identical to the retained main build. The 6.57e−14 s analytic/native wetting difference verifies the implemented relation, not agreement with measured onset.

The pre-campaign study selected 0.005 s because these reported quantities were stable under halving the step; no extractable-inventory gate was used. A0/A1 controls are unchanged. A2’s earlier pressure-tolerance diagnostics and every superseded run remain separately accounted for.

## Retained failed qualifications

The original concentration check remains failed. Recovery reads retained config, traces, logs, runtime and hashes; it records native completion separately from numerical qualification, without rerunning, clipping or relaxing a bound. All 56 A1 histories remain in the hydraulic assessment because viscosity is constant and concentration does not feed back into A1 permeability.

| Brew | Maximum C versus 180 kg/m³ | Worst time, s | Exact final excess solute, g | Worst-time excess upper bound, g | Beverage mass at detector onset, g | Excess bound over onset support, g |
|---|---|---|---|---|---|---|
| 1-2 | 180.000000020847 | 94.215 | 1.1005331359615781e-12 | 1.98543e-10 | 0.5072580915072928 | 0.0 |
| 2-3 | 180.000000028198 | 88.590 | 9.405560272048749e-13 | 2.68552e-10 | 1.393481156784361 | 1.4248560849712975e-10 |
| 2-5 | 180.000000048188 | 80.945 | 9.415179941455124e-13 | 4.58933e-10 | 2.7778899196306654 | 2.348667207808744e-10 |

Brew 1-2: onset mass support 57.786–62.836 s; first positive excess 72.915 s, worst excess 94.215 s. First/worst violation after support: True/True.
Brew 2-3: onset mass support 70.162–75.208 s; first positive excess 71.415 s, worst excess 88.590 s. First/worst violation after support: False/True.
Brew 2-5: onset mass support 86.333–91.380 s; first positive excess 74.430 s, worst excess 80.945 s. First/worst violation after support: False/False.

Exact final excess mass integrates max(C−180,0) over cell pore liquid volume, using retained final porosity/saturation fields, authenticated global cell addressing and the probe’s saved geometric cell volumes. Cell fields were not saved at every intermediate time: an exact integral at an unsaved worst/onset timestamp is unavailable. The reported upper bound there is max(C_max−180,0) times the retained total pore liquid volume. Zero over the observer support implies zero excess integral there. These reporting calculations neither modify concentration nor change qualification. Follow-up outside this PR: consider a relative tolerance on the concentration-bound check.

## Probe and figure captions

A2 was retired after partial execution. Its increasing recovery factor cannot delay physical front arrival relative to A1 under the same prescribed pressure history. The selected extraction normalization also limits recovery to approximately 0.737, bounding the descriptive constant-pressure liquid-flow maximum at approximately 1.551 g/s. These properties make this particular arm a poor route to repairing the identified wetting and flow-scale mismatch. Its full capability campaign was not completed.

Xc at 6/9/11 bar is 0.8294438807 / 0.8422833432 / 0.8524326302. The [final normalization record](VERIFICATION_FINAL.json) separates the algebraic recovery cap 0.737079628 from the probe’s numerical observations. The 9-bar A2/A1 flow ratios at 10/20/40/60/100 s are 1.254014 / 1.155075 / 0.965114 / 0.810643 / 0.742525.

**Endpoint figure:** Observed means/ranges use scale-derived beverage flow; Python A, A0 and A1 show DESCRIPTIVE_ALL liquid-flow predictions at 100 s. Python original has no wetting delay. A2 markers are retained partial constants and its single 9-bar probe, not a completed sweep or grade. Connecting lines do not supply an uncertainty interval.

**Onset figure:** All eleven nominal medians appear in full-range panels; right panels expand 3.5–13 bar. Sharp-front arrival is descriptive, plotted against observed detector onset for context. The lower panels use the full B0c beverage-mass operator. A0 and dashed A1 constants are descriptive; solid E1/A1 curves use measured histories. Nested triangles at 1 bar show the overlapping median lower bounds from actual censor times (front bounds remain 100 s); unavailable evidence is omitted and its coverage reported. A2 is retired and receives no completed onset curve or grade.

[Endpoint flow](ENDPOINT_FLOW.png) · [Front and detector onset](FIRST_DRIP.png) · [Probe observations](A2_PROBE.csv) · [Qualification details](QUALIFICATION_FAILURES.json).
