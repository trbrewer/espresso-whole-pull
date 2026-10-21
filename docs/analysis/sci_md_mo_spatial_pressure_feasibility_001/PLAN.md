# SCI-MD-MO-SPATIAL-PRESSURE-FEASIBILITY-001 plan

G1 bounded mathematical/source feasibility; `NO_GOVERNING_PHYSICS_CHANGE`
means production physics is unchanged. `RESEARCH_ONLY`, retrospective,
target-exposed, non-scoring; `PHYSICAL_VALIDATION=NOT_ESTABLISHED`.
The owner task authorizes this analysis, one independent scientific review,
and one draft EWP PR. No production adoption or successor is authorized.

## Intake and authorities

- **NEW_INFORMATION:** Whether spatial redistribution escapes the scalar ordering
  exclusion while retaining a passive hydraulic network, nonnegative opening
  and fixed-full-state pressure-monotone erosion.
- **DECISION_IF_POSITIVE:** Retain exactly the demonstrated spatial reduction as
  a structurally capable research candidate conditional on its assumptions;
  name missing coffee loading/material/observation joins.
- **DECISION_IF_NEGATIVE:** Retire exactly the family covered by a proof for
  common-condition discharge reversal.
- **DECISION_IF_NULL_OR_BLOCKED:** State the mathematical gap, bounded search,
  numerical limit or missing closure; close without a favorable invented closure.
- **GRINDER_TO_CUP_LINK:** Determine whether this source-informed spatial state
  supplies the hydraulic response direction missing from the scalar model.
- **REPEATED_BLOCKER:** This tests a new mathematical premise before calibration;
  it does not repeat a missing-data fit or claim corpora exhausted.
- **LOWER_COST_ALTERNATIVE:** Source/closure inspection and analytical exclusions
  precede simulation.

Fetched EWP main is `ba28b230d2c3a5da8b7d611b48af59b0ba90df35`.
Read-only PW main is `58075bbbce548e63d94106c96b918c1464221514`.
Both match preparation baselines; no intervening delta. The production lock
continues to name `fc61c4670ec7bf801e40bb391aab16048b8da26b`.

Reuse #207's audited Eq. (11) compression/sign/unit crosswalk and substantive
review. Inspect the Mo accepted manuscript II B, pp. 4–5 (force, effective
law, incomplete-wetting rationale), and II E (approximation/normalization).
[Institutional record](https://cronfa.swan.ac.uk/Record/cronfa57912),
[DOI](https://doi.org/10.1063/5.0059707); PDF SHA-256
`55ee1e3746312f85dcc8888e337775cdea0a99e93fec4a35376cb7663b67b99c`.
The source mass rate and 2D simulation stress are not aperture speed or SI
coffee calibration. Manuscript/figures stay outside Git. This is a reduction
of the effective law, not a reproduction of the spatial stochastic bond model.

## One declared model (before exploration)

Graph and signed orientation: SA, AT, SB, BT, AB, with boundaries S and T and
interior A,B. All edges have length and breadth L (a fixed positive length).
Full aperture is a_e=epsilon L x_e, epsilon=0.01; x_e0 in [0.1,1],
x_e0<=x_e<=2. Thus a/l and a/w are at most 0.02. Distinct nonoverlapping
wall coatings, two per edge, have combined removable thickness
h_e=epsilon L(2-x_e0); each wall supplies h_e/2. Junctions are fixed,
nonerodible, zero-volume/zero-resistance pressure nodes. No shared-wall
inventory is counted twice. Stop at geometry/topology invalidity.

No-slip, wide-slit, Newtonian, creeping flow with viscosity mu>0:

    g_e=w_e a_e^3/(12 mu l_e), q_e=g_e(p_u-p_v),
    tau_e=a_e |p_u-p_v|/(2 l_e).

p_S=p_out+P, p_T=p_out, P constant and positive. Re-solve the two-node
Kirchhoff system for every state; signed AB flow may reverse. Define K=Q/P;
compute Q_in=q_SA+q_SB and Q_out=q_AT+q_BT separately.
The model neglects entrance/junction corrections; it is an ideal slit-network
approximation, not an asymptotically exact model of a coffee pore junction.

**Mechanical closure:** both loaded slit walls are stiff, supported, incompletely
wetted erodible solid. The solid-interior/background pressure is held at the
same p_out in all edges and runs. Rigid supports balance fluid traction with
negligible reversible displacement. Outward solid normal points into the slit;
fluid traction has inward normal component -(p(s)-p_out). Define compression
positive: sigma_c(s)=sigma_0+p(s)-p_out, with sigma_0=0 in this study.
Axial p(s) is the linear hydraulic interpolation between endpoint pressures.
Interior pressures lie in [p_out,p_out+P], so sigma_c>=0. The differential
loading, stiff support and fixed internal pressure are explicit hypothetical
mechanical assumptions, not inferred coffee effective stress or an arbitrary
pressure multiplier. No measured line pressure is inserted as grain load.

Per effective surface site r(s)=C_E[tau-c-sigma_c(s)tan(psi)]_+ (kg/s),
C_E>=0 in kg/(s Pa). Effective initial site density n_s (sites/m^2) is
common to both walls and all edges. Remaining-site weight is
b_e=(2-x_e)/(2-x_e0). Assume area-averaged uniform aperture evolution even
when local retreat is nonuniform; this projection loses axial shape detail.
Integrate the positive part locally *before* averaging:

    I_e=(1/l_e) integral_0^l_e [tau-c-sigma_c(s)tan(psi)]_+ ds,
    Mdot_e=2 n_s C_E w_e l_e b_e I_e,
    M_removed,e=rho_s w_e l_e(a_e-a_e0),
    adot_e=(2 n_s C_E/rho_s) b_e I_e.

The factor two counts two walls; M_removed already uses full-gap opening.
This site-depletion closure is additional to Mo's effective law. rho_s>0,
n_s,C_E,c,psi and every inventory are identical across the compared runs.
No deposition, obstruction, viscosity/chemistry change or beverage solids
contribution is modeled: removed material leaves the hydraulic calculation.

Choose one pressure reference P_ref>0 independent of imposed pressure,
S_ref=epsilon P_ref/2, kappa=2 n_s C_E/rho_s,
t_ref=epsilon L/(kappa S_ref). For kappa=0 use the exact frozen solution.
Let pi=P/P_ref, theta=t/t_ref, gamma=c/S_ref,
beta=2 tan(psi)/epsilon; common clock and dimensional materials are preserved.
Hydraulic units: g_ref=epsilon^3 L^3/(12 mu), Q_ref=g_ref P_ref.
In these units g=x^3, p_S=pi, p_T=0 and

    J_e=integral_0^1 [x_e |p_u-p_v|-gamma-beta p_e(s)]_+ ds,
    dx_e/dtheta=b_e J_e.

Compute J analytically as the area under the positive part of a linear
function. This is not thresholding the mean pressure; no quadrature mesh.
Use z_e=-log(b_e), x_e=2-(2-x_e0)exp(-z_e),
dz_e/dtheta=J_e/(2-x_e0), z_e(0)=0. This unique nonnegative system preserves
inventory without post-step clipping; finite-time exhaustion is impossible
for bounded rates. Floating roundoff at the limiting upper endpoint is
recorded, not a reset. Nonfinite, decreasing or out-of-domain states fail.

The hydraulic approximation is the controlled slow-erosion limit kappa->0
at fixed theta, while fluid inertia is independently negligible. The omitted
pore-storage ratio is

    (dV_pore/dt)/Q = [epsilon L^3/(t_ref Q_ref)] sum_e(dx_e/dtheta)/Q*.

On this compact positive-conductance/pi domain Q* has a positive lower bound;
choose the common kinetic scale so this ratio tends uniformly to zero.
No finite coffee timescale or measured storage accuracy is claimed. Likewise
choose common physical scales with rho_f U a/mu <<1. Equal theta means equal
physical time with the same t_ref; source flux-dependent c* or T* are not used.

## Analytical controls before finite-cohesion exploration

Derive slit velocity/shear/units, maximum principle, dissipation and Rayleigh
conductance monotonicity. Opening makes each individual constant-P Q
nondecreasing; this does not order different-P trajectories.
At complete fixed x, each local bracket has form [pi s(x,s)-gamma]_+.
For gamma>=0 it is zero if s<=0 and nondecreasing in pi otherwise; positive
integration and b_e preserve componentwise pressure monotonicity.
Recover #207's unique scalar comparison and the symmetric bridge control.
For D=c+sigma_0 tan(psi)=0 everywhere, show dx/dt=P G(x) and
x_P(t)=X(Pt); monotone K excludes reversal. Finite-cohesion collinearity and
cooperativity must be examined, not presumed. Check active erosion and the
C_E=0 and gamma>=2 pi_H globally inactive controls.

Preliminary obstruction to a simple cooperative proof: at beta=0 and active
AT erosion, increasing g_BT decreases p_A when g_AB>0, hence decreases
AT's rate at fixed own aperture. Finite thresholds can make the pressure
vectors noncollinear. Neither fact proves reversal. If a stronger exclusion
is obtained, stop without a search.

## Bounded numerical protocol, only if analysis is insufficient

One topology and the closure above. 128 candidates from scrambled Sobol
(dimension 8, seed 20261021, random_base2(7), fixed SciPy 1.11.4).
Coordinates in order: five x0 log-uniform on [0.1,1], gamma log-uniform
on [0.01,0.5], beta uniform on [0,4], pi_H uniform on [1.05,3]; pi_L=1.
Thus friction is weak (tan(psi)<=0.02), explicitly a hypothetical material
range selected to admit erosion in slender slits, not source-measured coffee.
All other dimensions/properties are fixed above; only initial geometry and
common material parameters differ *between candidates*, never within a pair.
This eight-dimensional bounded screen is not a complete covering argument.

Common horizon theta in [0,32], unrelated to an empirical endpoint.
DOP853, rtol=1e-8, atol=1e-10, max_step=0.25; 1025 uniform output times.
Budget: 256 exploratory trajectories, <=100000 RHS evaluations per
trajectory and <=5000000 overall; numerical failures consume budget and are
retained. No optimizer, range expansion, topology or closure switch.
Retain each candidate's exact parameters, status, evaluation count, minimum
Q_H/Q_L and time; also conservation/domain/individual-monotonicity checks.

A preliminary witness needs Q_H/Q_L<1-1e-5 at three consecutive output times.
Freeze the first such candidate before refinement. At most four preliminary
candidates may receive verification (eight integrations each at most), with
failures retained. If none qualifies, refine the closest candidate once.
Independent verification uses tighter DOP853 and Radau, independent hydraulic
linear solve and threshold integration, common times and numerical-gap
estimates; isolate crossings and retain full paired trajectories and a plot
only for a qualified witness. Inter-resolution differences are estimates,
not global error enclosures. Witness status is NUMERICALLY_RESOLVED_REVERSAL
unless a genuine proof/enclosure is separately obtained within this scope.

Stop on a sufficient exclusion, one qualified witness, an essential missing
closure, budget exhaustion or four failed preliminary verifications. A
bounded search without a witness is UNRESOLVED, never INFEASIBLE. For a null,
retain the closest pair's reproducible parameters and refinement limits;
unsampled times/states remain unresolved.

## Scoped available-data note and limits

FILES_INSPECTED: EWP instructions/onboarding/state/claim ceiling, minimum
governance, controlling and data-first strategies, available-data authority,
existing-data programme/ledger and external-data use map; #207 plan/result/
JSON/review; #209 and #211 results; SCI-MD-011 observation interface; relevant
SCI-LC-001A formulation and terminal result. Read-only PW development guide,
R-04/T08, Mo card, streamtube implementation and Waszkiewicz/Mo structural
entries in the data guide and capability register. Primary manuscript
passages identified above. Reuse accepted observations without reopening
raw acquisitions, performing new reduction or constructing a corpus census.

CATALOG_ONLY here: Waszkiewicz raw traces, PSD/calibration holdings;
Mo2023 microCT/SPH structure, Hargarten swelling/wetting, Foster fronts,
Wadsworth PSD and Vaca dry porosity. Their availability is not a common
coffee loading/material/observation join. No claim of missing/exhausted
corpora or laboratory recommendation follows.

#207's scalar exclusion, #209's terminal beverage-delivery signs and #211's
within-puck observation stay at accepted strength. #211 has unresolved pressure
equivalence, observation response and causal attribution; no steady-flow,
permanent-opening, channeling or chemistry inference and no restart simulation.
SCI-LC-001A's signed relative-flow resistance law is different; its ineligible
terminal result is not an exclusion of this family. PW streamtube adds clogging,
which this opening-only study excludes. Prescribed bed pressure is primary;
line-pressure applicability NOT_ASSESSED. Coffee-specific loading, yield,
kinetics, initial geometry and hydraulic-to-beverage observation remain open.

One substantive independent scientific review will cover the source/reduction,
loading/sign/reference, fixed-state monotonicity, analytical controls, common
state/material/time, assurance, conservation and development consequence.
Run focused and normal applicable checks and hosted CI. Keep the single PR
open/draft/unmerged, auto-merge disabled; final identities and CI in its body.
