# SCI-MD-002B prospective protocol

Status: `CORRECTED_PREEXECUTION_PENDING_SECOND_REVIEW`

Change declarations: `NO_GOVERNING_PHYSICS_CHANGE`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`. Evidence class: `POST_OBSERVATION_MECHANISM_DISCRIMINATION`.

## Question and hypotheses

Can pressure-dependent wetting time give high-pressure cells enough extra swelling age to raise axial resistance and reproduce `Q5 > Q9 > Q11`, without pressure-specific tuning or another mechanism? H0 is the increasing-pressure no-swelling control. H1 is the structural incapability of simultaneous wetting with one common relative conductance history. H2 tests one-way Foster arrival times followed by local Mo swelling. H3 asks whether conservative two-way feedback could change capability. H4 brackets bed accommodation. H5 treats the four Mo powders solely as `SYNTHETIC_PARTICLE_SIZE_SIGNATURE_CONTROLS` because no governed source-grind mapping exists. H6 states that hydraulic survival is not unique mechanism identification.

## Evidence and mapping

The canonical protocol reuses `validation/cases/val_corpus_001/results/VAL_CORPUS_001_OVERLAYS_V3.json`, exactly as merged SCI-MD-002A did: prescribed basket-pressure groups 5/9/11 bar, the same terminal reporting point, source flow targets, area `0.002463008640414398 m2`, depth `0.01 m`, viscosity `0.000315 Pa s`, and density `965 kg/m3`. One Darcy permeability is anchored at the governed 9-bar endpoint and transferred unchanged. No pressure-specific swelling, accommodation, particle distribution, permeability, or reporting time is allowed.

The EWP source conditions are `EWP_GOVERNED_SOURCE`. Foster and Mo equations/parameters are `PUCKWORKS_PINNED_REFERENCE` at commit `fc61c4670ec7bf801e40bb391aab16048b8da26b`. Axis brackets are `SYNTHETIC_SCREEN_BOUND`; controls and identities are respectively `NUMERICAL_CONTROL` and `DERIVED_IDENTITY`. No new digitization or restricted material is present. Particle/grind transfer is `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`.

## Reduced equations

The fixed-area bed is divided into serial axial cells. `phi_wet=0.322` is the pinned Foster fitted accessible-liquid porosity used only for front propagation; `epsilon_b0=0.17` is the pinned Mo nominal bed porosity used only for solid/pore/bulk volume and permeability. Neither is a measurement for the retained EWP pressure groups. Prospective sensitivity bounds are respectively `[0.173,0.4]` and `[0.17,0.4]`; the primary reference rows use the stated values without outcome-dependent selection.

Adjudicative source rows load and validate every one of the 999 governed timestamps for P5, P9, and P11 from the exact overlay hash `e69d2b7b0f0ee6945013a0b185da21803d404270a34f1c9d26aed6ecda370c0e`. Piecewise-linear pressure is integrated exactly by the trapezoidal cumulative rule, and cell wetting times use analytic inversion within the bracketing segment. Terminal and transient flow use the governed pressure at each source time. Nominal constant steps exist only as controls.

The constant-pressure Foster limit is

`s(t)^2 = 2 k0 (DeltaP + pc) t / (mu phi0)`.

Cell age is `a_j=max(0,t-t_wet,j)` and no dry cell swells. Each fine/coarse representative sphere solves the Mo nonlinear diffusion equation `dc/dt=D(1-c) laplacian(c)` with center symmetry, fixed surface `c=C_M`, and zero initial additional water. Mo Eq. 42 gives particle volume ratio; the two populations are volume-fraction combined. Extraction and solute transport are absent.

For swollen-solid ratio `F_s` and accommodation `lambda`, the explicit volume-consistent map is `V/V0=H/H0=1+lambda(F_s-1)` and `epsilon_b=1-(1-epsilon_b0)F_s/(V/V0)`. Every temporal cell state calculates initial and swollen solid volume, added particle-water/swelling-storage volume, bulk volume, pore volume, porosity, height, permeability, and resistance. Storage rate is the deterministic adjacent-report finite difference. Exact solid/pore/bulk bookkeeping is closed; whole-liquid conservation is deliberately not claimed because S1 does not feed swelling storage back to the front. Its status is `ONE_WAY_LIQUID_FEEDBACK_NOT_CLOSED_BY_DESIGN`.

The one-way arm freezes initial-state wetting times and then applies swelling. A conservative two-way model would require distributed swelling-water sinks, spatially varying Darcy flux, moving-cell storage, and a supported relation between Mo additional water and continuum liquid storage. The available references do not uniquely close that balance. S2 is therefore prospectively retained as `SCI_MD_002B_TWO_WAY_COUPLING_DESIGN_BLOCKED`; no convenient balance is invented. The one-way arm remains valid within its explicit isolation purpose.

Before full wetting, outlet flow is zero. Records distinguish inlet flow, front-filling flow, swelling-storage uptake, outlet flow, first-drip/full-wetting time, and resistance. The source gate uses terminal outlet mass flow consistently.

## Arms, design, and controls

A0 contains Foster closed-form, capillary/zero-swelling/diffusivity/maximum-swelling, simultaneous-wetting, accommodation endpoint, serial-resistance, fixed-resistance monotonicity, and volume identities. C0 is the frozen no-swelling source triplet. C1 is simultaneous wetting. S1 is one-way wetting-age swelling. S2 is the typed design block. R1 freezes axial, temporal, radial-PDE and structural refinements.

The corrected deterministic 456-row matrix is below both the 1,500 preferred and 2,500 hard caps. Every S1 candidate and pressure has an exact base companion `(64 axial, 32 radial, 65 response points)` and refined companion `(128, 48, 129)`, plus its same-pressure C0 control, cross-pressure peers, and accommodation/particle-size peers. S1 uses four unmapped Mo particle signatures, diffusivity multipliers 0.5/1/2, maximum additional-water fractions 0.05/0.1, and accommodation 0/0.5/1. No inactive `dt_s` or adaptive row remains.

The standard-library implicit radial solve uses a frozen dimensionless step cap of `0.005` and at most 12,000 steps. Its direct pinned Mo sphere comparator has a prospectively fixed absolute volume-ratio tolerance of `1e-4`; no interpolation table or fitted temporal curve is used.

## Gates and dispositions

Gate precedence is authority/artifacts; references/numerics; conservation/physical state; resistance direction; pressure ordering; temporal signature; assumption dependence; particle/grind identifiability; aggregate comparison. Physical/numerical failure cannot be rescued by fit. Ordering margins are `M59=Q5-Q9` and `M911=Q9-Q11`; numerical uncertainty is the maximum matched base/refined absolute margin difference. Pass requires both lower bounds positive, unresolved means either interval contains zero, and rejection means either comparison is robustly nonpositive. RMSE is last.

Required states are finite; wetting monotone and bounded; uptake monotone; particle radii, bulk volume, porosity, permeability, resistance, and pore volume physically positive; no inversion and no clipping. Exact machine dispositions and stop states are frozen in `SCI_MD_002B_PROTOCOL.json`, including the required design blocks and pre-execution terminal state. `SWELLING_SELECTED` is prohibited.

## Execution and pilot boundary

The corrected attempt-3 pilot contains eight analytical, pressure-history, storage, temporal, structural, and matched-refinement controls. It contains no complete adjudicative source triplet. It tests runtime, memory, immutable records, corrected pressure-history handling, and integrity only. It must not calculate ordering or run the scientific reducer. Attempts 1 and 2 remain superseded diagnostic-only records.

The authorized executor is complete but fail-closed. An owner JSON must bind the exact token, task/lane/branch/source identities, all artifact and Puckworks hashes, exact row set, namespace, resource limits, owner/date, record schema, and immutable/exact-resume semantics. The reducer verifies a complete immutable authority-bound bundle, applies the frozen gates, groups candidate triplets and refinements, propagates signed-margin uncertainty, and emits an auditable table. Neither is invoked adjudicatively in this tranche.

Adjudicative execution requires a separately owner-created JSON with token `SCI_MD_002B_ADJUDICATIVE_EXECUTION_AUTHORIZED`, exact source/artifact/dependency hashes, namespace, one-worker cap, row set, date, and owner role. The program does not mint this token and refuses execution without it. No such authority exists.

## Claim boundary

`PHYSICAL_VALIDATION_NOT_ESTABLISHED`; `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`; `NO_COMBINED_MECHANISM_AUTHORIZATION`; `NO_SCI_LC_001B_AUTHORIZATION`. A later capability survivor would remain a reduced hydraulic capability, not proof of real swelling or a production selection.
