# EWP-POROSITY-PERMEABILITY-PRIOR-001 C1 result

## Disposition

`EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_ONLY`. This evidence-derived result is scoped to porosity only: no permeability representation has a closed transfer from source-native quantities to calibrated EWP effective saturated permeability.

## Authority and change boundary

EWP starting authority `98623e6853428ea65ace9de796d9619b209a698f` / `00a8f24dbd19912f14d426a4461f44a162271aa0`; Puckworks `a3428a4d4ad571ef3168a70e8a04620fca5d3520` / `6175b4ad39f45ebcdec32a176e5611bf3b03655b`. `SOURCE_SCENARIO_CHANGE_ONLY`; production defaults, solver, reference config, prepare-case behavior, runtime lock, governing physics, and laboratory status are unchanged. Physical validation is not established.

## Mapping dispositions

Wadsworth total XCT porosity: useful source-conditioned dry support. Wadsworth connected porosity: contextual only because it is not EWP total field porosity. Wadsworth XCT/LBflow permeability: source-native stress support only. Vaca Figure 12 measured dry porosity: useful support; calculated dry porosity: closed source operator under the reviewed negated-beta convention. Vaca C.1 epsilon_0: useful source-conditioned dry support. Both C.1 K representations are source-native stress supports only; the EWP-viscosity representation is a convention re-expression, not a new measurement or unit conversion. Eq.11 remains post-fit contextual evidence. All porosity units are dimensionless `1`.

## Execution

The unchanged EWP equations ran 82 analytical cases: 21 Wadsworth observed pairs, 18 separate Vaca pair representations, and 27 within-source factorial stress diagnostics without cross-source fusion. The preregistered pressure grid is 3, 9, and 12 bar (15 responses). Wetting K remains unchanged in every primary saturated-K diagnostic. Interaction residuals are numerical decompositions only.

## Convergence and extreme outputs

Reduced-twin convergence uses axial cells 128/256/512 and dt 0.04/0.02/0.01 s for four anchors. All 12 results are finite; maximum relative-to-finest difference is 0.00119618. Source K substitutions can generate extreme flows and masses. They are `NUMERICALLY_STABLE` but `OUTSIDE_DEFENSIBLE_TRANSFER_INTERPRETATION`; this diagnoses transfer incompatibility/stress behavior, not source measurement error.

## Waszkiewicz context

The frozen merged artifact supplies a post-fit characteristic static value Pc/Qc = 6.53241961 bar/(g/s), but no exact empirical minimum/maximum and a different resistance definition. The corrected result is `NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE`; no overlap claim is made. `FIXED_RESISTANCE_RETAINED_BY_PARSIMONY`.

## Decision and claim

Gate inputs are frozen in `DECISION.json`: eligible porosity supports=4, eligible permeability supports=0, stress supports=3, unresolved=0; source authority, execution, pressure response, convergence, and production invariants pass. Maximum claim: `SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY`. No default adoption, universal distribution, dry-equals-wet, home-lab, or physical-validation claim is made.

## Tests and exact-head readiness

C1 focused tests: 18. Related programme-state regressions: 27. The pre-manifest complete suite ran 1,151 tests with 2 skips; its only expected failures were the deliberately stale source manifest, which is regenerated last. Final exact-head suite and GitHub check statuses are recorded in the PR description after final manifest reconciliation and pushed-head CI.
