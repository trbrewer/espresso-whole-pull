# XSV-PANNUSCH-EWP-INPUT-MAPPING-001 C1 result

**Disposition:** `XSV_PANNUSCH_EWP_INPUT_MAPPING_001_NO_QUALIFIED_MAPPING_PRESERVE_INDEPENDENT_INPUT_TREATMENTS` (deterministic reducer branch `C`). The operational mapping set is empty and adjudicated operational candidates are terminally negative or unresolved. Genuine context rows do not override branch C. **PRESERVE_PANNUSCH_AND_EWP_INDEPENDENT_INPUT_TREATMENTS.**

## Authority, correction, and method

EWP base/predecessor merge: `7c79c8c6bf4670cb8ade7fb107ecdfd73afa827e` / tree `808abec7b2e9f5ca6cd42d5786daa293af627f88`. Puckworks authority: `2058d0e947ee9eb92c52d64f6165b810f1fb4732` / tree `a6ffb312473b15be43c1571a893b19873ea47c5a`. C1 starts from reviewed PR head `3e988084455b6dde85321b9447730a3747352ef0` / tree `33fab154953b1e502eca9e69239f6df9353d57fc` and corrects the reducer, primitive inventory, mapping coverage, context semantics, and programme state without changing scientific physics.

The corrected registry separates Pannusch `water_density(T)` from fixed flow-conversion `RHO=980`, separates fixed closure `D32` from the per-grind recomputation, and registers EWP `liquid.density_kg_m3 -> liquidDensity`, required `temperature_K` validation metadata, fixed-zero initial concentration, and indexed species identifiers. Every Pannusch primitive now has a terminal mapping row. Neither density object qualifies: the closure requires constitutive evaluation and a mapped temperature, while `RHO=980` is an internal conversion constant rather than an authoritative scenario liquid property. Neither resolves the independent flow-unit ambiguity.

## Critical flow and other results

Source tables still label programmed flow as mL/s, while `solver.py` computes superficial velocity as `flow_mL_s / 1000 / RHO / ACS`. The complete mass-versus-volume convention remains unresolved and fails closed. C07/C08 histories, `MassData.flow`, `/0.98`, beverage derivatives, pressure inference, clock reconstruction, calibration, refit, and chemistry scoring remain excluded. Chemistry, grind, porosity, diffusivity, viscosity, capacity, inventory, extraction-rate, species-identity, and equilibrium-initial-state transfers remain rejected on their exact gates. No materializer was created.

## Tests and claim ceiling

Focused and repository acceptance evidence is recorded in `PACKAGE_QA_STATUS.json`. No OpenFOAM or Pannusch solver scoring occurred; production solver source, equations, prescribed-flow/pressure/lumped-machine behavior, defaults, cases, calibrated parameters, source bytes, and the Puckworks lock are unchanged.

Claim ceiling: `SOURCE_AUTHORITY_AND_INTERFACE_SEMANTICS_QUALIFICATION_ONLY`. SOURCE_INTERNAL; TARGET_EXPOSED; NOT INDEPENDENT VALIDATION; NOT PHYSICAL VALIDATION; NOT HYDRAULIC VALIDATION; NOT PUCK_FACE_FLOW VALIDATION; NOT PRESSURE_FLOW_VALIDATION; NOT CHEMISTRY VALIDATION; NOT MODEL COUPLING; NOT PRODUCTION QUALIFICATION; NO PRODUCTION ADOPTION.
