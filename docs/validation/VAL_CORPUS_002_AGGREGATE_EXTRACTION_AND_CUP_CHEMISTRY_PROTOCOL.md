# VAL-CORPUS-002 Stage A: aggregate extraction and cup chemistry protocol

Status: `CORRECTED_FROZEN_PENDING_INDEPENDENT_REVIEW`
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
`c0 = 0.24827 g TDS/g beverage` (SE `0.00419 g/g`) and `lambda = 17.47261 g
beverage` (SE `0.48029 g`). Here `c0` is fitted outlet concentration and is not
the solver extractable fraction. Source `conc_in_cup` is already g/g: every
selected row must satisfy `TDS fraction = TDS mass/target beverage mass` within
an absolute `1e-12` tolerance. Waszkiewicz 9-bar TDS supplies twelve collected
5-second fractions over `[0,5]` through `[55,60]` s as a cross-source,
nonholdout time-shape comparison with no chemistry calibration. No 5-bar or
11-bar chemistry is inferred. The chemistry clock is
ambiguous: future reporting must show the source-reported clock and the existing
accepted fixed `+3 s` source-to-solver mapping, never an optimized shift.

The public source data are already observable. No holdout or independence claim
is made. No transfer observation may enter calibration or later retuning.
Schmieder species are reserved for a source-only one-solute limitation audit.

## Frozen parameterizations

P0 preserves the merged predecessor values without retuning:
extractable fraction 0.28 g/g, extraction rate 0.15 s^-1, saturation
concentration 180 kg/m3, and effective solute diffusivity 1e-9 m2/s.

P1 is `P1_SCHMIEDER_EXP7_REDUCED_EXPONENTIAL_MAPPING`. Its internally
consistent zero-dimensional mapping gives reduced initial inventory
`c0*lambda = 4.3379248847 g` and solver extractable fraction
`c0*lambda/20 = 0.216896244235`. With the declared source convention
`rho = 1.0 g/mL`, `Q = 2.0 mL/s`, and `lambda = 17.47261 g`,
`k = rho Q / lambda = 0.11446486815650324 s^-1`. Dimensions reduce to 1/s.
Saturation concentration and diffusivity retain the P0 values. Inventory and
rate are `SOURCE_DERIVED_REDUCED_LAW_MAPPING`, not directly fitted solver
parameters. This mapping neither exactly represents Eq. 3's discrete first
fraction nor identifies the PDE-local extraction rate physically.

P2 fixes extractable fraction `0.216896244235` and calibrates only one global
extraction rate in H1 at Experiment 7 to mean TDS masses at 20, 40, and 60 g.
H0 calibration, mode-specific rates, and transfer refitting are prohibited;
the same fitted rate applies unchanged to every H0/H1 production comparison.
The objective is equal-weight
mean squared relative error, optimized in log(k) from P1/10 to P1*10. The frozen
optimizer is bounded golden-section search, log-k tolerance 1e-8, at most 128
evaluations, lower-k tie break, and fail-closed behavior. It is not invoked in
Stage A. Every parameter’s provenance class is explicit in the parameter ledger.

## Hydraulic decomposition

H0 uses the arithmetic mean of unique replicate maximum-pressure metadata as
inlet pressure, zero-gauge outlet, and unchanged native permeability. It is a
limited native coupled diagnostic with no hydraulic fitting to chemistry.
H1 is `FLOW_CONDITIONED_EFFECTIVE_DARCY_CLOCK` using
`k = mu L Q/(A delta_p)`, source mean measured flow, exact merged geometry, and
a declared maximum-pressure-to-zero-gauge-outlet mapping. The source provides
maximum pressure, not a time-resolved basket pressure history; this sharply
limits the H1 claim. Its coefficient is a numerical conditioning value, not a
physical permeability inference or validation. Exact per-experiment values are
frozen in the execution contract. Compaction and Darcy–Forchheimer are disabled. The merged
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
and native/source-conditioned error ratios are frozen. Fixed-mass outputs use
deterministic linear interpolation of cumulative solute mass against cumulative
beverage mass; duplicate masses, missing targets, and extrapolation fail closed.
A zero denominator makes an H0/H1 error ratio undefined and requires reporting
the paired errors without an epsilon floor.

Axis contrasts are high-minus-low flow, coarse-minus-fine setting, and
high-minus-low temperature at each brew ratio. Each Waszkiewicz model value is
integrated outlet solute mass divided by integrated beverage mass over the
corresponding 5-second collection interval. Midpoint point-sampling and
extrapolation are prohibited, and the identical operator applies to both fixed
clock presentations. This comparison uses cross-source chemistry parameters
but same-source Waszkiewicz hydraulic conditioning and therefore carries
TDS/dissolved-mass soft circularity; it is not independent whole-solver
chemistry validation. Waszkiewicz metrics are
unweighted RMSE, MAE, bias, and early/middle/late residuals over the frozen
windows. Uncertainty-weighted results are secondary and use supplied
uncertainty only; none is invented for 2.5 s. There is no universal binary
physical-validation threshold.

The future 42-case OpenFOAM matrix covers seven Schmieder experiments, three
parameterizations, and H0/H1. It is not executed. The nine unique sensitivity
runs comprise one exactly reusable Exp-7 P1/H1 production baseline and two
nonbaseline factors for each of four parameters. Exact absolute values are
frozen. The analysis is `FINITE_RANGE_ONE_AT_A_TIME_SENSITIVITY` using
`[ln(y_high)-ln(y_low)]/[ln(p_high)-ln(p_low)]`; nonpositive or missing outputs
fail closed. Its 3-output by 4-parameter matrix has rank at most 3. Singular
values, declared rank tolerances, correlations, and equifinality are reported.
This is `NOT_STRUCTURAL_IDENTIFIABILITY`.

The execution contract separately inventories the at-most-128 P2 calibration
evaluations, 42 final production cases, and nine sensitivity identities. The
final valid P2 optimizer evaluation may replace only the final Exp-7 P2/H1
production case, and the sensitivity baseline may reuse only Exp-7 P1/H1, in
each case after exact input, solver-commit, and executable identity matching.
Every production case freezes source aggregation and conditions, base-config
hash, solver/executable identity, geometry, boundaries, hydraulic coefficient,
chemistry, timestep, 90 s end time, 16 ranks, write controls, observation
operators, completion/conservation gates, and external artifact identities.

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
