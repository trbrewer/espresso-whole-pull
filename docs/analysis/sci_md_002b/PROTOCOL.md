# SCI-MD-002B prospective protocol

Status: `PROSPECTIVE_FROZEN_ADJUDICATIVE_EXECUTION_NOT_AUTHORIZED`

Change declarations: `NO_GOVERNING_PHYSICS_CHANGE`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`. Evidence class: `POST_OBSERVATION_MECHANISM_DISCRIMINATION`.

## Question and hypotheses

Can pressure-dependent wetting time give high-pressure cells enough extra swelling age to raise axial resistance and reproduce `Q5 > Q9 > Q11`, without pressure-specific tuning or another mechanism? H0 is the increasing-pressure no-swelling control. H1 is the structural incapability of simultaneous wetting with one common relative conductance history. H2 tests one-way Foster arrival times followed by local Mo swelling. H3 asks whether conservative two-way feedback could change capability. H4 brackets bed accommodation. H5 treats the four Mo powders solely as `SYNTHETIC_PARTICLE_SIZE_SIGNATURE_CONTROLS` because no governed source-grind mapping exists. H6 states that hydraulic survival is not unique mechanism identification.

## Evidence and mapping

The canonical protocol reuses `validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json`, exactly as merged SCI-MD-002A did: prescribed basket-pressure groups 5/9/11 bar, the same terminal reporting point, source flow targets, area `0.002463008640414398 m2`, depth `0.01 m`, viscosity `0.000315 Pa s`, and density `965 kg/m3`. One Darcy permeability is anchored at the governed 9-bar endpoint and transferred unchanged. No pressure-specific swelling, accommodation, particle distribution, permeability, or reporting time is allowed.

The EWP source conditions are `EWP_GOVERNED_SOURCE`. Foster and Mo equations/parameters are `PUCKWORKS_PINNED_REFERENCE` at commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`. Axis brackets are `SYNTHETIC_SCREEN_BOUND`; controls and identities are respectively `NUMERICAL_CONTROL` and `DERIVED_IDENTITY`. No new digitization or restricted material is present. Particle/grind transfer is `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`.

## Reduced equations

The fixed-area bed is divided into serial axial cells. Initial one-way wetting obeys the recorded/prescribed constant-pressure Foster limit

`s(t)^2 = 2 k0 (DeltaP + pc) t / (mu phi0)`.

Cell age is `a_j=max(0,t-t_wet,j)` and no dry cell swells. Each fine/coarse representative sphere solves the Mo nonlinear diffusion equation `dc/dt=D(1-c) laplacian(c)` with center symmetry, fixed surface `c=C_M`, and zero initial additional water. Mo Eq. 42 gives particle volume ratio; the two populations are volume-fraction combined. Extraction and solute transport are absent.

For swollen-solid ratio `F_s` and accommodation `lambda`, the explicit volume-consistent map is `V/V0=H/H0=1+lambda(F_s-1)` and `phi=1-(1-phi0)F_s/(V/V0)`. Thus `lambda=0` is fixed height and `lambda=1` is the constant-porosity/free-height endpoint. Fixed area is retained. Relative Carman-Kozeny permeability combines the evolving porosity and Mo Sauter diameter once; cell resistance is `(H/H0)/(k/k0)`, and serial resistance is the arithmetic mean of cell relative resistances. This avoids replacing the single EWP hydraulic scale or double-counting particle size.

The one-way arm freezes initial-state wetting times and then applies swelling. A conservative two-way model would require distributed swelling-water sinks, spatially varying Darcy flux, moving-cell storage, and a supported relation between Mo additional water and continuum liquid storage. The available references do not uniquely close that balance. S2 is therefore prospectively retained as `SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED`; no convenient balance is invented. The one-way arm remains valid within its explicit isolation purpose.

Before full wetting, outlet flow is zero. Records distinguish inlet flow, front-filling flow, swelling-storage uptake, outlet flow, first-drip/full-wetting time, and resistance. The source gate uses terminal outlet mass flow consistently.

## Arms, design, and controls

A0 contains Foster closed-form, capillary/zero-swelling/diffusivity/maximum-swelling, simultaneous-wetting, accommodation endpoint, serial-resistance, fixed-resistance monotonicity, and volume identities. C0 is the frozen no-swelling source triplet. C1 is simultaneous wetting. S1 is one-way wetting-age swelling. S2 is the typed design block. R1 freezes axial, temporal, radial-PDE and structural refinements.

The deterministic 243-row matrix is below both the 1,500 preferred and 2,500 hard caps. S1 uses four unmapped Mo particle signatures, diffusivity multipliers 0.5/1/2, maximum additional-water fractions 0.05/0.1, accommodation 0/0.5/1, and the shared 5/9/11 conditions. Refinements are selected prospectively. No adaptive row exists.

## Gates and dispositions

Gate precedence is authority/artifacts; references/numerics; conservation/physical state; resistance direction; pressure ordering; temporal signature; assumption dependence; particle/grind identifiability; aggregate comparison. Physical/numerical failure cannot be rescued by fit. Ordering margins are `M59=Q5-Q9` and `M911=Q9-Q11`; numerical uncertainty is the maximum matched base/refined absolute margin difference. Pass requires both lower bounds positive, unresolved means either interval contains zero, and rejection means either comparison is robustly nonpositive. RMSE is last.

Required states are finite; wetting monotone and bounded; uptake monotone; particle radii, bulk volume, porosity, permeability, resistance, and pore volume physically positive; no inversion and no clipping. Exact machine dispositions and stop states are frozen in `SCI_MD_002B_PROTOCOL.json`, including the required design blocks and pre-execution terminal state. `SWELLING_SELECTED` is prohibited.

## Execution and pilot boundary

The frozen pilot contains eight analytical, structural, refinement, 9-bar-only, and synthetic-7-bar rows. It contains no adjudicative source row and no complete source triplet. It tests runtime, memory, deterministic records, numerical behavior, and integrity only. It must not calculate ordering or run the scientific reducer.

Adjudicative execution requires a separately owner-created JSON with token `SCI_MD_002B_ADJUDICATIVE_EXECUTION_AUTHORIZED`, exact source/artifact/dependency hashes, namespace, one-worker cap, row set, date, and owner role. The program does not mint this token and refuses execution without it. No such authority exists.

## Claim boundary

`PHYSICAL_VALIDATION_NOT_ESTABLISHED`; `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; `NO_COMBINED_MECHANISM_AUTHORIZATION`; `NO_SCI_LC_001B_AUTHORIZATION`. A later capability survivor would remain a reduced hydraulic capability, not proof of real swelling or a production selection.
