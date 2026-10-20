# SCI-MD-MO-PRESSURE-FEASIBILITY-001 result

**The declared scalar effective-law reduction cannot produce a declining
high-pressure discharge branch. Retire that reduction for this purpose; it
does not warrant calibration or governing-law implementation to recover that
sign. Transfer of this exclusion to the accepted processed `endpoint_100s`
observable remains unresolved.** The full Mo2021 spatial/stochastic model is
also unresolved, not rejected. `PHYSICAL_VALIDATION=NOT_ESTABLISHED`.

This is one completed R-04/T08 source-and-mathematics analysis, G1 /
`NO_GOVERNING_PHYSICS_CHANGE`, retrospective, target-exposed and non-scoring.
The exact authorities/intake are in [PLAN.md](PLAN.md); machine-readable
scope, identities and file hashes are in [RESULT.json](RESULT.json).
No fit, empirical score, numerical evolution, native solver run or predecessor
campaign was performed. The production Puckworks lock is unchanged.

| Scope | Structural capability for the requested declining branch | `endpoint_100s` applicability |
|---|---|---|
| Fixed-geometry effective erosion law, affine tractions, nonnegative offset | INFEASIBLE for a decreasing **local erosion rate**; this alone is not a flow theorem | UNRESOLVED; no local-rate-to-endpoint map |
| Declared scalar opening/conductance model, common initial state, ordered histories, admissible adapter throughout | INFEASIBLE for decreasing instantaneous endpoint discharge | UNRESOLVED for the actual processed target; conditional hydraulic theorem below |
| Full source spatial geometry/stochastic bonds, including departure from Eq. (11) | UNRESOLVED | UNRESOLVED |

## Source authority, signs and dimensional crosswalk

Mo, Johnston, Navarini and Ellero, *Modeling the effect of flow-induced
mechanical erosion during coffee filtration*, *Physics of Fluids* **33**,
093101 (2021), [DOI](https://doi.org/10.1063/5.0059707).
The [institutional record](https://cronfa.swan.ac.uk/Record/cronfa57912)
labels the [inspected manuscript](https://cronfa.swan.ac.uk/Record/cronfa57912/Download/57912__20869__84fcf87a8f8542e8a1a9e9fd996e9fc5.pdf)
as accepted; its first page is dated **4 August 2021**. The downloaded
26,047,376-byte PDF has SHA-256
`55ee1e3746312f85dcc8888e337775cdea0a99e93fec4a35376cb7663b67b99c`,
matching the preparation authority. Equations/passages were inspected from
that PDF, including visual inspection of Figs. 1–3 and 7. No material version
difference arose; the typeset version was not used as an interchangeable
authority. The institutional rights statement is CC-BY-NC-ND 2.0; the PDF and
figures remain outside Git. This report supplies analysis and attribution.

**Sign reconciliation.** In Fig. 1 the surface normal points outward; the
signed `F_n` in Figs. 2–3 is negative for inward compression. The source says
inward normal force impedes breakage. In Fig. 7, the positive horizontal
normal-stress coordinate increases the positive shear threshold. To preserve
that meaning in Eq. (11), use a separately named compression-positive load
`sigma_c=-F_n/a_s>=0`, where `a_s` is the local surface measure, and a shear
magnitude `tau=|F_t|/a_s`. This is a **DERIVED sign reconciliation** on the
compressive branch, not an assertion that Fig. 2's signed force and Fig. 7's
stress are the same signed variable. The research card's parenthetical
“compression negative” belongs to the force plots; inserting that signed
quantity directly into `+sigma tan(psi)` would reverse the physical effect.
The card is not modified or treated as primary evidence.

The following crosswalk distinguishes source equations from the reduction.
Let `M`, `ell`, `T` denote dimensions, `d` spatial dimension, `S_d=force /
ell^(d-1)` the local stress dimension. The source uses 2D simulation units:
force has dimension `M ell/T^2`, `S_2=M/T^2`; it is not directly a measured
3D stress in Pa. A 3D physical reduction needs a surface-area/thickness
interpretation rather than numerical substitution of source constants.

| Premise / source location | Variables, units and sign | Domain and status |
|---|---|---|
| `d_vec=(sum lhat_i lhat_i)^(-1) F/k`; `Delta l_i=lhat_i dot d_vec`, II B Eqs. (5)–(6), p. 4; geometry Eq. (10) | Displacement/stretch `ell`; `F` signed vector force; spring stiffness `k=force/ell`; unit directions run interior to surface. Eq. (10) gives `(1/sqrt(2),-1/sqrt(2)),(1,0),(1/sqrt(2),1/sqrt(2))`. | SOURCE_STATED: stiff springs, small displacement, supported surface particle, invertible support tensor. Not a bulk skeleton stress law. |
| `p_i=min(p_0(Delta l_i-Delta l_c),1)`; `T_i=N_freq Delta t/p_i`; `k_er=m/sum_{i in S_b} T_i`, II B Eqs. (7)–(9), p. 4 | Probability dimensionless; `p_0=ell^-1`; threshold `ell`; interval/lifetime `T`; particle mass `M`; rate `M/T>=0`. Ineligible bonds have no positive breaking rate. | SOURCE_STATED: only most-stretched eligible bond, stretch above threshold; support changes after each break. The analytical sequence may exclude the last spring once it cannot constrain motion. This stochastic/sequence model is not replaced by an exact linear identity. |
| `k_er=C_E[tau-(c+sigma_c tan(psi))]_+`, II B Eq. (11), p. 5 | `tau,c,sigma_c` stress `S_d`, `psi` angle; `C_E` has units `M/(T S_d)` and is nonnegative. `k_er` is particle mass/time, not porosity/time. | SOURCE_STATED effective form; DERIVED compression-positive convention as above; examined domain `0<=psi<pi/2`, compressive loading, `c>=0`. It is not exact for all spring states. |
| `C'_E=m p_0 (Delta x)^(d-1)/(k N_freq Delta t)`, II B Eq. (12), p. 5 | Particle spacing `ell`; with the preceding units this is `M/(T S_d)`. | SOURCE_STATED estimate of scale, not a closed expression for `C_E`; does not calibrate coffee kinetics. |
| `P_i=P_0(d_i/d_0)^nu-P_b`, II A p. 3; Table I p. 7 | `d_i,d_0` number density `ell^-d`, `nu` dimensionless; `P_i,P_0,P_b` simulation stress. `P_0-P_b=6400` in Table I. | SOURCE_STATED SDPD equation of state/background pressure. Neither a measured coffee preload nor a Darcy-drop-to-grain-load closure. |
| `F^C_ij=alpha(P_i/d_i^2+P_j/d_j^2) F_ij r_ij`, `alpha=tan(psi)`, II E Eqs. (16)–(17), p. 8 | `alpha>0` dimensionless; pair distance `ell`; kernel factor `F_ij=ell^(-d-2)` gives force. `S` is supported surface particles (at least `d` interior links). | SOURCE_STATED scaling of conservative force on those particles, not of the imposed machine pressure. The `alpha=0` shear-only limiting case is discussed in III C. No fluid-side closure from `L` to traction follows. |
| `tau_ref=6 q_s eta/(epsilon_0 E_0(lambda))`; `t_er=m/(tau_ref C'_E)`; `c*=c/tau_ref`, `T*=T/t_er`, II E p. 7 | `q_s` is source superficial **velocity** `ell/T`, viscosity `S_d T`, pore width `ell`, porosity dimensionless, `tau_ref` stress, `t_er` time. | SOURCE_STATED normalizations: `q_s=0.08`, `epsilon_0=0.564`, `E_0=0.456D_0`, `tau_ref≈23.3`, `t_er≈17.17` in simulation units. These are not seconds/bar/g/s calibration. |
| `tau=A(g)P`, `sigma_c=sigma_0(g)+B(g)P`; `s_E=A-B tan(psi)`, `D=c+sigma_0 tan(psi)` | Hereafter `P` is **bed pressure drop in bar**, `A,B` Pa/bar, `sigma_0,c,D` Pa, `C_E` kg/(s Pa), `r_E` kg/s. | ADDITIONAL 3D quasi-steady affine traction closure; DERIVED `r_E=C_E[s_E P-D]_+`. Common datum, viscosity, boundaries, geometry and coefficients fixed while varying pressure; no identification with bulk effective stress. |
| `M_E=rho_s V_* x`, `F=N(x)r_E/(rho_s V_*)` | `x` dimensionless fraction of a fixed erodible solid volume `V_*` (m³) removed; solid density `rho_s>0` kg/m³; `N` dimensionless number/effective weight of equivalent surface sites. `F` is s^-1. | ADDITIONAL scalar geometry closure `g=g(x)` and nonnegative mass-to-opening conversion. If viewed as porosity of fixed bed volume `V_b`, `epsilon=epsilon_0+(V_*/V_b)x`, so `d epsilon/dt=Mdot_E/(rho_s V_b)`. A normal retreat rate instead requires `Mdot_E/(rho_s a_s)` (m/s). Area/volume factors cannot be dropped. |
| `q=K(x)P`; `K=1000 rho_f A_b k_perm(x) 10^5/(mu H_b)` for fixed Darcy area/height | `q` g/s, `K` g/(s bar), `rho_f` kg/m³, basket area `A_b` m², permeability `k_perm` m², viscosity `mu` Pa s, height `H_b` m. Factors convert kg to g and bar to Pa. | ADDITIONAL hydraulic closure. For changing height/area it is the full conductance `K`, not permeability alone, that must be nonnegative/nondecreasing. Common positive density/area converts superficial velocity to mass flow. |
| `P=L-h(q)` with `h(q)=a q²+b q+h_0`, SCI-MD-011 `OBSERVATION_INTERFACE.json` | `L,P,h` bar; `q` predicted mass flow g/s; `a=0.017184292098914252` bar s²/g², `b=0.03670858658698296` bar s/g, `h_0=0.2831597837775055` bar. | Retained observation authority; ADDITIONAL use instantaneously throughout the transient. Positive-flow branch, `L>=h_0`; predictive input never observed basket pressure. |

These are all load-bearing equations. Subsequent inequalities, sensitivities
and comparison bounds are DERIVED from the declared premises, not further
source claims. Source `q_s` must not be confused with this report's `q`.
Likewise source local `P_i`, source normalization `P*`, bed drop `P`, and
measured line pressure `L` are distinct quantities.

**What the source actually investigates.** II D (p. 6) uses 225 random disks,
periodic boundaries and a reset inlet velocity: **prescribed flux**, with
`Re=0.04`. It explicitly does not run fixed-pressure filtration there. Its
comment about fixed-pressure erosion referring to previous work is not a
proof for all its own spring/geometry states. Shrinking grains, increasing
pore widths and downstream/upstream differences describe changes in time
and position at fixed flux (III A–C), not a cross-imposed-pressure endpoint
curve. Released particles join the fluid representation; deposition is
excluded (II B rule v). No source outlet-solids accounting is supplied for a
beverage scale.

**Effective law versus full model.** Fig. 7, II E pp. 7–8, has a threshold
slope approaching one at sufficiently large compression, but a smaller slope
at small compression for larger stretch thresholds. The surrounding prose
occasionally writes `Delta x` where the plotted varying parameter is
`Delta l_c/Delta x`; use the legend/caption and equations to disambiguate.
The authors explicitly describe Eq. (11) as an approximation. The source's
nonaffine failure envelope and probability cap/bond sequence escape the exact
effective-law premise. They are an identified boundary of this theorem,
not an established turnover witness. No justified grain-traction map,
common physical clock and pressure-controlled endpoint solution were supplied
that would turn this escape into FEASIBLE.

## Fixed-geometry sign lemma

For fixed `g`, write

`r_E(g,P)=C_E(g)[s_E(g)P-D(g)]_+`, `P>=0`, `C_E>=0`, `D>=0`.

If `s_E<=0`, then `s_E P-D<=0` everywhere in the domain and erosion is
identically inactive. If `s_E>0`, the onset is `P_on=D/s_E`; below it the
rate is zero and above it the slope is `C_E s_E>=0`. Equality at onset is
handled by the positive part, not a nonexistent derivative. `C_E=0` is also
inactive. Thus finite positive cohesion or background compression delays
onset but cannot cause an active decreasing segment in this affine model.

The affine approximation needs more than the yield law: at fixed saturated
geometry, linear Stokes/Darcy response with fixed viscosity and common
boundary geometry gives velocity and viscous shear proportional to imposed
bed drop; local fluid pressure can be a fixed offset plus a spatial
coefficient times that drop. Converting this field into surface traction
requires common exposed surface measure, pressure reference and grain
interior loading. Here `A>=0`, `B>=0`, `sigma_0>=0`, finite common `c>=0`
and `0<=psi<pi/2` supply a compression-positive example of `D>=0`; the
algebraic lemma itself only needs `C_E,D,P>=0` and real `s_E`.

It is **not** generally legitimate to set the local pressure equal to the
bed drop, line pressure, or bulk skeleton effective stress. Incompressible
hydraulics alone fixes gradients, not the absolute/interior-pressure
imbalance needed for this source premise. The explicit `sigma_0` holds that
unresolved offset; it is not set from SDPD's 6400 or a measured tamp force.
Coefficients, reference pressure, material constants and initial geometry
are not allowed to change with the varied pressure. Changing any of these
can leave the lemma's domain. This lemma by itself says nothing about
endpoint discharge through an evolving geometry.

## Scalar opening theorem at prescribed bed pressure

The precise examined representative-site reduction is

`dx/dt=F(x,P)=N(x) C_E(x)[s_E(x)P-D(x)]_+/(rho_s V_*)`,
`q=K(x)P`, `x(0)=x_0 in [0,1]`.

All geometric/material functions are common across conditions. `N,C_E,A,B,
sigma_0` are bounded, nonnegative and Lipschitz on `[0,1]`, `N(1)=0`,
`rho_s,V_*>0`, and `c,psi` are fixed finite values in the domain above.
`K` is bounded C¹, `K>=0`, `K'>=0`. The initial state is common, not reset
separately by pressure. This is an explicitly **ADDITIONAL** lumping of
geometry and exposed mass, not a derivation that a spatial bed has one state.
It is the smallest declared opening-only Darcy reduction of the effective
source law; no clogging, compaction, new wetting schedule or varying material
constant is inserted.

The positive-part function is Lipschitz. For bounded piecewise-continuous
nonnegative pressure histories, `F` is uniformly Lipschitz in `x` on this
interval and bounded; standard integral-equation existence/uniqueness applies.
`F>=0` and `F(1,P)=0` make `[0,1]` invariant, and boundedness gives existence
for every finite common physical time. The state is cumulative opening;
mass accounting is `Mdot_E=rho_s V_* F=N r_E` and cannot exceed
`rho_s V_*(1-x_0)` after initialization. This is an assumed removal-to-void
balance, not a measured bed-conservation result.

The fixed-state lemma makes `F` nondecreasing in `P`, even if `s_E(x)` changes
sign along the trajectory. More generally the proof holds for a common
`F(x,P,t)` with the same Lipschitz/invariance and pressure-monotonicity
conditions; no explicit time-dependent law is introduced here.

Let `P_2(t)>=P_1(t)>=0` on a common interval `[0,T]` and let both solutions
start at the same `x_0` (or at ordered states). On the set `x_1>x_2`, the
positive part `w=(x_1-x_2)_+` satisfies, almost everywhere,

`w' <= F(x_1,P_2,t)-F(x_2,P_2,t) <= Lambda w`,

where `Lambda` is a Lipschitz bound in state. Since `w(0)=0`, the integral
Gronwall bound gives `w(t)=0`. At contact the pressure order makes the
upper derivative nonpositive; erosion thresholds cause no problem.
**No condition `F_x>=0` is needed.** It follows that `x_2>=x_1` and

`q_2(T)=K(x_2(T))P_2(T)>=K(x_1(T))P_1(T)=q_1(T)`.

For discontinuous prescribed histories, use their specified endpoint values
or one-sided limits; the endpoint pressures must be ordered too. Constants,
proportional nonnegative histories, and general pointwise ordered histories
are covered. An ordering of endpoints alone is not sufficient. The theorem
holds at **every finite common physical time**, with finite `D>=0`, without
calibrating a 100-second erosion rate. Rising low-pressure flow is permitted;
a declining high-pressure discharge branch is excluded. For positive
conductance and strictly higher constant pressure the endpoint flow is
strictly higher; zero conductance permits equality.

## Include the machine adapter in the evolution

Let `h(q)=a q²+b q+h_0` with the retained coefficients above. For fixed `x`,
solve `L=P+h(K(x)P)` on `P>=0`. Its derivative in `P` is
`1+h'(q)K(x)>=1` because `h'(q)=2a q+b>0` for `q>=0`.
The map starts at `h_0` and increases without bound. Therefore **exactly one
nonnegative branch exists for `L>=h_0`**. At `K=0`, `q=0` and `P=L-h_0`.
For `K>0` the numerically stable explicit positive root is

`q=2K(L-h_0)/(1+bK+sqrt((1+bK)^2+4aK^2(L-h_0)))`.

Implicit differentiation on the admissible differentiable branch gives

`P_L|x = 1/(1+h'(q)K)`,
`q_L|x = K/(1+h'(q)K)`,
`q_x|L = K'(x)P/(1+h'(q)K)`.

All are nonnegative (the first is strictly positive). Define
`H(x,L,t)=F(x,P(x,L),t)`. The first identity and fixed-state erosion lemma
make `H` nondecreasing in `L` for each `x,t`. The same scalar comparison proof
therefore orders states for **pointwise ordered line-pressure histories**
`L_2(t)>=L_1(t)>=h_0`, including finite offsets/cohesion. Then the last two
identities order endpoint flows in both arguments. One must **not** claim
that the evolving bed drops themselves are ordered: the higher-conductance
trajectory can have a larger machine loss. Comparing at fixed state is what
establishes the theorem.

The polynomial's positive intercept is not a startup model. For `L<h_0`
there is no solution with both `q>=0` and `P>=0`; neither negative flow nor
clipping nor branch switching is admitted. Use throughout a transient is an
explicit quasi-steady applicability assumption, even where the mathematical
root exists. It excludes unrepresented compliance, storage and delays.
The formula has no mathematical upper limit on nonnegative flow, but this
does not extend the calibration's physical validity to every such flow.

For comparison, a **genuinely static**, single-valued differentiable
characteristic `q=G(P)` obeys
`dq/dL=G'(P)/(1+h'(q)G'(P))` where `L=P+h(G(P))` and the denominator is
nonzero on the chosen admissible branch. For nondecreasing `G`, that
denominator is positive. This is a static composition identity, **not** a
derivative formula for a trajectory whose endpoint state depends on the
entire history. A singular denominator or unsupported branch switch is not
a turnover witness.

No pressure/time scaling is needed. Such a separate exact argument would
require homogeneity of the **entire** evolution, including `D=0` (not merely
`c=0`), no other clock breaking it, and appropriate forcing. Nonlinear `h`
precludes silently replacing bed pressure by line pressure in that scaling.
For vector/spatial geometry, monotonicity in pressure at fixed state alone
does not order trajectories; cooperativity, ordered domains or another
justified comparison structure would be necessary. None is proved here,
including for finite-cohesion spatial evolution or stochastic bonds.

## Applicability to the retained observation

The unchanged [SCI-MD-010 metric contract](../sci_md_010/METRIC_CONTRACT.json),
[diagnostics](../sci_md_010/PRESSURE_RESPONSE_DIAGNOSTICS.json),
[SCI-MD-011 interface](../sci_md_011/OBSERVATION_INTERFACE.json), and
[channel semantics](../xsv_waszkiewicz_dynamic_hyd_001/CHANNEL_SEMANTICS.json)
retain 56 canonical physical brews and 11 conditions. Input is measured
`pressure__bar` at index 999; target is `mass_flow_rate__g_per_s` at
`endpoint_100s`. Condition IDs are grouping labels, never pressure values.
The separate 60-brew/110–120-second calibration remains context only.

Measured condition-mean line-pressure subsets are low `<=5.25` bar (five
conditions) and high `>=8.5` bar (three). Retained diagnostic slopes are
**+0.5042068394004887** and **−0.06550641262782862 g/s/bar** respectively.
They are read from committed results, not recomputed scores. The historical
high-pressure gate was `NONPOSITIVE_OR_SATURATING slope <= 0`; it is unchanged.
This task asks about an actual declining branch because that is the retained
trend. No exact peak, slope magnitude or pointwise-fit requirement is added.

**a. Histories.** The theorem covers constants, proportional nonnegative
histories and all pointwise ordered histories on its admitted interval.
[CHECKS.json](CHECKS.json) uses canonical membership and only the line-pressure
column of the existing per-brew histories, whose bytes match the historical
SCI-MD-010 input hash. All 74 cross-condition pairs among the three high
groups are ordered at all 1,000 aligned samples. Minimum upper-minus-lower
gaps are 1.39266 bar (9-group to 11-group), 1.62961 bar (11 to 13), and
3.30191 bar (9 to 13); grouping was selected/sorted using the retained
measured condition means, not parsed labels. A piecewise-linear continuation
of these common-grid histories preserves the order between samples. This
supports the **recorded aligned-grid high-pressure history premise**, not
unobserved sub-sample fluctuations or pre-alignment histories. All canonical
recorded line pressures lie in [0.86675,13.09755] bar, above `h_0`, so none
fails the adapter's algebraic line-pressure domain. No target-derived basket
pressure was used. This is an applicability audit, not a model/data score.

**b. Time and initial state.** Model `t` is seconds from one common physical
initial state, not dimensionless source time. The processed data align each
shot to the sample after the last out-of-tolerance line pressure in its
initial 500 acquisitions, then retain/interpolate 0–100 s. Equal aligned
time does not establish equal time since first water contact, common eroded
geometry at alignment, or the forcing before alignment. We do not reset
state at that point. These missing joins prevent an unconditional theorem
about actual brews even though the retained high histories are ordered.

For a common initial-state distribution one can couple two conditions using
the **same initial draw** and common material draw, with ordered forcing
almost surely. The deterministic theorem then gives pathwise order, hence
ordered expectations/distributions for instantaneous discharge. Merely
declaring a common marginal initial distribution while allowing different
state/forcing dependence does not supply that coupling. Finite noisy sample
means or one realization are not structural counterexamples.

II E's `tau_ref` is proportional to the chosen source flux, and `t_er` is
inversely proportional to it. Holding `c*` or `T*` fixed while changing that
normalization would silently change physical cohesion or elapsed time.
This analysis uses one fixed physical stress/time reference across conditions;
no source `T*` is labelled 100 seconds. The all-time exclusion does not need
a calibrated clock, but positive endpoint applicability would.

The source motivates brittle erosion using incompletely wetted grains and
entrapped gas (Introduction pp. 1–2; II B p. 5), with wetting/softening
relevance early in extraction. It does not establish an unchanged brittle
law over a 100-second shot or a universal five-second shutoff. Opening made
early could persist to 100 seconds in this irreversible removal model even
if later erosion ceased; later wetting/swelling might change that mapping.
Neither persistence in real coffee nor a timed cutoff is assumed measured.
No wetting schedule is tuned or added.

**c. Discharge to beverage mass.** A common positive conversion
`q_h=1000 rho_f A_b u_s` transfers hydraulic order to carrier-liquid mass
flow. Our `K` includes that conversion. It becomes beverage mass flow only
under an additional common proportional outlet relation, with no separately
varying solids mass, density, liquid retention or transport delay. The
source makes detached particles fluid-like computationally; that is not a
measurement of suspended or dissolved material at the cup. An independently
varying solids contribution cannot be dropped or added to the theorem
without justification. The available outlet-composition mapping is
insufficient; no multiphase outlet model is developed.

**d. Processed endpoint.** Source provenance specifies aligned/truncated
scale mass, `gradient(mass,t)` then Savitzky–Golay window 31/order 1, and
interpolation to the common grid. These observations are not instantaneous
model discharge. Integrating ordered discharge from a common mass origin
orders cumulative mass, and a common nonnegative weighted average of ordered
instantaneous discharge would preserve order. Differentiating arbitrary
ordered mass traces does not in general preserve it; the complete retained
sampling/gradient/filter/interpolation operator must be examined on its
actual support before claiming such transfer.

In particular, even the usual degree-one least-squares **edge** evaluation
of a 31-sample filter has weights
`w_j=1/31+15(j-15)/2480`, `j=0,...,30` at the last point. They sum to one
and reproduce a linear signal, but the first weight is `-29/496` and ten
are negative. This DERIVED conditional example shows why a smoothing name
alone cannot prove order preservation on arbitrary gradient samples. It is
not a reconstruction of this dataset's uninspected raw sample/edge operator,
nor evidence that processing caused the observed decline. Actual source
timestamps, endpoint boundary treatment and the model-to-scale relation are
not resolved by the packaged histories/provenance. **Target applicability
is therefore UNRESOLVED**, with no new smoother, observer tuning or rescore.

## Existing holdings and missing joins

The pinned [Puckworks guide](https://github.com/trbrewer/puckworks/blob/58075bbbce548e63d94106c96b918c1464221514/docs/data/ESPRESSO_DATA_GUIDE.md),
`AVAILABLE_DATA_REGISTER.json`, relevant MANIFEST rows, EWP
[use map](../../EXTERNAL_ESPRESSO_DATA.md),
[ledger](../data_leverage/DATA_LEVERAGE_LEDGER.csv) and historical results
were used; no broad corpus census was run. The current register sometimes
has empty capability/missing-join fields or `UNKNOWN` consumed status. These
are metadata limits, not evidence that the corresponding science is absent;
the explicit completed-task results supply the prior-use limits below.

| Access category | Relevant holdings actually checked / catalogued | Useful constraint and remaining join |
|---|---|---|
| FILES_INSPECTED | Primary Mo2021 manuscript; `docs/cards/mo2021.md`; streamtube equations; R-04/T08; EWP historical results/contracts | Supplies source premise and nonduplication, not coffee yield properties or a pressure-controlled spatial result. |
| FILES_INSPECTED | `waszkiewicz2025/traces_per_brew`, provenance; SCI-MD-010 canonical membership and diagnostics; SCI-MD-011 adapter | Pressure histories and processed scale-mass/flow columns exist; only line pressure was newly reduced. No per-shot initial geometry, pre-alignment history, grain load or full raw observer reconstruction. Source-internal, exposed, previously used; not independent validation. |
| FILES_INSPECTED | `waszkiewicz2025/brewer_quadratic_params.csv`, `constants.csv` | Exact retained loss coefficients; source radius 0.028 m, height 0.01 m, dose 18.5 g and water viscosity 3.15e-4 Pa s are source context. They do not measure local traction, wet conductance evolution or erosion kinetics. No new parameterization from them. |
| CATALOG_ONLY | `waszkiewicz2025/brewer_quadratic` point series, `mastersizer_psd`, scale/flow/timing provenance and original source acquisition locator | Per-rig loss and PSD information may constrain geometry/observer work. PSD does not determine the local grain-stress field, surface conversion or initial state. |
| CATALOG_ONLY | `mo2023/forchheimer`, `mo2023/fig8a`; Hargarten swelling anchors; Foster front/headspace digitizations | Measured microCT geometry with simulated permeability, wetting/swelling/front evidence from different sources. Potential constraints, no same-shot stress/erosion/discharge join; Mo inertial units remain caveated. |
| CATALOG_ONLY | Wadsworth PSD/permeability and Vaca dry-porosity data, `mo2023_2` swelling/extraction families | Separate-source priors/operators only; no row-level fusion into one common material campaign. Mo2023_2 chemistry transfer's source-contract/numerical limits remain unchanged. |
| KNOWN_BUT_UNAVAILABLE_IN_THIS_ENVIRONMENT, scoped to registered locations | Original Waszkiewicz acquisition traces and GPL analysis scripts documented in Zenodo provenance; absent from the inspected registered family directory and research checkout | That directory is accessible and holds processed subsets, not original timestamps/operator code. No claim about every file elsewhere or evidence nonexistence. No acquisition undertaken. |

The exact missing joins are: (1) bed/line pressure to local shear and
compression with a supported interior/background pressure reference;
(2) coffee `c,psi,C_E`, erodible mass/surface density and physical erosion
clock; (3) geometry-to-conductance evolution and whether it can be scalar
and monotone; (4) initial material/geometry state and forcing history at a
common physical origin; (5) discharge, transported solids and scale processing
over endpoint support. Existing wet-bed/structure evidence could constrain
some assumptions without sharing the target coffee or apparatus. No missing
join is declared globally unmeasurable or the corpus exhausted.

## Nonduplication, checks and decision

[SCI-MD-012](../sci_md_012/RESULT.md) already rules out turnover by Qc/Pc
rescaling of its monotone families; that result is reused. [SCI-MD-002C](../sci_md_002c/RESULT.md)
held active-bed permeability fixed: zero of 96 synthetic release/transport/
deposition stems passed pressure ordering, including its four potentially
feasible inventory stems. It did not reject all fines mechanisms.
Puckworks Rung B already evolves eroded fraction with relative local flow
and uses `kappa=k0(1+a_open E)/(1+a_clog E)^2`; opening alone is not novelty.
[SCI-LC-001A](../sci_lc_001a/RESULT.md) studied signed relative-flow/resistance
feedback, with terminal `NOT_ADJUDICATED_FINAL_ATTEMPT_INELIGIBLE`, not physical
mechanism rejection. The [dynamic-hydraulics result](../xsv_waszkiewicz_dynamic_hyd_001/RESULT.md)
did not establish stable advantage for its tested bounded forms and does not
prove constant resistance universally. [SCI-MD-MO-TRANSFER-001](../sci_md_mo_transfer_001/RESULT.md)
concerns `mo2023_2` extraction chemistry. None answers this local
shear/normal-loading sign question under changing driving pressure.

The result is analytical, not a numerical sweep. [check.py](check.py) and
[CHECKS.json](CHECKS.json) independently check explicit adapter roots against
`q=KP`, its intercept/zero-conductance limits, finite-difference versus
implicit sensitivities, the aligned high-pressure history premise, and the
conditional filter-weight illustration. The arbitrary `K=0,1` algebra cases
are not coffee parameters or capability witnesses. Maximum recorded adapter
residual is `1e-49` g/s in 50-digit decimal arithmetic; sensitivity errors
are retained without rounding in JSON. No ODE was numerically integrated,
so no resolution/control campaign is needed. Repository checks, hosted CI
and the one independent review are recorded in [REVIEW.md](REVIEW.md).

**Development decision:** retire the affine, nonnegative-offset,
opening-only **scalar effective-law reduction** for explaining decreasing
high-pressure instantaneous discharge under common-state, ordered-history
operation. Further fitting of that reduction cannot supply the missing sign.
The conditional theorem is useful even without a coffee-specific clock:
no admitted parameter choice changes the conclusion at any common time.
Unresolved target mapping prevents calling this a falsification of Mo2021
physics by Waszkiewicz, and the source's nonaffine/spatial/stochastic features
remain outside the proved scope. Failure to produce an escape is not proof
none exists.

At most one smallest subsequent scope is justified **if** a target-level
exclusion is needed: qualify the existing Waszkiewicz endpoint observation
operator on its original sampling/edge support for ordered discharge
histories. This would settle only the observer join, not traction, common
initial state or the full source model. It is not executed or automatically
authorized. No governing-law port or parameter campaign is selected.
