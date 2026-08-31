# EWP-POROSITY-PERMEABILITY-PRIOR-001 result

## Disposition

`EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_AND_PERMEABILITY`. Separate source-conditioned supports materially structure static EWP sensitivity for porosity and saturated permeability. They are not pooled and do not validate EWP physics.

## Scientific question and authority

The bounded question is answered positively for both requested quantities under explicit observation/transfer operators. EWP authority is `9c7b8b286d7a9943c72e35b8ea88cd592949488f` / `fbda7a202423e5787010f1e88b66e16e62ec0a73`; external Puckworks authority is `a3428a4d4ad571ef3168a70e8a04620fca5d3520` / `6175b4ad39f45ebcdec32a176e5611bf3b03655b`. Rights permit analysis of reviewed transcriptions; no publisher PDF or source CSV was copied.

## Change declaration

`SOURCE_SCENARIO_CHANGE_ONLY`; `NO_GOVERNING_PHYSICS_CHANGE`; `NO_PRODUCTION_DEFAULT_CHANGE`; `NO_RUNTIME_PUCKWORKS_LOCK_CHANGE`; `NO_SOURCE_ROW_FUSION`; `NO_HOME_LAB_OPERATION`; `PHYSICAL_VALIDATION_NOT_ESTABLISHED`.

## Definitions and mapping

The machine-readable ledgers freeze EWP initial porosity, separate saturated and wetting permeabilities, geometry, dose, density, viscosity, source state, total/connected basis and transfer limits. Wadsworth total and connected porosity remain separate. Wadsworth XCT/LBflow K is an untamped intrinsic source-conditioned design support, not EWP effective K. Vaca Fig. 12 closes only its dry-porosity operator (n=50, R2=0.941741, RMSE=0.0125352); it has no K. Vaca C.1 retains nine Darcy points and the unpublished-pump-curve limitation. Eq. 11 remains post-fit contextual evidence and was not refit. The reviewed negated-beta convention is preserved.

## Supports and default comparison

Wadsworth retains 22 rows, 21 K values, two coffees and one missing K without imputation. Vaca retains 50 Fig. 12 rows and nine separate C.1 rows. Published-viscosity K and EWP-viscosity re-expression are separate; the latter is not a unit conversion or measurement. The EWP default phi and calibrated effective K are compared source by source in `DEFAULT_COMPARISON.csv`; out-of-envelope status does not imply error or authorize adoption. Wetting K remains the EWP default in every primary case.

## Hydraulic sensitivity and geometry

All 16 bounded cases use unchanged analytical equations; 11 anchors use the unchanged reduced finite-volume twin. Fixed-geometry porosity cases report implied mass inconsistency. Fixed-dose cases recompute depth and all interface/probe positions and conserve 20 g numerically. Saturated-K-only changes steady flow/resistance but not first drip because wetting K is independent. Full OpenFOAM: `NOT_REQUIRED_FOR_SOURCE_QUALIFICATION`.

## Numerical identifiability

The local phi/log10(K) Jacobian uses central steps 0.01 and 0.02 with first drip, steady flow, and saturated pore water. It has rank 2; signatures are locally distinguishable numerical responses, not experimental parameter identification.

## Waszkiewicz and Visualizer

Only frozen merged Waszkiewicz context is used; no search/refit/reranking occurred. Common resistance outputs are contextual, not validation, and `FIXED_RESISTANCE_RETAINED_BY_PARSIMONY` is preserved. No Visualizer mining or fitting occurred; the handoff records a future low/central/high boundary contract.

## Decision, claim, and successor

Source/quantity dispositions are in `DECISION.json`. Maximum claim: `SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY`. Production defaults remain unchanged. Recommended successor: `EWP-REAL-WORLD-BOUNDARIES-001`.

## Production invariants and execution

The production solver, `config/reference_R0.json`, `scripts/prepare_case.py`, and runtime Puckworks lock are unchanged. No governing physics, laboratory plan, source fusion, or physical-validation claim was introduced. Compact tests and command results are recorded in the PR handoff.
