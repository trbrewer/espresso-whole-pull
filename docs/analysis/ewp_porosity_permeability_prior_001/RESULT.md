# EWP-POROSITY-PERMEABILITY-PRIOR-001 C2 result

## Disposition

`EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_ONLY`. This evidence-derived result is scoped to porosity only.

## Authority and change boundary

EWP starting authority `c60e7bafd5df9220fa097539cdd364689d564572` / `8a00e97003883e2c2eae89e06fd7395a20c470ac`; Puckworks `a3428a4d4ad571ef3168a70e8a04620fca5d3520` / `6175b4ad39f45ebcdec32a176e5611bf3b03655b`. `SOURCE_SCENARIO_CHANGE_ONLY`; production defaults, solver, reference config, prepare-case behavior, runtime lock, governing physics, and laboratory status are unchanged. Physical validation is not established.

## Mapping dispositions

Exactly two propagated EWP-eligible porosity supports were established: `WADSWORTH_TOTAL_XCT_POROSITY` and `VACA_TABLE_C1_EPSILON_0`. Under `VACA_FIGURE_12_OPERATOR_QUALIFICATION_ONLY`, Figure 12's 50 measured/calculated dry rows qualify the closed source operator but are not propagated as additional EWP supports. They contribute zero to the eligible count and establish neither wet operating-puck porosity nor physical validation. Permeability retains zero EWP-compatible supports and three stress-only representations. Wadsworth connected porosity and Vaca Eq.11 remain contextual.

## Computed porosity materiality

`EWP_PP_PRIOR_001_POROSITY_MATERIALITY_RULE_V1` uses fixed-dose, mass-conserving median cases at 9 bar against `EWP_BASELINE`. The owner-frozen 5% engineering floor is not publication-derived. Maximum convergence uncertainty is 0.00119617625; multiplier=10.0; computed threshold=0.05.

- `WADSWORTH_TOTAL_XCT_POROSITY` / `WADS_TOTAL_PHI_DOSE_MEDIAN`: first_drip_time_s=0.9679970210580598, steady_outlet_flow_m3_s=0.24733333333333332, effective_hydraulic_resistance=0.32860938883968116, final_water_mass_kg=0.3830815966297451, time_to_target_yield_s=NOT_COMPARABLE_TARGET_NOT_REACHED; qualifying=4; material=true.
- `VACA_TABLE_C1_EPSILON_0` / `VACA_PHI_DOSE_MEDIAN`: first_drip_time_s=0.3502889233925143, steady_outlet_flow_m3_s=0.19999999999999982, effective_hydraulic_resistance=0.16666666666666657, final_water_mass_kg=0.2783186565378244, time_to_target_yield_s=TARGET_REACHABILITY_CHANGED; qualifying=5; material=true.

Material supports=2/2; all supports material=true; overall computed gate=true.

## Execution and bounded interpretation

The unchanged EWP equations ran 82 analytical cases: 21 Wadsworth pairs, 18 Vaca pair representations, 27 within-source factorial diagnostics, 15 pressure responses at 3, 9, and 12 bar, seven reduced anchors, and 12 convergence rows. Source K substitutions can generate extreme outputs; these are stable stress evidence outside defensible transfer interpretation, not source error.

Waszkiewicz remains `NOT_COMPARABLE_EXACT_RANGE_UNAVAILABLE`; no overlap claim is made. `FIXED_RESISTANCE_RETAINED_BY_PARSIMONY`.

## Decision and claim

Gate inputs in `DECISION.json`: eligible porosity=2, eligible permeability=0, stress-only=3, qualified operators=1, unresolved=0. Maximum claim: `SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY`. The decision consumes the same computed materiality object written to `POROSITY_MATERIALITY.json`; it is not calculated independently here. No default adoption, universal distribution, dry-equals-wet, home-lab, or physical-validation claim is made.

## Tests and exact-head readiness

Final exact test and skip counts are recorded in the PR description after manifest reconciliation and pushed-head CI.
