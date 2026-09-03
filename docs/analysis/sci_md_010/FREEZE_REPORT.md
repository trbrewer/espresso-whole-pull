# SCI-MD-010 R3 leakage-free equilibrium hydraulic freeze

R3 uses directly measured line `pressure__bar` at the final 100-s grid sample; flow-derived `basket_pressure__bar` is prohibited as an exogenous predictor. The fixed same-campaign brewer calibration is `delta_p=a*q^2+b*q+c`, evaluated only with predicted flow. The primary target is the repository-qualified `endpoint_100s` equilibrium mass flow: one row for each of 56 canonical brews in 11 leave-one-condition-out folds. The alias duplicate is excluded.

B0 is the condition-balanced training mean. B1 is a fixed condition-balanced quadratic in line pressure, capable of one turnover. E1 is the uniform saturated steady fixed-resistance Darcy limit, coupled implicitly to the machine operator with nonnegative conductance enforced. E2 is unavailable and remains NOT_ADJUDICATED. Membership is loaded from the frozen file; weights are equal by condition and brew. The primary loss is heldout-brew RMSE divided by the training condition-mean range. Low (<=5.25 bar) and high (>=8.5 bar) direction gates and a 2,000-replicate nested condition/brew bootstrap use seed 20260902.

Results map only to conditional reduced-Darcy decisions, never retention of full EWP. No Phase B execution or real score occurred. Final independent review is required.

Disposition: SCI_MD_010_R3_LEAKAGE_FREE_EQUILIBRIUM_HYDRAULIC_UTILITY_FREEZE_READY_FOR_FINAL_INDEPENDENT_REVIEW.
