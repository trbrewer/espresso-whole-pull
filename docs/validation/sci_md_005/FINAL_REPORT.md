# SCI-MD-005 production-law species bridge

## Governance and authority

SCI-MD-004 is closed as `SCI_MD_004_REJECTED_PARAMETERIZATION_OR_FORMULATION_COMPLETE`. Its indexed solver, Stage C verification, Stage E0 parameterization, conditional Darcy adapter, immutable Stage E1 prediction bundle, sole scorer receipt, negative result, and governance evidence are unchanged. Angeloni is `CONSUMED_POST_HOLDOUT_COMPARISON_DATA`; this lane neither rescored it nor generated a revised Angeloni prediction.

The starting EWP authority was commit `3748703cfad8eb76a648e3de64871584aa7f66bb`, tree `ebc5299d82f8ee776b40c370021ccc110282eb44`. The read-only Puckworks authority was commit `5ce003e751aac516b5de3d9ede4e6910627e2b12`, tree `d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`. The change declaration is `NO_GOVERNING_PHYSICS_CHANGE`.

The production source `solver/espressoWholePullFoam/espressoWholePullFoam.C` remains SHA-256 `9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599`.

## Consumed comparison decomposition

`SCI_MD_004_FAILURE_DECOMPOSITION.json` uses only committed SCI-MD-004 artifacts. Every H1 species error is negative. Mean H1 inventory utilization is 0.483 for caffeine and 0.608 for trigonelline, while mean inlet back-diffusion is below `5e-6` of initial inventory. The committed result artifacts do not record maximum local concentration, so `max(C)/C_sat` is explicitly unavailable rather than reconstructed by a new execution. The evidence supports `DIRECT_OUTLET_EXPONENTIAL_PARAMETERS_ARE_NOT_SEMANTICALLY_PORTABLE_TO_THE_LOCAL_PRODUCTION_SOURCE`; the observed H1 behavior is transfer-rate/residence-time limited, with boundary loss and inventory exhaustion excluded as primary explanations. C_sat-specific attribution remains inseparable from the missing local maximum.

## Blocking H0 contract contradiction

The generic indexed, no-physics composition closure is implemented in `tools/inventory_scaled_composition/`. It applies one aggregate legacy extracted fraction to arbitrary measured species inventories and reports cup mass, concentration, extraction fraction, aggregate consistency, inventory closure, and uncertainty components.

The required exact-reproduction gate fails. Frozen SCI-MD-004 H0 did not implement the newly specified H0 identity: its indexed caffeine, trigonelline, residual, and aggregate laws used a common **absolute** `C_sat=180 kg/m3`. An absolute concentration ceiling is not inventory-scaled, so the species and aggregate extracted fractions differ. Across 66 frozen cases and 132 species-condition comparisons, the maximum extracted-fraction discrepancy is 0.10538032195259106 and maximum cup-mass discrepancy is `3.644123943515249e-05 kg`. A single common aggregate fraction therefore cannot reproduce the frozen caffeine, frozen trigonelline, and frozen total-solids values simultaneously.

Resolving this would require changing the authorized H0 identity, changing historical artifacts, or changing production semantics. None is authorized. The exact audit is `validation/sci_md_005/H0_EXACT_REPRODUCTION_AUDIT.json`.

## Nonadjudicative attempted training analysis

Before discovery of the exact-reproduction contradiction, the target-independent adapter was run against Schmieder only. Its attempted full-data parameters were caffeine `k=0.09018035261474691 1/s`, `C_sat=13.807107206581305 kg/m3`; trigonelline `k=0.09247858258241895 1/s`, `C_sat=99.99999999999996 kg/m3`. Trigonelline is at the frozen upper bound and therefore fails identifiability. All eight starts converged within 1% objective.

The attempted blocked metrics are nonadjudicative: `J_H0=0.5655143198337991`, `J_H1-production=0.551037582788493`, against a required maximum `0.4806871718587292`; the 15% improvement gate would fail. Caffeine NRMSE changes `0.4607449299099482 -> 0.48909772045411526` and trigonelline `0.67028370975765 -> 0.6129774451228707`. Because the H0 contract is invalid, these values do not select L1 or L2.

Reduced/full parity, profile intervals, leave-one-experiment-out parameter stability, and mesh/timestep qualification were not advanced after the upstream contract blocker. They are `NOT_REACHED`, not passed or hidden inside a joint statistic.

## Result and prospective evidence

Primary result:

`SCI_MD_005_TRAINING_DATA_CONTRACT_BLOCKED`

The concise prospective contract is preserved in `validation/sci_md_005/PROSPECTIVE_INDEPENDENT_DATA_CONTRACT.json`; experimental commissioning remains unauthorized.

The next model-development recommendation is to issue a new G1 authorization that chooses one internally consistent H0 definition and freezes its reference artifacts before any renewed production-law fit. If exact compatibility with historical SCI-MD-004 H0 is mandatory, that historical model must be described as common-parameter indexed transport, not inventory-scaled common extraction. No G2 physics change is recommended from this blocked lane.

Operational next action:

`SCI_MD_005_TRAINING_DATA_CONTRACT_BLOCKED`
