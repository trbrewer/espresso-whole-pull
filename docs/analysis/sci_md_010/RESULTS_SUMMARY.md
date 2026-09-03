# SCI-MD-010 result summary

`NO_STABLE_REDUCED_DARCY_ADVANTAGE_OVER_EMPIRICAL_BASELINE`.

Across 56 physical brews and 11 leave-one-pressure-condition-out folds, B0,
quadratic B1, and reduced Darcy E1 had aggregate normalized losses
0.31786798610901296, 0.1532500174983135, and 0.29894242558587686. The
full-domain B1-minus-E1 delta was -0.14569240808756337 (paired 95% interval
[-0.2487589900770766, -0.036163174040446486]); the low-pressure delta was
-0.11232543181874685 ([-0.2669334833198054, 0.029735204181095785]). B1 won
seven of 11 conditions and alone passed both frozen pressure-direction gates.
All 33 fits/predictions passed and no roots failed.

The architecture decision is `NO_STABLE_ADVANTAGE_OVER_SIMPLE_BASELINE`.
Simplification or reparameterization should precede hydraulic-specific new
data. The experiment recommendation is
`SIMPLIFY_BEFORE_HYDRAULIC_SPECIFIC_EXPERIMENT_M01_NOT_ADJUDICATED`.
Current full EWP E2 is `NOT_ADJUDICATED`; M01 is not adjudicated by L-HYD;
SCI-ED-003 Stage F and Stage D remain unauthorized; physical validation is
`NOT_ESTABLISHED`. This is only retrospective, within-source, conditional
reduced-equilibrium-hydraulic evidence, not independent or grinder-to-cup
validation.
