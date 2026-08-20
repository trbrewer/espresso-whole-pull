# SCI-MD-002C prospective protocol

## Question and hypotheses

Can one pressure-shared, finite-inventory, mass-conserving axial fines release/transport/deposition mechanism create enough higher-pressure resistance to reproduce `Q5 > Q9 > Q11`? H0 is the no-fines wrong-order control. H1 requires inventory and packing feasibility. H2 tests axial deposition capability. H3 tests retention dependence without assuming full-retention dominance. H4 and H5 test unidentified release and compact-layer-conductivity dependence. H6 prohibits grind transfer. H7 states that capability cannot identify fines without direct particulate/deposition evidence.

This is `POST_OBSERVATION_MECHANISM_DISCRIMINATION`; `PHYSICAL_VALIDATION_NOT_ESTABLISHED`.

## Authority and source mapping

The governed overlay SHA-256 is `e69d2b7b0f0ee6945013a0b185da21803d404270a34f1c9d26aed6ecda370c0e`. Its exact columns are source time, solver time, observed pressure, predecessor/reference pressure, observed flow, predecessor/reference flow, observed mass, and predecessor/reference mass. Observed pressure forces the model and observed flow alone is the comparison target.

The saturated-model approximation is the already governed protected comparison window at source rows 100–899 inclusive: exactly 800 samples from 10.01001 through 89.98999 s. Pressure is piecewise linear between exact samples and is evaluated at each numerical-substep midpoint; exact source pressure is retained at reporting timestamps. This is not a measured first-drip or full-wetting event. No claim is made outside the selected window.

The hydraulic scale is one observed P9 full-overlay terminal-flow reference transferred unchanged to P5 and P11. It is not a clean-bed measurement. No fines parameter is pressure-specific.

The model begins the selected window with `WINDOW_START_FULL_UNRELEASED_INVENTORY`, distributed uniformly over the axial cells, and zero mobile fines, deposited mass, escaped mass, and cake resistance. This is a `SYNTHETIC_WINDOW_START_RESET`, not an observation at 10.01001 s; `PRE_WINDOW_FINES_STATE_NOT_ADJUDICATED`. No initial-state axis is added.

## Model

The geometry is a one-dimensional 10 mm bed split into serial finite-volume cells. State consists of bound mobilizable fines in each cell, mobile fines in each cell, escaped fines, deposited fines, compact-layer thickness and resistance, fixed active-bed resistance, and aggregate flow.

The primary synthetic release closure is

\[
\dot M_{b,i}=-k_{rel}(u/u_{ref})^nM_{b,i}.
\]

It is a prospective `SYNTHETIC_CAPABILITY_BOUND`, not the unidentified Fasano equilibrium law. Exact exponential depletion prevents release beyond remaining inventory. Mobile mass uses conservative first-order upwind compartment transport with CFL-controlled internal subcycling and zero dispersion. `particle_velocity_ratio=1.0` is fixed as a `SYNTHETIC_CAPABILITY_UPPER_BOUND`: fines move at the fastest admissible velocity, and robustness to particle retardation is not established. At the outlet, shared retention fractions 0.5 and 1.0 are both in the primary matrix because full-retention dominance is not assumed. Deposited and escaped fluxes sum exactly to outlet fines flux.

The compact layer obeys the mass/volume identities in `FEASIBILITY_BOUNDS.md`; added resistance is nonnegative and zero at zero deposited mass. Flow is

\[
Q(t)=\Delta p_{obs}(t)/(R_{bed,0}+R_c(t)).
\]

Active-bed resistance is fixed. Release never opens the bed. No lateral, swelling, compaction, chemistry, machine, or combined mechanism is present. No clipping is permitted.

## Matrix and numerical design

The canonical JSON contains 585 transient rows: six non-adjudicative controls and an exact 579-row future cohort (3 C0 plus 576 S1). There are 96 physical candidate stems. Each has P5/P9/P11 and matched base/refined records. Axes are fines fraction 0.02/0.06/0.10; mobilizable fraction 0.25/0.75; release coefficient 0.02/0.10 s⁻¹; velocity exponent 1/2; retention 0.5/1.0; compact-layer porosity 0.5; and specific cake resistance (10^{12}/10^{13}) m/kg. All physical axes are synthetic capability bounds. Base uses 32 axial cells and one temporal subdivision; refined uses 64 cells and two temporal subdivisions. CFL-controlled transport subcycling remains operational in both.

For each pressure margin, uncertainty is the absolute difference between base and refined margins. `PASS` requires both base margins minus uncertainty to remain positive. `REJECTED` applies if either base margin plus uncertainty is nonpositive. Otherwise ordering is `NUMERICALLY_UNRESOLVED`. Mass absolute tolerance is 2e-12 kg, frozen before execution.

## Arms

- A0: zero limits, finite inventory, conservation, transport refinement, serial resistance, and durable-record controls.
- B0: closure-independent feasibility records, separate from transient row count.
- C0: three governed no-fines controls.
- C1: `INDEPENDENT_STRUCTURAL_IDENTITY_CHECKS`, `PUCKWORKS_PROVENANCE_BOUND`, and `NO_QUANTITATIVE_REFERENCE_PARITY_CLAIM`.
- S1: the primary governed axial fines-deposition family.
- S2: no deferred conditional run; retention 0.5 and 1.0 are already in S1 because dominance is not assumed.
- R1: base/refined numerical comparisons.

## Temporal contract

Every source-conditioned record contains all 800 exact window timestamps with observed pressure, predicted and clean-bed flow, bound and mobile mass, interval and cumulative release, outlet flux, retained/escaped increments and cumulative masses, layer thickness and resistance, total resistance, and fines-mass residual. The validator independently checks every release, mobile, outlet, retained, escaped, deposition, geometry, resistance, flow, monotonicity, source-time, source-pressure, conservation, and terminal-summary identity at frozen absolute/relative tolerances. Rates equal their interval increments divided by interval duration; cumulative release and outlet transport equal running increment sums; pressure integral equals running midpoint quadrature under piecewise-linear forcing. The first row must reproduce the exact synthetic reset with zero rates, increments, cumulative quantities, and pressure integral.

## Gate precedence and reduction

Gate 0 validates source/tree/dependencies/hashes/authority/bundle UUID/exact physical file set/cohort/records and all three complete zero-fines C0 controls. Gate 2 separately records numerical mass conservation, physical-state validity, finite-inventory feasibility, and compact-layer geometry validity. Terminal and temporal fields are read only after their prerequisite status and validity gates. Only a valid candidate whose retention-adjusted optimistic maximum cake resistance misses the joint bounds receives `SCI_MD_002C_REJECTED_INSUFFICIENT_FINES_INVENTORY`; conservation failure is numerical invalidity. A family rejection requires complete adjudication of all four analytically feasible release stems; without a survivor, any invalid feasible stem yields the numerical-invalid family disposition. Subsequent gates are resistance direction, signed ordering, temporal signature, retention and closure dependence, grind identifiability, and aggregate comparison.

Survivor support is reported across retention, release coefficient and exponent, total mobilizable inventory and its primitive factors, cake resistance, fixed layer porosity, and particle velocity. Primary dependence precedence is extreme inventory, full retention, single retention, release closure, layer conductivity, then bounded synthetic capability; overlapping restrictions remain secondary flags. Fixed compact-layer porosity and particle velocity are not robustness axes.

The exact machine-readable dispositions are frozen in `SCI_MD_002C_PROTOCOL.json`. Capability is always qualified as synthetic-closure capability; `FINES_SELECTED` and physical-validation language are prohibited.

## Execution authority and durability

Production code calculates mechanical bindings but cannot provide the token, owner role, owner date, or UUID. Adjudicative execution requires an independently supplied exact full-cohort authority containing `SCI_MD_002C_ADJUDICATIVE_EXECUTION_AUTHORIZED` and `HUMAN_REPOSITORY_OWNER`. Partial, reordered, stale, broadened, or wrong-UUID authorities fail before any row starts.

Each immutable record and the manifest use temporary write, flush, `fsync`, atomic rename, directory synchronization where supported, immediate readback/JSON parse, internal-hash verification, and full-file size/hash verification. Exact resume verifies every completed record and refuses corruption.

## Pilot and claim boundary

The eight frozen pilot IDs contain no complete source-conditioned candidate triplet; no ordering or scientific reduction is permitted. One worker and nested thread, no GPU/OpenFOAM, and 16 GiB maximum RSS apply.

Standing claims: `NO_PRODUCTION_GOVERNING_PHYSICS_CHANGE`, `NO_COMBINED_MECHANISM_AUTHORIZATION`, `NO_SCI_LC_AUTHORIZATION`, `NO_OPENFOAM_AUTHORIZATION`, `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`, and `FINES_CLOSURE_PARAMETERS_NOT_ESTABLISHED_AS_REAL_PUCK_MEASUREMENTS`.
