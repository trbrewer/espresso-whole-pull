# SCI-MD-WASZ-RESTART-RESPONSE-001

Design recorded on 2026-10-20 **after source authentication and pressure/time
inspection, before evaluation of mass contrasts**. This file is preserved in
its initial Git commit. G1 / NO_GOVERNING_PHYSICS_CHANGE; RESEARCH_ONLY /
RETROSPECTIVE / SOURCE_INTERNAL / TARGET_EXPOSED. This is non-scoring exposed
characterization, not target blindness, a new holdout or independent validation.
One compact result bundle, one substantive independent scientific review,
at most one bounded material correction. PHYSICAL_VALIDATION=NOT_ESTABLISHED.

## Intake and scoped availability preflight

Actual EWP base: `adb50c634f0e7959eb1e5a63405ee881cde7be72`, tree
`a92736aa23a1637db85ae23a9c6f57876a27812b`; live read-only Puckworks research
main: `58075bbbce548e63d94106c96b918c1464221514`, tree
`a722e85bf919d038931f97af8c8437c06e922638`. Both match review snapshots;
no intervening main changes at intake. GitHub repository IDs are respectively
1315029743 and 1296849686. Production lock remains
`fc61c4670ec7bf801e40bb391aab16048b8da26b`, tree
`1d553e44ee2f7480a5df521560801b478618cc84`. The legacy local directory named
puckworks-pinned is at `352dacd51015d95a3b5a5b3e1a8fb331419d78b0`; it is not
used as production or research authority and is not modified. No Puckworks
execution or dependency refresh is needed.

Repository task paths, programme, ledger and GitHub issue/PR searches for
restart found no equivalent completed or active study. Related #207 and #209
are preserved. The accepted 56-physical-brew / 11-condition cohort, including
its alias treatment, is unchanged. This acquisition has separate identity
`waszkiewicz2025_fig10_restart_puck_01`; six episodes share that one identity.
It is not appended as a 57th accepted cohort brew.

Read: EWP AGENTS, onboarding, current state, claim ceiling, external-data use
map, data-first plan, available-data policy/authority, minimum governance,
controlling strategy, programme/ledger, #207 and #209 bundles; Puckworks
AGENTS/CLAUDE/onboarding, data/development guides, Waszkiewicz provenance/card,
relevant register and manifest entries, and PROTOCOL_kappa_t_discrimination.
The latter's rebrew proposal is conceptual prior work, not an executed analysis
or a chemical-exhaustion measurement for this acquisition.

- NEW_INFORMATION: a separate within-puck interrupted-brew acquisition, with
  original time, line pressure and unsmoothed cup mass actually inspected.
- DECISION_CONSEQUENCE: supported later differences with justified pressure
  and observation comparability retain a conditional restart-response constraint;
  early differences with supported later attenuation prioritize transient,
  storage and observation explanations; pressure mismatch, drift or apparatus
  ambiguity retain arithmetic but withhold an interruption-specific requirement;
  inadequate support closes the question with exact unavailable comparisons.
- GRINDER_TO_CUP_LINK: measured delivery after pressure cycling constrains
  hydraulic-state and observation assumptions, conditional on their mapping.
- REPEATED_BLOCKER: this adds a distinct within-puck record, not another fit
  to the already used between-brew rankings; those rankings are not reopened.
- LOWER_COST_ALTERNATIVE: authenticated existing observations and arithmetic;
  no solver, fit, new F, simulation, laboratory recommendation or successor.

FILES_INSPECTED: original acquisition and original plotting script in an existing
verified external cache; relevant source and Puckworks documentation; accepted
EWP result bundles. CATALOG_ONLY: other chemistry/CT/PSD/calibration families
in the guides/register. No same-record chemistry, temperature, independent
puck pressure, valve-command trace, response calibration or uninterrupted
control is established. Missing joins are scoped to this record, not a corpus
exhaustion claim. Active protect_main ruleset 19901931 requires
source-and-boundary and inexpensive-checks; read via GitHub API because the
connector lacks ruleset inspection. Final PR must remain draft/open/unmerged,
auto-merge disabled.

## Authenticated source and support

Original repository: https://github.com/RadostW/espresso at exact revision
`fbc33d3380a9c8cff2467bae70fec7137a6ed46f`, retrieved previously by Git clone
and reused only after clean-checkout and Git-object verification.

| File | Git blob ID (not SHA-256) | SHA-256 | Bytes |
|---|---|---|---:|
| measurements_brew_restarting/brew_restarting.txt | 7940d6aa008e7cae37bb1bf8ceece44fa07d0bff | e82430cde25574140d2026882a883fba21a0f0ac6d9588b15df22571836f68e9 | 163514 |
| plot_singlepanel_brew_restarting.py | f93c4c2abb6847d70b21df669bd6940089c226b3 | aa35ade18cc8b6946164279d6e2e82337435c3165698be932ff3d0f32b47cd74 | 1783 |

Data attribution: Waszkiewicz, Myck, Białas, Puciata-Mroczynska, Dzikowski,
Szymczak and Lisicki (2025), CC-BY-4.0 deposit data per accepted provenance and
[Zenodo 18046315](https://zenodo.org/records/18046315). Accompanying software
is GPLv3, inspected only; independently implement the mathematics, without
copying code or running the upstream pipeline. Raw payloads/full logs stay
outside Git, with source-root-relative locators and hashes in the manifest.
[Primary paper](https://arxiv.org/html/2512.21528v1), apparatus II.2–II.3 and
Figure 10 discussion inspected: pump-side pressure and cup scale; closed-valve
periods near 3 bar and possible backflow are source descriptions. Exact valve
commands, same-record solute exhaustion and internal channel images are not
measurements furnished by this acquisition. Do not promote p1 to puck pressure.

1818 rows, fields U/v1/v2/p1/p2/m/t present; original clock 0.126–170.031 s;
1817 adjacent intervals: 1016 at 93 ms, 678 at 94 ms, 123 at 95 ms. No clock
duplicates/reversal. ACTIVE iff p2/100 > 5.5 bar, defined from pressure alone;
this labels states, not flowing-puck pressure or pressure equivalence.
E0 2.464–77.363; E1 82.974–93.913; E2 99.805–110.559;
E3 117.760–128.327; E4 135.621–146.094; E5 152.452–167.319 s.
Keep all seven low-pressure episodes and both adjacent transition brackets.
The first/last active samples define support, not measured valve commands.

## Fixed observer, windows and comparisons

`t` is milliseconds, time=t/1000 s; p2/100 is line pressure in bar; m is cup
mass in g per the plotting method. Other fields remain uninterpreted.
Preserve original row indices and clock everywhere. M_tilde uses linear
interpolation only between adjacent valid original acquisitions; qbar[a,b]
= (M_tilde(b)-M_tilde(a))/(b-a), g/s. Retain both endpoint indices, times,
masses, bracket widths, fractions and exactness. No extrapolation, holding,
nominal-10-Hz replacement, smoothing, monotonic repair, reset repair or clipping.
Missing/nonfinite records, nonincreasing time, explicitly documented broken
edges and gaps outside this inspected 93–95 ms cadence do not supply an
interpolation bracket. The 95 ms support envelope is an acquisition-specific
software support check fixed from time inspection, not a physical response or
measurement-accuracy claim. Report all signed mass steps/extrema and physical
ambiguity; absence of a large jump does not establish no scale handling.

Exactly three designs:

| Design | D (s) | symmetric guard g (s) |
|---|---:|---:|
| PRIMARY | 2 | 2 |
| SENSITIVITY_A | 3 | 2 |
| SENSITIVITY_B | 2 | 3 |

Each restart: early [s+g,s+g+D], later [e-g-D,e-g]. Require supported,
nonoverlapping intervals for early/later comparison; never shorten or move
windows to recover eligibility. Preserve unavailable outcomes with reasons.
E0 reference is [e0-g-D,e0-g], not wetting. Exactly three consecutive width-D
initial drift windows end at e0-g; the third is the reference. No trend fit,
earlier search, extrapolated uninterrupted counterfactual or fourth design.
A guard does not prove transient completion: say later within the recorded
active episode and give actual times. Compare designs on their common subset.

All eligible restarts: A=later minus E0 later; B=later minus immediately
preceding episode later (E1 duplicates A); C=later minus early; D=early minus
E0 later. Store components, signed g/s differences, midpoint time separation,
identities/support and pressure diagnostics. Absolute differences are primary;
no ratios are needed. Initial drift includes both consecutive differences.
Low-pressure periods use first-to-last low samples for supported mass changes;
never subtract these as a storage correction or call them puck throughput.

## Pressure and source-observer lineage

Pressure uses piecewise linear interpolation on original adjacent acquisitions,
with original indices/history and endpoint support retained. Report exact
trapezoidal time-weighted mean, extrema, original-sample quartiles (explicitly
sample weighted), endpoint change/direction, total variation and maximum
excursion from the mean. For each equal-duration contrast, form the union of
both relative-time knot sets and integrate the squared linear trajectory
difference analytically: RMS=sqrt(sum dt*(d0²+d0*d1+d1²)/3 / D).
Also report maximum absolute mismatch and signed mean-pressure difference.
No dynamic warping, segment selection, pressure tolerance or fitted F.

Reconstruct the source lineage separately: trailing five-sample mean of m,
then its successive difference divided by the current adjacent dt (seconds).
Mean missing for rows 0–3; derivative missing for rows 0–4. Verify via the
independent identity (m[i]-m[i-5])/(5*dt[i]) for complete data. This is sample
count smoothing, not the five-interval mass change divided by total elapsed
time on irregular acquisitions. No maximum derivative or selected peak is
primary evidence. No #209 alignment, truncation, SG filter or endpoint producer.

## Interpretation and completion

Level 1: recorded delivery on exact intervals, cumulative versus successive
changes, early/later pattern and fixed-design dependence. Physical uncertainty
is uncalibrated; serialization precision is not sensor accuracy. One physical
puck, no independent episode replicates, p-values, row bootstrap or population
claims. Missing later support is not evidence of transient-only behavior.

Level 2: candidate hypothesis q(t)=F(P_line(t)), time-invariant and memoryless,
under stable apparatus, other relevant conditions and observation response.
For nonlinear F, average F(P) matters, not F(average P). Approximate trajectory
matching cannot exclude an unrestricted steep/nonlinear F. Without independently
justified pressure-response bounds and observation comparability, quantitative
pressure exclusion is unresolved. A model reproducing the recording must map
its predictions through a suitable observation operator; no particular puck
state variable is automatically required.

Level 3: rearrangement/permeability, continued dissolution, temperature/viscosity,
stored liquid/transit, machine/valve behavior, scale response and ordinary time
evolution remain distinct explanations to assess. No same-record chemical
exhaustion, observed channel formation or interruption-specific causal effect
is established. Pressure cycling, time and cumulative delivery co-evolve.
#207's scoped theorem and #209's historical producer-lineage caveat stand;
full spatial/stochastic Mo2021 behavior is not adjudicated.

Implement focused scientific failure-mode tests and deterministic reproduction,
run applicable repository and hosted checks, obtain one independent AI scientific
review with direct representative recomputation. Keep all prior artifacts,
solver/defaults/lock and Puckworks unchanged. Close with the actual result and
bounded development consequence, including informative null/limited outcomes.
No automatic successor, fit, solver port, campaign or laboratory recommendation.
