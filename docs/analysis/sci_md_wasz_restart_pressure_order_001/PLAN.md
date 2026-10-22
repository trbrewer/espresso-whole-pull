# SCI-MD-WASZ-RESTART-PRESSURE-ORDER-001

Recorded 2026-10-22 before the new production calculation. G1 /
NO_GOVERNING_PHYSICS_CHANGE; RESEARCH_ONLY / RETROSPECTIVE / SOURCE_INTERNAL /
TARGET_EXPOSED / NONSCORING; PHYSICAL_VALIDATION=NOT_ESTABLISHED.
The motivating margins and counts have already been inspected. This is neither
target-blind parameterization nor a holdout score. The owner's explicit exposed,
non-scoring authorization controls the applicable G1 interpretation: one fixed
plan, deterministic evidence and one substantive independent scientific review.

## Intake and availability preflight

Fetched EWP main is `aace2cc6b6c2a393d2dbfb0274104192ca6c7203`, tree
`cb713f8229075fe4f3f1e05d1eca77868e5692ae`. Read-only Puckworks research main is
`d4eb54ce4bd0eb21a0968d3c37f43ad4ef8ccd16`, tree
`455baed303cc95af198c97a043a9e1506f8b81d2`. Both match reviewed reference heads;
there is no intervening main delta. Production lock stays
`fc61c4670ec7bf801e40bb391aab16048b8da26b`. Repository-path and GitHub issue/PR
searches for the task ID, restart and monotone found no equivalent task; #211
and #213 are distinct completed work. Preserve #207/#209/#211/#213 and the
accepted 56-brew / 11-condition cohort; this separate recording is one puck,
`waszkiewicz2025_fig10_restart_puck_01`, not six experiments or a cohort addition.

Read EWP AGENTS/onboarding, project state, claim ceiling, external-data map,
controlling strategy, data-first plan, available-data policy/authority, minimum
governance, and relevant programme/ledger entries. Read the retained #211
PLAN/RESULT/manifest/episodes/intervals/contrasts and relevant JSON/review, observer
and tests. Puckworks data/development guides, Waszkiewicz card and relevant
MANIFEST.csv/AVAILABLE_DATA_REGISTER entries were inspected at the research pin.

FILES_INSPECTED: retained EWP bundle; original restart acquisition and plotting
script in a verified external Git cache. CATALOG_CONTEXT_ONLY: processed
`waszkiewicz2025/traces_per_brew`, `traces_time_dependent`, `equilibrium_windows`,
chemistry/calibration/CT/PSD; Pannusch/Schmieder, G10, Wadsworth/Vaca/Maillé,
Foster and Visualizer families. No new cross-source join is attempted. The
record lacks established same-record chemistry, temperature, independent puck
pressure, valve commands, calibrated response/latency or uninterrupted control.
These are scoped applicability limits, not a claim that the corpus is exhausted.

NEW_INFORMATION: the restriction to a common nondecreasing pressure response
permits an order theorem without approximate pressure equivalence. This differs
from #211's unrestricted-F question and does not reopen its delivery analysis.
DECISION_IF_EXCLUDED: reject the declared joint response/observer hypothesis on
nominal recorded interpolants; a reproducing model must account for the discrepancy
through response shape, evolving state/conditions or a supported observation term.
DECISION_IF_NOT_EXCLUDED: pairwise order supplies no exclusion; no existence proof.
DECISION_IF_UNSUPPORTED: close affected calculations with diagnostics, no rescue.
GRINDER_TO_CUP_LINK: constrain admissible line-pressure-to-beverage observation
models. REPEATED_BLOCKER: this tests a different mathematical restriction using
available data, not another fit against the same missing joins. LOWER_COST_ROUTE:
exact interpolation/order arithmetic; no solver, fit or laboratory recommendation.
No automatic successor, production adoption or Puckworks modification.

## Source and retained observer

Use only RadostW/espresso revision `fbc33d3380a9c8cff2467bae70fec7137a6ed46f`.
Verify current cache HEAD, pinned-tree blobs, lengths and SHA-256 against #211:

| Relative source locator | Bytes | Git blob | SHA-256 |
|---|---:|---|---|
| measurements_brew_restarting/brew_restarting.txt | 163514 | 7940d6aa008e7cae37bb1bf8ceece44fa07d0bff | e82430cde25574140d2026882a883fba21a0f0ac6d9588b15df22571836f68e9 |
| plot_singlepanel_brew_restarting.py | 1783 | f93c4c2abb6847d70b21df669bd6940089c226b3 | aa35ade18cc8b6946164279d6e2e82337435c3165698be932ff3d0f32b47cd74 |

Waszkiewicz et al. (2025), Zenodo 18046315; retain CC-BY-4.0 data attribution.
GPLv3 plotting software is inspected for lineage only, not copied or executed.
Raw payloads and full logs remain external with relative locators and hashes.
A material authentication mismatch closes the affected calculation UNSUPPORTED;
no replacement trace, current upstream substitution or input repair.

Use original zero-based row indices and integer millisecond clock; seconds=t/1000,
line pressure=p2/100 bar, m=recorded cup mass in g. Other fields uninterpreted;
p1 is not independent puck pressure; no flow-derived basket correction.
ACTIVE iff p2/100 > 5.5 bar. Verify retained supports E0 2.464–77.363,
E1 82.974–93.913, E2 99.805–110.559, E3 117.760–128.327,
E4 135.621–146.094, E5 152.452–167.319 s. Threshold boundaries are acquisition
support, not valve-command times or pressure-equivalence criteria.

Exactly PRIMARY (D=2 s,g=2 s), SENSITIVITY_A (3,2), SENSITIVITY_B (2,3).
Every later interval is [episode_end-g-D, episode_end-g], including E0.
Reuse retained eligibility/support decisions; reconcile all 18 later intervals.
qbar=(M_tilde(b)-M_tilde(a))/D with unsmoothed piecewise-linear mass. Pressure
uses the same original-adjacent linear interpolation. Retain endpoint brackets,
indices, raw values, times, weights and exact-sample flags. No extrapolation,
missing/nonfinite support, nonincreasing clock, documented discontinuity, gap
>95 ms or bracket crossing its episode boundary. The 95 ms rule is software
support, not sensor response. No smoothing, clipping, monotonic repair, grid
replacement, lag search, alignment optimization, new windows or time warping.

## Fixed family, theorem and arithmetic

Family A: E1–E5 later versus E0 later, each design (15 rows). Family B:
E1–E5 later versus preceding episode later, each design (15 rows).
B(E1,E0) has explicit duplicate_of=A(E1,E0): 30 reporting rows, 27 unique keys.
No early/later, initial-drift or early/reference comparisons in this task.
C=candidate restart; R=reference; dP=P_R-P_C; delta_q=qbar_C-qbar_R.

Hypothesis: qbar_I=(1/D) integral_0^D F(P_I(s)) ds for every included interval,
with one finite, time-independent, nondecreasing F otherwise unrestricted on
the observed pressure domain. If P_C<=P_R pointwise, then F(P_C)<=F(P_R), and
integration implies qbar_C<=qbar_R. Thus delta_q>0 contradicts the hypothesis.
Symmetrically P_C>=P_R implies delta_q>=0. Identical pressure implies equality.
Flat portions permit equal delivery even under strict pressure order. A finite
monotone F is measurable and bounded on the closed observed pressure range,
so the Lebesgue integrals exist. One contrary pair excludes a common F for the
set. Absence of one proves neither existence nor feasibility.

Use Fraction from exact source decimal tokens; integer-ms endpoints and knot
unions. Signs use exact rationals, without inferred quantization or a tolerance.
Union={0,D, all internal original C and R acquisition knots shifted by their own
start}. Between knots dP is linear; extrema occur at endpoints. Store full union,
pressure supports, segment extrema, global extrema and attaining knot indices/
times (including flat attaining segments). Exact rational strings are authoritative;
decimals are presentation. Report differences from old float outputs separately
from unestablished measurement uncertainty.

Mutually exclusive classes: CANDIDATE_WEAKLY_LOWER iff min>=0,max>0;
CANDIDATE_WEAKLY_HIGHER iff max<=0,min<0; IDENTICAL_PRESSURE iff both zero;
CROSSING iff min<0<max; otherwise UNSUPPORTED or NUMERICALLY_UNRESOLVED with
reason. Strict separation is separate. Contrary signs are respectively delta_q>0,
delta_q<0, delta_q!=0. Supported noncontrary and crossing rows are
NOT_EXCLUDED_BY_PAIRWISE_ORDER_TEST, never feasible/validated/explained.
Retain every declared row and failure, not only exclusions.

## Conditional robustness and completion

For lower pressure mP=min(P_R-P_C), higher pressure mP=min(P_C-P_R).
A uniform adverse differential correction E_P gives corrected ordered margin
>=mP-E_P: E_P<mP preserves strict separation; equality preserves weak order;
E_P>mP can destroy this certificate but does not establish an F. With equal
separate trajectory bounds epsilon_P, E_P<=2*epsilon_P; boundary mP/2.
Zero-margin weak order is nominally valid without positive adversarial reserve.
For contrary delivery, adverse differential rate correction <abs(delta_q)
preserves its sign; equality can remove it. Four separately bounded endpoint
mass errors |e|<=eta imply |error(delta_q)|<=4*eta/D without independence;
eta_critical=D*abs(delta_q)/4 assumes fixed timing and interpolation.
Also aggregate exact original-sample coefficients in delta_q=sum c_j*m_j,
including shared-sample cancellation/reinforcement, before computing sum|c_j|.
Report |error|<=sum|c_j|*eta_j and the uniform-bound threshold; distinguish
attained versus conservative generic 4/D. These are worst-case box boundaries,
not known instrument accuracies or distributions. Common additive mass offset
cancels; positive mass gain preserves sign; common constant pressure offset and
positive pressure gain preserve order. Differential drift/dynamics need not cancel.
No latency/transit/storage/timing/interpolation-model error bound is inferred.
Shared observations mean margins are not independent experiments or a proven
simultaneous correction explaining all rows.

Execute offline; deterministic standard-library producer and focused mathematical/
observation tests. Exposed E1/E0 and E5/E4 values/counts are discrepancy checks,
not success gates: investigate units, source, signs and support without retuning.
One independent scientific reviewer directly recomputes these and one crossing,
checks theorem, error boundaries and scope, and binds review to scientific hashes.
Run applicable current source/static/Python/historical/boundary/shell/JSON and
manifest checks. Active main ruleset 19901931 requires source-and-boundary and
inexpensive-checks (GitHub API inspected; connector has no ruleset read tool).
No OpenFOAM or archival Allrun/Allverify/Allclean execution.

Report nominal recorded/interpolant exclusion, conditional error requirements and
physical applicability separately. This concerns joint response/observation
assumptions, not unobserved physical pressures. Nonmonotone fixed responses and
pressure-driven memory models remain outside scope. No interruption causality,
chemical exhaustion, observed channels, steady state or particular permeability
law follows. Preserve all prior conclusions. Deliver one open draft PR, unmerged,
auto-merge disabled; no successor.
