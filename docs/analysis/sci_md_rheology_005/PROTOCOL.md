# SCI-MD-RHEOLOGY-005 contract

G2 / GOVERNING_PHYSICS_CHANGE, under the owner directive; issue #157, one
branch and focused unmerged EWP PR. Defaults remain unchanged. No Puckworks
writes, runtime lock update, laboratory work, adoption, merge or successor.
PHYSICAL_VALIDATION remains NOT_ESTABLISHED. This is an exposed source-conditioned
computational comparison, not a protected holdout, physical truth or speed test.

## Authority, availability and task selection

Fetched EWP main is accepted 004 merge ab29a805217010f8c441047aaa04e6b4adaca3fe,
tree 3437fa55ea8510cdebfd66c15ec8ac75e3e3fcb6. There are no subsequent main
commits or prior 005 lane. Fetched Puckworks main is analysis authority
2058d0e947ee9eb92c52d64f6165b810f1fb4732, tree
a6ffb312473b15be43c1571a893b19873ea47c5a. Actual Git objects match the accepted
records. Production dependency remains fc61c4670ec7bf801e40bb391aab16048b8da26b,
tree 1d553e44ee2f7480a5df521560801b478618cc84; it is not the analysis source.

Accepted 001–004 protocols, results, source-use/audit records and implementations
supply the inherited evidence. Their conclusions concern frozen local fields,
local feedback, law robustness and C/N delivery, respectively; none answers
independent bulk-state evolution. Existing external science directories,
scenario inputs, tables, logs and original/corrected executable identities are
verified by REUSE.json and PROPERTY.json. The source audit is reused, not repeated.
The original 002 science executable and accepted parser-corrected executable
remain distinct under its POST_RESULT_AMENDMENT. Candidate C controls receive
new 005 identities and must qualify unchanged local behavior before refinements
are used. Historical files and all predecessor semantics remain unchanged.

Available-data-first preflight: the accepted measured TR loader, SW equation,
source cards, provenance and capability register already support this bounded
source-conditioned calculation. No new source search, experimental target or
inventory inference is needed. NEW_INFORMATION is autonomous G pressure,
transport and extraction feedback, which cannot be inferred from saved C.
Positive: this specific scalar approximation meets selected-output budgets in
the tested regime; negative: retain local coupling for the named failed outputs;
unresolved: no simplification claim. None authorizes adoption or another task.
GRINDER_TO_CUP_LINK is the hydraulic/aggregate-delivery constitutive decision.
No species-inventory/E2C/Visualizer repeated blocker is reopened. LOWER_COST
same-state resistance reconstruction cannot answer independent predictive
adequacy; accepted C/N/W evidence supplies context at no new campaign cost.

## Mathematics and interface

C = accepted locally coupled model. G = independently evolving bulk-state model.
N = accepted reference-calibrated constant viscosity. W = water viscosity.
Primary comparison is G versus C; C is a computational reference.

Freeze spelling: `aggregate_viscosity.mode = "bulkCoupled"`, generated native
`aggregateViscosityMode bulkCoupled`. At the beginning of [t_n,t_n+dt], from
G's own accepted c_i^n (kg/m3 pore water), static phi_i and V_i (m3):

    Vp = sum(phi_i V_i)
    Md = sum(phi_i c_i^n V_i)
    cbar = Md/Vp
    wbar = Md/(rho_water Vp + Md)
    muG = f(wbar)
    mobility_i = k_i/muG

Each local sum is reduced once across MPI ranks, then scaled to the full basket
with 2*pi/sin(wedgeAngle). Vp is pore-water m3; Md is stored dissolved kg;
wbar is wet-basis dimensionless; muG is Pa.s. Scaling cancels in the ratio,
not in reported extensive quantities. This is neither remaining inventory,
outlet/cup TDS, discharged solute nor an unweighted average of fractions or mu.
No alpha or other calibration parameter is introduced.

Native pressure and conservative darcyFlux=-pressureEquation.flux() feed the
unchanged extraction/transport/inventory advance exactly once. Beginning-step
lag is retained; no nonlinear iteration or imported C trajectory. Scalar mu
and mobility coefficient boundaries update before pressure, including processor
patches. Local law evaluation still rejects invalid cells before and after
advancement even when bulk storage lies in-domain. Existing correction-mass
handling is preserved.

Supported envelope is exactly 002: fresh saturated static uniform or axial-two-layer
Darcy, positive constant prescribed pressure difference, complete single aggregate,
363.15 K and rho=965 kg/m3. Independent generation and native startup reject
unsupported modes. No restart, histories, prescribed flow, machine coupling,
mechanics, changing k, indexed species, multiphase, variable density/thermal
or non-Newtonian extension. Current solver initializes static porosity uniformly;
cell-weighted implementation/analytical fixtures do not add a new material interface.

`aggregate_intervals.csv` preserves C/W/N semantics. For G its Q_cont describes
the applied uniform coefficient. Its mu extrema and dilute fractions remain
explicitly **counterfactual local-law diagnostics**, including accepted next-state
mu extrema; they do not describe applied G viscosity. G-only
`aggregate_bulk_intervals.csv` records state/end times, full-basket Vp, Md,
cbar, wbar, applied mu, native Q, applied continuum Q and counterfactual local Q.
Main hydraulic analytical diagnostics use the applied G coefficient as well.

For the axial-series continuum, R_C=(1/A) integral(mu_C/k dz),
R_k=(1/A) integral(1/k dz), and mu_eff_C=R_C/R_k is an identity from C's state.
It is not G's closure. Nonlinear f and different phi*V versus V/k weights
imply f(cbar/(rho+cbar)) != mu_eff_C generally. No C-resistance forcing is used.
This continuum identity is distinct from native arithmetic face interpolation.
Synthetic fixtures cover nonuniform phi/V, consistent scaling, subdivision,
uniform c, constant law, heterogeneous non-equivalence and local invalidity.

## Inputs and execution

Copy 001 SCENARIOS.json objects uniform_9bar and reversed_3bar through accepted
002 scenario(): geometry, k, phi=.4, c=0, 0.0056 kg initial inventory, rate .15/s,
capacity 180 kg/m3, diffusion 1e-9 m2/s, fixed pressures and 0–30 s unchanged.
They change pressure and layering together and cannot identify their separate effects.
Base 512x4, dt=.02; temporal dt=.01; spatial 1024x4, dt=.02; SW property uses
base mesh/dt with accepted refined table. Field output cadence is inherited.

Exactly TR_LINEAR and SW_WATER_ANCHORED_90C, using the approved common native
piecewise-linear evaluator and accepted tables. TR retains industrial-extract
transfer and dilute linear continuation; SW retains industrial/reconstituted
transfer, water anchoring and explicitly labelled 90 C temperature extrapolation
from its recorded 0–80 C source. No source ranking or new physical validation.
Qualified TR exporter reproduces the exact accepted table; every measured
breakpoint and linear dilute segment is preserved. Thus no distinct TR property
refinement exists and its contribution is zero. SW base/refined table hashes,
qualified exporter/source receipt and dense candidate native equivalence are
checked by prepare.py. Native/Python <=1e-12 for SW; table/law <=1e-4 and inherited
TR native/adapter <=1e-4. All tables/restricted payloads remain external.

Full planned executions: 6 TR G + 8 SW G + 4 base candidate C = 18. C controls
run first. No new N/W runs or predecessor campaigns. Frozen N alpha values and
accepted N/W histories remain contextual evidence only. At most four additional
full attempts solely for documented nonsemantic execution/QA recovery; absolute
ceiling 22. STARTED is appended and fsynced before launch; failed directories,
logs and attempts remain. Recovery requires a prior terminal failure in that
slot and a reason, never altered parameters, scores, grids or longer duration.
A frozen execution-root hash prevents accidentally starting another campaign.

Short matrix, completed before freeze: for both scenarios, 32x2, dt=.02, 0–.2 s:
accepted absent, candidate absent/off, accepted/candidate observe and coupled,
and candidate constant-law C/G (18 total). Add evolving layered G serial/repeat/
2-rank MPI, uniform zero-extraction G, layered constant-G 64x2 refinement (5).
These 23 engineering runs have no science scores. Eleven native startup
rejections bypass generation; generation rejection fixtures are separate.
Short exact baseline uses accepted corrected 002 executable. No full run is
permitted before a genuine independent pre-scoring audit of this freeze.

## Observer, budgets and qualification

Use unchanged 004 full-interval observer: B=W_out+S_out, S=S_out, zero-mass origin
and every interval; split water, solute and time conservatively at B boundaries.
B is modeled beverage mass, not a validated scale measurement. Zero-mass TDS is
undefined. Before discrepancies write SUPPORT.json with one B* per scenario,
minimum across both laws and all required C/G sets, capped at inherited 004 B*.
Missing arms make support provisional. Coverage ratio B*/B004 must be >=.95
for overall sufficiency. No extrapolation, favorable-window choice or longer run.
Use exactly five equal B fractions, including the first; fraction TDS=100 dS/dB.

    E_Qint = sum(|QG-QC| dt)/sum(QC dt)       budget .01
    E_Qpeak = max(|QG-QC|/QC)                budget .02
    E_Spath = max_B |SG(B)-SC(B)|/SC(B*)     budget .01
    D_TDS = 100 max_j |dSG/dB-dSC/dB|        budget .10 pp

Complete matching native intervals over 0–30 s supply hydraulics; no sparse
trapezoids. Mass extrema use union of native B breakpoints. Inherited observer
is called compare(G,C), so its second-arm denominator is C; output labels are
translated explicitly to G/C. Report time to B*, fixed-time masses, signed
fraction TDS, stored/remaining mass, boundary loss, corrections, conservation,
local admissibility and applied bulk viscosity without fitting.

For each metric: u = |temporal-base| + |spatial-base| + |property-base| +
max float64/longdouble arithmetic discrepancy + hydraulic operator allowance
(hydraulic metrics only). Paired refinement deltas contain C and G changes
once; do not add separate arm refinement effects. Sampling/quadrature is zero
for complete discrete intervals. These are empirical allowances, not confidence
intervals or rigorous PDE bounds.

Operator allowance explicitly inherits the conservative native/continuum envelope.
For each set define dC=|QC-QCcont|, dG=|QG-QGcont|,
econt=|QGcont-QCcont|/QCcont. E_Qint contributions are
sum(dC dt)/sum(QC dt), sum(dG dt)/sum(QC dt), and
E_Qint_cont*sum(dC dt)/sum(QC dt). E_Qpeak contributions are
max(dC/QC), max(dG/QC), max(econt*dC/QC). For each contribution take the maximum
across sets and add the three once. Report all C/G/denominator terms separately;
this includes C denominator propagation and does not rely on cancellation.
It describes an additional operator envelope, not another mesh-refinement term.
Never substitute it for a solute-delivery estimate.

Require u<=20% of its budget. Qualified pass: value+u<budget; qualified failure:
value-u>=budget; otherwise unresolved. Insufficient if any admissible qualified
metric fails, while missing/unresolved siblings remain visible. Sufficient only
if all 16 metrics pass with full evidence, adequate coverage and engineering
gates; otherwise unresolved. No threshold, denominator, fraction or case change
after scores. Engineering failure is not scientific rejection.

Carry 002/003/004 gates by reference to their PROTOCOL.md and observer.validate:
water/solute balance <=1e-8 kg; total absolute corrections <=1e-10 kg;
c >=-1e-10 and <=180+1e-8 kg/m3, w<=.24; inventory >=-1e-12 and
<=.0056+1e-10 kg; dissolved storage >=-1e-12 kg; Qdt-volume <=1e-15 m3;
water increment-rho Qdt <=1e-14 kg; contiguous intervals/time tolerances unchanged.
Short analytical and multiplier relative <=1e-6; baseline normalized difference
<=1e-10; repeat absolute <=1e-12; MPI normalized <=1e-6 with 1e-8 floor and
balances separate; layered continuum error decreases under refinement.
Base C full controls use the inherited normalized all-column <=1e-10 gate.

Freeze binds source, case, property, executable, tools, tests, gates and reuse.
Final exact-head independent G2 review, source/static/Python/baseline/shell/CI
checks remain required and are reported separately from scientific disposition.
Failure rejects this specific pore-volume closure only; success covers selected
hydraulic/aggregate outputs only, not internal-field equivalence, physical espresso,
whole-shot transfer, taste or implementation speed. No operational adoption follows.

## Pre-scoring review correction

Independent audit of 4d08f32 found the maintained case generator's legacy preview/
B0 exclusion recognized only coupled. Before any full attempt, extend that same
guard to bulkCoupled and test generated NOT_APPLICABLE/no-B0 output. No native
coefficient, physical input, metric, threshold or executable changed; accepted
short solver results remain applicable. Original contract and failed review are
preserved in Git/external review history. A preparatory unit fixture also replaced
a decimal subtraction equality assertion with an unambiguous above-budget value;
production decision arithmetic was unchanged. Final freeze follows passing tests.
