# VAL-CORPUS-002 Stage A: aggregate extraction and cup chemistry protocol

Status: `FROZEN_PENDING_INDEPENDENT_REVIEW`  
Evidence class: `RECONSTRUCTION_OR_CALIBRATION`  
Change declaration: `SOURCE_SCENARIO_CHANGE_ONLY`

This is a prospective protocol freeze. Stage A authorizes no OpenFOAM build or
execution, parameter fitting, optimizer invocation, governed scoring, or
model-versus-source metric calculation. Physical validation is not established,
VAL-CASE-002 is not started, and new governing physics is not yet justified.

## Exact foundations

The protocol starts from merged main
`0a5c146078da5d5f88b344b20e7b81042bf27ddb`, tree
`12fdbc542270e2765e2071d83c21812951f892e8`. The merged validation framework is
used unchanged. Its controlling standard is
`docs/validation/VALIDATION_OPERATING_STANDARD_V1.md`; the directly used record
semantics and validation utilities remain those pinned by the merged VAL-001
registries and schemas. Runtime Puckworks remains locked at commit
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`. Evidence is read only from snapshot
commit `9c52c94edb27b461b6e7a4d471d29f3cef9d053e`, tree
`44d6539096648777f78c4db83f0985d5bd16e352`; no Puckworks data are copied here.

The evidence manifest records every directly consumed file, its SHA-256,
rights, definition, units, admissibility, circularity, and role. Candidate
sources not in the primary cohort receive exactly one explicit treatment in
the adjudication record. Missing geometry, pressure histories, clocks,
uncertainties, species mappings, and chemistry remain unavailable.

## Mandatory cohorts and partitions

Schmieder Experiment 7 is the sole local reconstruction anchor: DoE central
point, 20 g dose, 2.0 mL/s target flow, grinder setting 1.7, 89 °C target, six
replicates, and TDS only for governed aggregate comparison. Brew ratios 1/1,
1/2, and 1/3 map to 20, 40, and 60 g beverage. Replicate observations, means,
sample standard deviations, ranges, and counts are frozen machine-readably.

Metadata alone selects Experiments 1–6 as low flow, high flow, fine grinder,
coarse grinder, low temperature, and high temperature respectively. The
selector does not inspect TDS, mass, or concentration outcomes. These axis
experiments are fixed-parameter, within-campaign out-of-fit comparisons, not
sealed holdouts. Experiment 7 and Experiments 1–6 are disjoint.

The source equation is `c(m) = c0 exp(-m/lambda)`. The Experiment-7 TDS fit is
`c0 = 0.24827 g/g` (SE `0.00419 g/g`) and `lambda = 17.47261 g beverage` (SE
`0.48029 g`). Waszkiewicz 9-bar TDS supplies twelve points at 2.5 through 57.5
s as a cross-source, nonholdout time-shape comparison with no chemistry
calibration. No 5-bar or 11-bar chemistry is inferred. The chemistry clock is
ambiguous: future reporting must show the source-reported clock and the existing
accepted fixed `+3 s` source-to-solver mapping, never an optimized shift.

The public source data are already observable. No holdout or independence claim
is made. No transfer observation may enter calibration or later retuning.
Schmieder species are reserved for a source-only one-solute limitation audit.

## Frozen parameterizations

P0 preserves the merged predecessor values without retuning:
extractable fraction 0.28 g/g, extraction rate 0.15 s^-1, saturation
concentration 180 kg/m3, and effective solute diffusivity 1e-9 m2/s.

P1 maps the source fit directly: extractable fraction 0.24827 g/g and initial
extractable mass 4.9654 g for a 20 g dose. With the declared source convention
`rho = 1.0 g/mL`, `Q = 2.0 mL/s`, and `lambda = 17.47261 g`,
`k = rho Q / lambda = 0.11446486815650324 s^-1`. Dimensions reduce to 1/s.
Saturation concentration and diffusivity retain the P0 values.

P2 fixes P1 extractable fraction and calibrates only extraction rate to the
Experiment-7 mean TDS masses at 20, 40, and 60 g. The objective is equal-weight
mean squared relative error, optimized in log(k) from P1/10 to P1*10. The frozen
optimizer is bounded golden-section search, log-k tolerance 1e-8, at most 128
evaluations, lower-k tie break, and fail-closed behavior. It is not invoked in
Stage A. Every parameter’s provenance class is explicit in the parameter ledger.

## Hydraulic decomposition

H0 is the unchanged native coupled solver, with no hydraulic fitting to TDS or
cup-solute data. H1 is uniform saturated Darcy conditioning using
`k = mu L Q/(A delta_p)`, source mean measured flow, exact merged geometry, and
a declared maximum-pressure-to-zero-gauge-outlet mapping. The source provides
maximum pressure, not a time-resolved basket pressure history; this sharply
limits the H1 claim. Compaction and Darcy–Forchheimer are disabled. The merged
viscosity 0.000315 Pa s and 3 s ramp are held fixed because no governed
temperature-property relation or source ramp history is available. Thus the
temperature axis carries an explicit mapping limitation.

A reduced source-clock reference uses measured beverage flow and the same
aggregate inventory law. It is `DIAGNOSTIC_NOT_OPENFOAM_NOT_VALIDATION`.
Waszkiewicz uses the exact corrected WP03-002 9-bar case and executable identity
recorded in the decomposition record. Stage A changes neither.

## Outputs, metrics, sensitivity, and interpretation

Future mandatory outputs include cup-solute mass, TDS, extraction yield, target
mass time, interval flow, hydraulic and balance residuals, boundedness, and
completion. Replicate means, sample SDs, ranges, and counts are retained without
an invented uncertainty floor. Absolute and declared-denominator relative error,
three-mass RMSE, standardized residual where SD exists, observed-range/SD counts,
and native/source-conditioned error ratios are frozen.

Axis contrasts are high-minus-low flow, coarse-minus-fine setting, and
high-minus-low temperature at each brew ratio. Waszkiewicz metrics are
unweighted RMSE, MAE, bias, and early/middle/late residuals over the frozen
windows. Uncertainty-weighted results are secondary and use supplied
uncertainty only; none is invented for 2.5 s. There is no universal binary
physical-validation threshold.

The future 42-case OpenFOAM matrix covers seven Schmieder experiments, three
parameterizations, and H0/H1. It is not executed. The nine unique sensitivity
runs comprise one P1 baseline and two nonbaseline factors for each of four
parameters. Exact absolute values are frozen. Future finite differences report
normalized sensitivities, Jacobian, singular values, rank at declared relative
1e-8 and absolute 1e-12 tolerances, correlations, and equifinality. This is
practical local sensitivity, not proof of structural identifiability.

Native failure improved by H1 implicates hydraulic mismatch; failure in both
modes leaves aggregate chemistry/source-law mismatch. Successful P2 local fit
with failed fixed transfer is `LOCAL_RECONSTRUCTION_ONLY`. Preserved direction
and scale under fixed P1/P2 supports only
`SOURCE_SPECIFIC_AGGREGATE_CHEMISTRY_SUPPORT`. Waszkiewicz failure is
`CROSS_SOURCE_TIME_SHAPE_TRANSFER_FAILURE`. Species divergence identifies lost
information but neither uniquely attributes aggregate residuals nor authorizes
multispecies physics.

## Stage-B gate

Stage B requires independent review of this exact frozen head and a separate
human-owner execution authorization. Any prospective amendment must precede
observation. Final reporting must declare `SCIENTIFIC_RESULT_DISPOSITION`,
`VALIDATION_FRAMEWORK_DISPOSITION`, and `CLAIM_CEILING`. Until then execution,
calibration, fitting, and governed scoring remain prohibited.
