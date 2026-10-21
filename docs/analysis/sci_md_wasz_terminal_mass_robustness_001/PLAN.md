# SCI-MD-WASZ-TERMINAL-MASS-ROBUSTNESS-001

Fixed before computing terminal mass condition slopes, 2026-10-20.
G1 / NO_GOVERNING_PHYSICS_CHANGE. RESEARCH_ONLY / RETROSPECTIVE /
SOURCE_INTERNAL / TARGET_EXPOSED. PHYSICAL_VALIDATION=NOT_ESTABLISHED.
The owner's task authorizes one finite retrospective analysis and one draft,
unmerged EWP PR with auto-merge disabled.

- NEW_INFORMATION: original untruncated scale acquisitions provide a terminal
  beverage-mass increment observer independent of the processed endpoint derivative.
- DECISION_IF_POSITIVE: if the declining high-pressure sign survives all three
  supported windows and relevant brew deletions, retain that descriptive
  requirement conditional on acquisition support.
- DECISION_IF_NEGATIVE: identify the window/brew dependence and narrow the
  empirical requirement; do not select a favorable sensitivity window.
- DECISION_IF_NULL_OR_BLOCKED: preserve partial evidence, identify the exact
  source/reconstruction/support failure, and close with a limited or unresolved result.
- GRINDER_TO_CUP_LINK: distinguish a recorded beverage-delivery trend from a
  processing-dependent observation before interpreting hydraulic model applicability.
- REPEATED_BLOCKER: the new raw observer addresses #207's endpoint applicability
  gap; it neither repeats a fit nor repairs missing local physics or initial states.
- LOWER_COST_ALTERNATIVE: reuse authenticated original acquisitions and fixed
  descriptive arithmetic; no simulator, mechanism fit, or laboratory campaign.
- GOVERNANCE_CLASS: G1 / NO_GOVERNING_PHYSICS_CHANGE, exposed-data
  characterization, one independent scientific review and focused correction.

## Intake, authorities and scoped data preflight

Live main heads match preparation: EWP
`f93095abd58b31476ec331f3aa8d68feb98df9b0`; read-only Puckworks
`58075bbbce548e63d94106c96b918c1464221514`. No intervening changes.
Repository PR searches and the existing-data ledger identify no equivalent
terminal-mass task; related SCI-MD-010/011/012, dynamic-hydraulics, and mass-delivery
work remain complete and untouched. Active EWP PRs found at intake were #117
(evidence inventory) and #130 (dependency automation), unrelated to this question.

Read authorities: EWP AGENTS, onboarding, external-data use map, claim ceiling,
current state, controlling strategy, minimum-necessary-governance, available-data
policy/authority, data-first plan, existing-data programme/ledger; Puckworks
AGENTS/CLAUDE, onboarding and espresso data guide. Task-specific authorities:
`sci_md_mo_pressure_feasibility_001/`, `sci_md_010/FOLD_MEMBERSHIP.csv`,
`METRIC_CONTRACT.json`, `PRESSURE_RESPONSE_DIAGNOSTICS.json`,
`sci_md_011/OBSERVATION_INTERFACE.json`, `xsv_waszkiewicz_dynamic_hyd_001/`;
Puckworks `waszkiewicz2025/PROVENANCE.md`, `traces_per_brew.csv`,
`equilibrium_windows.csv`, `brewer_quadratic_params.csv`, loader/alias tests,
and `analysis/waszkiewicz_shot_level.py`. These files are FILES_INSPECTED,
not merely catalog metadata. No Pc/Qc calibration, H1 comparison, model selection,
completed mass reduction, or protected score will be repeated.

Original public source: [RadostW/espresso v1.0.1](https://github.com/RadostW/espresso/tree/fbc33d3380a9c8cff2467bae70fec7137a6ed46f),
commit `fbc33d3380a9c8cff2467bae70fec7137a6ed46f`,
[Zenodo 18046315](https://zenodo.org/records/18046315).
Inspect formatter, 57 top-level acquisition files, brewer calibration and
published aggregate. Verify exact prefix alias `12-8-6_alt` -> `12-8-6`.
Primary membership is the accepted EWP 56 unique physical IDs / 11 conditions;
the published 57-record aggregation is separately labeled lineage only.
Never infer condition from filename or admit `excluded/` files.
Data attribution: Waszkiewicz, Myck, Białas, Puciata-Mroczynska, Dzikowski,
Szymczak and Lisicki (2025), CC-BY-4.0 deposit data per accepted provenance.
Accompanying source software is GPLv3; inspect but do not copy its code.
Independent EWP implementation follows the observed algorithm. Raw payloads
remain outside Git with relative-path hashes and reproducible retrieval.
Availability is adequate for this bounded audit; physical acquisition ambiguity
may still limit inference. No general corpus-exhaustion or measurement recommendation.

## Frozen computation

Reconstruct median-p2 reference (kPa), nearest-half-bar rounding, `1-2.txt -> 1`
and rounded `1.5 -> 2` corrections; strict pressure-tolerance violations outside
`[max(0.9*median, median-50), min(1.1*median, median+50)]`.
Match the source's global `mask.any()` guard and reversed first-501-sample
`idxmax` semantics (including the all-false searched-prefix fallback), then
START_IDX=selected index+1; subtract its timestamp, milliseconds to seconds.
Truncate aligned samples at <=100 s; use NumPy gradient default edge_order=1,
SciPy SG(31,1) default mode='interp', then np.interp onto linspace(0,100,1000).
The debug CSV's 4-decimal serialization is not reloaded; the published means
are written to 6 decimals and Puckworks per-brew fields to 5 decimals.
Compare per-brew endpoints with half a 1e-5 serialization unit plus explicitly
reported floating arithmetic slack; published means with half a 1e-6 unit.
Record alignment, counts, support, last retained/next acquisition, endpoint
holding/brackets, and numerical differences. Record versions and input hashes.
Reproduce the historical canonical means and slopes from retained observations;
do not replace them with newly rounded reconstructions.

For original, untruncated, pressure-aligned masses only:

- PRIMARY q10 = [M(100)-M(90)]/10 g/s.
- SENSITIVITY q5 = [M(100)-M(95)]/5 g/s.
- SENSITIVITY q20 = [M(100)-M(80)]/20 g/s.

Linear interpolation requires an exact measurement or two actual brackets,
including a genuine post-100 acquisition from the same record. No extrapolation,
holding, nearest neighbor, smoothed derivative, monotone correction, negative
clipping, curve fitting, fourth window or post-hoc window selection.
Retain endpoint times/masses, width, fraction and exactness; inspect monotonicity,
duplicate times, finiteness, units, gaps, resets and continuity. Report calculable
but physically ambiguous brackets separately. No sensor-resolution or maximum-gap
acceptance rule is available or will be invented. Descriptive interval rankings
and negative steps are diagnostics, not automatic exclusions.

Freeze the accepted measured endpoint line-pressure mean for each condition,
for every observer and deletion. LOW <=5.25 bar; HIGH >=8.5 bar. Same condition
membership throughout. Equal arithmetic means over physical brews; unweighted
condition slope = sum((p-mean(p))*(q-mean(q)))/sum((p-mean(p))**2), exactly the
SCI-MD-010 estimator. Descriptive sample SD uses n-1 (undefined if n<2).
Report all condition counts/means, peak ties, slope differences, numerical signs.
Near-zero status means floating arithmetic resolution only (64 machine eps times
sum(abs((p-mean(p))*q))/sum((p-mean(p))**2)); this is not measurement uncertainty
or physical materiality. Physical near-zero significance remains unqualified.
Absent brews are explicit; never silently change a historical comparison cohort.
Retain full eligible IDs, common-support comparisons, and any unresolved 56-brew verdict.

Delete each of the 56 physical IDs once, paired across four observers. Recompute
the affected outcome mean only, keep pressure coordinates fixed, retain slope
changes/sign changes and applicability. Missing observers/empty conditions are
typed unavailable. Deletions outside a subset give no additional robustness
evidence for that subset. Deletion ranges are descriptive, not confidence intervals.

Assess the actual gradient/filter/truncation/interpolation composite, its edge
weights and acquisition timing, with a small deterministic synthetic illustration
separate from empirical effects. An ideal common nonnegative discharge kernel
preserves pointwise discharge order; cumulative mass order alone is insufficient.
Separate grids and instrument response require extra assumptions. Negative filter
weights alone do not establish an empirical processing artifact.

## Decision, verification and stopping

Report separate decisions A reconstruction, B operator order, C high-pressure
mass signs, D low-pressure mass signs, E brew influence, F physical applicability.
Distinguish averaged beverage-mass flow / instantaneous discharge, interpolation
/ instrument response, beverage outflow / puck hydraulic flux, aligned / physical
origin time, and material / initial-state variation. #207 remains valid within
its assumptions; full spatial/stochastic Mo2021 behavior is not inferred.

Focused checks cover mapping/aliases/manual corrections, exact alignment,
brackets/gaps/invalid records, original endpoint operator/serialization, constant
mass/linear ramp/negative increments, means/slopes/fixed pressures/deletions,
JSON/CSV consistency and deterministic rerun. Execute applicable source-and-boundary,
inexpensive-checks and hosted CI; retain one substantive independent AI scientific
review (not human merge approval). Correct material defects once as needed and
verify final PR head. No automatic follow-on.

Reproduction commands and exact receipts will be recorded with the result;
implementation belongs in existing scripts/tests locations and the compact
result bundle, with only necessary current-state/ledger pointers and source/QA
manifest bookkeeping. Preserve all prior scientific artifacts and production lock.


## Intake clarification before mass-window condition slopes

Inspection found that the accepted SCI-MD-010 values come from Puckworks
`equilibrium_windows.csv`, not the final flow of `traces_per_brew.csv`.
The initial expectation of equality between those two observers is false.
The four declared analysis observers are unchanged: historical means the actual
accepted equilibrium table, q10/q5/q20 remain fixed. Reconstruct both the original
truncated formatter and the accepted table separately. A full-record SG derivative
averaged over actual samples in [99.9,100.1] s reproduces all 57 accepted endpoint
flow/basket-pressure rows and sample counts within 5-decimal serialization.
This is a numerical lineage inference; its original producer script is not
retained in inspected Puckworks history. It is neither a new mass window nor a
replacement historical target. Restrict the historical-operator applicability
claim accordingly. One `7-1` final JSON record contains p2 but lacks t/m;
retain its p2 in the reference median, record the incomplete tail, and use only
the preceding complete measurements for interpolation. No measurement is filled.
