# Spatial effective-law pressure feasibility

Scientific analysis for issue [#212](https://github.com/trbrewer/espresso-whole-pull/issues/212).
G1 / `NO_GOVERNING_PHYSICS_CHANGE`; RESEARCH_ONLY, retrospective,
target-exposed, non-scoring. `PHYSICAL_VALIDATION=NOT_ESTABLISHED`.
The equations, assumptions and finite search domain are frozen in [PLAN.md](PLAN.md).
This report's analytical assessment preceded numerical exploration.

## Source and declared reduction

Reuse the [#207 audited sign/unit crosswalk and review](../sci_md_mo_pressure_feasibility_001/RESULT.md).
Mo et al., Physics of Fluids 33, 093101 (2021),
[DOI 10.1063/5.0059707](https://doi.org/10.1063/5.0059707),
[institutional accepted manuscript](https://cronfa.swan.ac.uk/Record/cronfa57912).
Original II B pp. 4–5 was inspected for per-particle mass rate, inward
compression suppressing failure, and the incomplete-wetting motivation for
pressure difference between a grain's exterior and interior. II E's effective
law approximation and pressure/flux normalization limitations remain as audited
in #207. This does not reimplement or validate the full spatial stochastic
spring/bond model, whose force envelope is not exactly Eq. (11).

The new hypothetical closure is a five-edge bridge of supported slit-wall
coatings with common background/interior pressure equal to outlet pressure.
Fluid normal traction relative to that background is inward and compression
positive: sigma_c(s)=p(s)-p_out>=0. Support is rigid; no instantaneous
pressure-dependent compaction is included. This load is local fluid pressure,
not edge drop, imposed bed drop, line pressure or measured solid stress.
No source result supplies this coffee-specific support/loading closure.
It is mechanically specified but physically unvalidated.

Each edge has l=w=L, a=epsilon L x with epsilon=.01 and x0<=x<=2.
Inert, nonoverlapping supports contain separate two-wall finite inventories.
Area-averaged projection gives one uniform aperture even for nonuniform
local erosion. The local positive part is integrated before that projection.
Remaining effective-site density is n_s(2-x)/(2-x0), the same in both runs.
These assumptions, including uniform aperture projection and depletion, are
additional to the source effective law.

## Hydraulic derivation, units and passive controls

For axial coordinate s and transverse y in [-a/2,a/2], Stokes balance is
mu d²v/dy²=dp/ds, no slip at both walls. Thus
v(y)=(-dp/ds)(a²/4-y²)/(2mu). Integrating over width w and full gap a gives
q=w a³ Delta p/(12mu l); |mu dv/dy| at either wall is
tau=a|Delta p|/(2l). Conductance has units m³/(Pa s), q m³/s and tau Pa.
This is the declared ideal wide-slit approximation; end and junction losses
are omitted. Choose common physical scales giving rho_f U a/mu <<1.

Use p_out=0 for the *relative* hydraulic calculation. The interior equations are

    (g_SA+g_AT+g_AB)p_A - g_AB p_B = g_SA P,
    -g_AB p_A + (g_SB+g_BT+g_AB)p_B = g_SB P.

The positive-conductance Dirichlet Laplacian is positive definite: for any
nonzero interior potential perturbation, sum g_e(Delta v_e)²>0 since every
interior node is connected to the fixed boundaries. Hence the solution is
unique, with 0<p_A,p_B<P by the weighted-average maximum principle. Scaling
P scales every p and signed q, so Q=K(x)P and K>0. Kirchhoff conservation
independently gives Q_in=q_SA+q_SB=Q_out=q_AT+q_BT. Multiplying node equations
by p yields P Q=sum_e g_e(Delta p_e)²>=0.

For unit boundary potential, K(g)=min_v sum_e g_e(Delta v_e)².
If any g_e increases, the energy increases at every trial v, so its minimum
cannot decrease (Rayleigh monotonicity). Equivalently
partial K/partial g_e=(Delta v_e)²>=0. Since dg_e/dx_e=3g_ref x_e²>=0
and xdot_e>=0, K and Q at constant P are nondecreasing along each trajectory.
This is not a comparison between trajectories at different P.

All five identical apertures x give p_A=p_B=P/2, zero cross flow and
K*=x³: two equal two-edge series paths in parallel. More generally with
all four outer edges equal, the cross aperture does not affect K. Frozen
geometry (C_E=0) gives Q_H/Q_L=P_H/P_L exactly. In the search bounds,
tau*/pi=x|v_u-v_v|<=2; gamma>=2 pi_H is a globally inactive control.
For example x=.5, gamma=.1, beta=4, pi=1 still gives positive AT/BT
integrated erosion near the outlet: its endpoint brackets are -.85 and .15,
and J=.01125. Thus the declared family is not everywhere inactive.

## Mass, time and invariant domain

C_E is a per-site mass-rate/stress coefficient in kg/(s Pa), n_s is sites/m²,
rho_s is kg/m³; kappa=2n_s C_E/rho_s has units m/(s Pa). Integrating over
both wall areas gives Mdot=2n_s C_E w l b I and
M_removed=rho_s w l(a-a0). Consequently adot=kappa b I. There is no extra
factor two in the full-gap mass formula. Initial inventory is
rho_s epsilon L³(2-x0); removed plus remaining equals it on each edge.
The source's 2D stresses and C'_E are not substituted for these 3D quantities.

One pressure-independent stress scale S_ref=epsilon P_ref/2 and time scale
t_ref=epsilon L/(kappa S_ref) are used. All comparisons have common theta=t/t_ref,
cohesion gamma=c/S_ref and beta=2tan(psi)/epsilon. With unit hydraulic
potential v(x), p*=pi v(x), the complete system is

    J_e(x,pi)=integral_0^1 [pi {x_e|Delta v_e|-beta v_e(s)}-gamma]_+ ds,
    dx_e/dtheta = [(2-x_e)/(2-x_e0)] J_e(x,pi).

For endpoint brackets u,v, the exact integral is zero if max(u,v)<=0,
(u+v)/2 if min(u,v)>=0, and max(u,v)²/[2|u-v|] otherwise.
For example endpoint brackets -3,1 give integral 1/8 although the positive
part of their mean is zero. There is no axial quadrature resolution parameter.

The vector field is Lipschitz on the positive compact aperture box: the
hydraulic inverse is smooth there, absolute value and positive part are
Lipschitz, and integration preserves that property. At the lower faces the
rate is nonnegative; at x=2 it is zero. Equivalently z=-log b satisfies
z'=J/(2-x0)>=0, x=x0+(2-x0)(1-exp(-z)). Bounded rates imply finite z at every
finite theta, so exact finite-time exhaustion cannot occur. This provides
unique invariant solutions and avoids post-step clipping across inventories.
Threshold and signed-AB-flow switches are continuous Lipschitz switches,
not state resets or topology events.

Neglecting growing pore liquid inventory is a controlled slow-erosion limit,
not a finite coffee-scale claim: epsilon L³ sum x'/[t_ref Q_ref Q*] tends
to zero with common kappa at fixed theta. Q*>0 uniformly on the compact
search box. Pressure relaxation is likewise fast relative to t_ref in this
limit. Removed solid is discarded from the hydraulic problem without
transport, deposition, viscosity or beverage-mass contribution. Equal
carrier-liquid inlet/outlet flows apply at this leading order only.

## Ordering results and the remaining mathematical gap

At fixed **complete** x and axial position, write the bracket as
[pi s-gamma]_+. If s<=0 it vanishes for pi>=0; if s>0 it is nondecreasing.
Nonnegative pressure-independent integration/site/mass weights preserve this
order component by component. A pressure-independent preload would replace
gamma by D/S_ref=(c+sigma_0 tan(psi))/S_ref>=0. Thus this model preserves #207's
fixed-state premise despite compression suppressing local yield.

For a unique scalar opening y with F(y,P) nondecreasing in P, common y0
implies y_H>=y_L by the scalar comparison argument of #207; monotone K
then orders Q. No F_y>=0 assumption is required. In the present graph,
beta=0 with identical four outer apertures is such a scalar invariant
subfamily (AB remains inactive). General asymmetric states are not scalar.

If D=0 throughout the domain, including every preload contribution, the
positive part is positively homogeneous: F(x,P)=P G(x). The inventory
factor belongs to G and is pressure independent. Uniqueness gives
x_P(t)=X(Pt); monotone K along X implies
Q_H(t)=P_H K(X(P_H t))>=P_L K(X(P_L t))=Q_L(t).
More generally, if F=alpha(x,P)G(x) with alpha>=0 nondecreasing in P,
one orbit is parameterized by lambda'=alpha(X(lambda),P); scalar comparison
in lambda gives the same exclusion, subject to uniqueness and monotone K.
Finite cohesion alone therefore does not guarantee an escape.

The declared finite-cohesion family does not globally satisfy either of
these sufficient criteria. At x=(1,1,1,1/2,1), beta=0, gamma=1/10,
p_A/pi=25/43 and p_B/pi=32/43. For SA,AT the J vectors at pi=1 and pi=2
are (137/430,207/430) and (317/430,457/430), whose determinant is -7/430.
Positive common inventory weights do not restore collinearity at this
interior state (choose any x0 below it). This also persists for sufficiently
small positive beta by continuity. The exhibited state is an admissible
state, not a demonstrated reachability or discharge-reversal witness.

For active AT at beta=0, with its own aperture fixed,
partial p_A/partial g_BT=-g_AB p_B/det<0, where det is the hydraulic
2x2 determinant. Thus increasing x_BT reduces AT erosion: the system is
not cooperative in the componentwise aperture order. This persists on an
open set of small positive beta. Thresholds/material bounds do not repair a
negative derivative at an interior active state. This defeats that standard
comparison test, not every possible ordering proof. A discharge-specific
ordering invariant for the general finite-threshold network has not been
established in this bounded analysis. Spatial pattern or cross-flow reversal
alone is not positive capability evidence.

## Empirical and development boundary

The primary comparison prescribes bed pressure. Line-pressure applicability
is NOT_ASSESSED; no adapter is applied afterward. The retained adapter is
P=L-h(q), h(q)=0.017184292098914252 q²+0.03670858658698296 q+
0.2831597837775055, with pressures in bar, q in g/s and coefficients in
bar s²/g², bar s/g and bar respectively. It would have to act throughout
evolution with one supported dimensional conversion. Dimensionless Q here
has no supported coffee g/s scale. No finite-cohesion line-pressure claim
or numerical campaign is made.

#207's scalar exclusion remains unchanged. #209's high-negative/low-positive
terminal beverage-delivery signs remain unchanged. #211 remains a quantitative
within-puck observation with unresolved pressure equivalence, observation
response and causal attribution; it does not establish steady flow,
interruption-specific permanent opening, chemical exhaustion or channeling.
No geometry reset or restart simulation is performed. SCI-LC-001A's signed
relative-flow resistance feedback and ineligible terminal result are distinct.

Coffee-specific wall support/interior pressure, cohesion/friction/kinetics,
physical clock, initial geometry and discharge-to-beverage observation joins
are uncalibrated. This study cannot identify an experimental puck mechanism,
validate Mo2021, establish an empirical branch shape/slope, or promote research
parameters to production. Puckworks and the production lock are unchanged.
