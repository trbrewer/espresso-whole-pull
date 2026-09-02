# XSV-PANNUSCH-EWP-INPUT-MAPPING-001 result

**Disposition:** `XSV_PANNUSCH_EWP_INPUT_MAPPING_001_CONTEXT_ONLY_PRESERVE_INDEPENDENT_INPUT_TREATMENTS`. The operational mapping set is empty. **PRESERVE_PANNUSCH_AND_EWP_INDEPENDENT_INPUT_TREATMENTS.**

## Authority and question

EWP base and predecessor merge: `7c79c8c6bf4670cb8ade7fb107ecdfd73afa827e` / tree `808abec7b2e9f5ca6cd42d5786daa293af627f88`. Exact merged Pannusch authority: Puckworks `2058d0e947ee9eb92c52d64f6165b810f1fb4732` / tree `a6ffb312473b15be43c1571a893b19873ea47c5a`. This audit asked whether a source-authorized Pannusch primitive can populate an existing EWP consumer by identity, exact units, or an explicitly source-defined basis conversion without inference, refit, reconstruction, defaults, coupling, or physics change.

## Method and result

The complete bounded Pannusch inventory and current EWP runtime consumers were source-located, role-classified, and compared through the frozen gates. No operational candidate passed all gates. Context-only compatibilities record nominal 58 mm geometry, 20 g scenario, initially saturated state, clean inlet, source temperature metadata, particle context, and observer/run-control facts. They authorize no EWP execution. Chemistry, grind, porosity, diffusivity, viscosity, capacity, inventory, and extraction-rate transfers were rejected for authority, quantity/basis, consumer, state, constitutive, or calibration reasons. No materializer was created.

## Critical flow finding

Source tables label programmed flow as mL/s, but `solver.py` computes superficial velocity as `flow_mL_s / 1000 / RHO / ACS`. The source authority does not unambiguously establish volumetric flow, mass flow, or a numerical water-equivalent convention with the exact density basis. `H_UNRESOLVED` therefore fails closed as `UNIT_OR_BASIS_UNRESOLVED`. Exact hypothetical SI mL/s round trips are recorded only to expose the competing convention; they are not accepted mappings. C07/C08 endpoints, `MassData.flow`, `/0.98`, beverage derivatives, pressure inference, and clock reconstruction remain excluded.

## Tests and claim ceiling

Focused and repository acceptance evidence is recorded in `PACKAGE_QA_STATUS.json`. No OpenFOAM or Pannusch chemistry execution occurred; production solver source, equations, defaults, calibrated parameters, and the Puckworks lock are unchanged.

Claim ceiling: `SOURCE_AUTHORITY_AND_INTERFACE_SEMANTICS_QUALIFICATION_ONLY`. SOURCE_INTERNAL; TARGET_EXPOSED; NOT INDEPENDENT VALIDATION; NOT PHYSICAL VALIDATION; NOT HYDRAULIC VALIDATION; NOT PUCK_FACE_FLOW VALIDATION; NOT PRESSURE_FLOW_VALIDATION; NOT CHEMISTRY VALIDATION; NOT MODEL COUPLING; NOT PRODUCTION QUALIFICATION; NO PRODUCTION ADOPTION.
