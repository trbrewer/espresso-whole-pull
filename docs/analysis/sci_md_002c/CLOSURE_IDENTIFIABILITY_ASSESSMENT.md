# SCI-MD-002C closure-identifiability assessment

## Audit conclusion

The pinned Fasano material supports a saturated one-dimensional conservation structure with bound, mobile, and downstream-deposited fines, a moving compact layer, and serial hydraulic resistance. It does not uniquely specify the release equilibrium/kinetics, permeability closures, compact-layer conductivity, real-puck mobilizable inventory, or a mapping to the retained source grinds. Puckworks explicitly implements a mechanism demonstration rather than a faithful quantitative reproduction; values such as `M=5`, `Rc=50`, and `aR=1` are project-selected demonstration controls, not source measurements. Its retained digitized curves have qualitative/structural evidence role only.

The screen can proceed without fitting the retained ordering by using broad, predeclared `SYNTHETIC_CAPABILITY_BOUND` brackets. Survivors, if any, are synthetic-closure capabilities and cannot identify a real fines mechanism.

## Closure ledger

| Quantity or closure | Frozen treatment | Provenance | Identifiability limit |
|---|---|---|---|
| Axial bound/mobile/deposited balance | Conservative finite-volume mass compartments | `PUCKWORKS_PINNED_REFERENCE` | Fasano structure, independently reimplemented |
| Mobilizable fines inventory | Dose × fines fraction × mobilizable fraction | `SYNTHETIC_CAPABILITY_BOUND` | Not measured for retained groups |
| Release law | Finite-inventory first-order rate multiplied by shared velocity-ratio exponent | `SYNTHETIC_CAPABILITY_BOUND` | Fasano leaves key equilibrium/rate functions unspecified; screen form is not source-reported |
| Velocity/gradient dependence | Shared exponent on superficial-velocity ratio | `SYNTHETIC_CAPABILITY_BOUND` | Surrogate, not a measured shear law |
| Axial mobile transport | Conservative upwind advection | `NUMERICAL_CONTROL` | Minimum dispersion-free transport model |
| Dispersion | Zero in primary family | `UNIDENTIFIED_NOT_EXECUTED` | No defensible source bound |
| Downstream retention | Shared prospective bracket | `SYNTHETIC_CAPABILITY_BOUND` | Full retention is not assumed to represent an ordinary basket and is not assumed dominant without proof |
| Compact-layer packing | Explicit porosity bracket | `SYNTHETIC_CAPABILITY_BOUND` | Not measured |
| Specific cake resistance | Positive mass-specific-resistance bracket | `SYNTHETIC_CAPABILITY_BOUND` | Fasano compact-layer conductivity is unspecified |
| Layer thickness | Deposited mass divided by solids density, solids fraction, and filter area | `DERIVED_IDENTITY` | Volume- and mass-consistent |
| Active-bed permeability after loss | Fixed | `NUMERICAL_CONTROL` | Bed opening/channeling is prohibited |
| Hydraulic anchor | One observed P9 terminal-flow scale transferred unchanged | `EWP_GOVERNED_SOURCE` | Reference scale, not clean-bed measurement |
| Saturated start | Source indices 100–899 as inherited governed comparison window | `EWP_GOVERNED_SOURCE` | `SATURATED_MODEL_APPROXIMATION`; no measured first-drip/saturation event |
| Solids density and geometry | Existing EWP conventions where available; otherwise disclosed bounds | `EWP_GOVERNED_SOURCE` / `SYNTHETIC_CAPABILITY_BOUND` | No group-specific retuning |
| Particle-size/grind mapping | Not executed | `UNIDENTIFIED_NOT_EXECUTED` | `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED` |

## Fasano/Puckworks reconciliation and exclusions

Fasano’s structural release form includes a flow-dependent equilibrium threshold, but the paper and pinned implementation do not establish a unique dimensional real-puck mapping. The transient screen therefore uses a simpler explicitly synthetic finite-inventory kinetic family and tests closure dependence. It is not presented as the Fasano equation. The C1 reference arm tests mass balance, declining-flow direction, and compact-layer growth against the pinned mechanism structure without claiming quantitative parity to espresso observations.

The Puckworks multi-streamtube rung is inspected solely to exclude it. Its local flow competition, bed opening, and channel reinforcement overlap SCI-LC and are prohibited here.

## Measurements needed for identification

Direct time-resolved turbidity or outlet fines flux, retained/deposited mass, deposited-layer thickness and conductivity, mobilizable fines inventory, particle-size distributions, and interruption/recovery observations are required to distinguish this mechanism. No synthetic survivor can supply those measurements.

