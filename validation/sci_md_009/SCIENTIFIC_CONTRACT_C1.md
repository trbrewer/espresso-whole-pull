# SCI-MD-009-C1 supplemental scientific contract

This correction preserves frozen production physics and parameters and permits
at most 150 new target-blind production cases. The original 498-case cap and
matrix remain historical.

Deterministic seed: 90091. Conditions are the lowest-flow, median-flow, and
highest-flow sanitized envelopes with condition ID as tie-breaker. Each uses 24
quadratic-response training points and 6 independently generated validation
points. Species coordinates are independently permuted. Bounds are M0 scale
0.1--3.0 and the frozen k/Csat 95% intervals. Six D +/-10% cases are included.
No adaptive point addition is permitted.

The quadratic log-response model contains intercept, three linear, three
squared, and three pairwise-interaction terms per fraction, species, and
condition. Held-out relative RMSE must be <=0.5%, maximum relative error <=2%,
and absolute error below the 1% measurement scenario and one tenth of the
smallest B0/production separation. It must not extrapolate.

Local derivatives at 0.5%, 1%, and 2% pass componentwise when both alternate
steps differ from 1% by <= max(5% of the 1% magnitude, 1e-8 kg). Numerical
derivative noise is the largest component difference between baseline 1%
derivatives and refined-timestep, refined-mesh, repeated, or alternate-rank 1%
derivatives. Singular values must exceed ten times that measured floor after
observable/covariance scaling.

Nonlinear profiles re-optimize both nuisance parameters on a deterministic
bounded grid. Joint recovery varies all three parameters, uses at least five
starts, noise 1/2/5% plus an absolute 1e-9 kg floor, and records all estimates.
Practical identification requires rank three, bounded profiles, median error
<=10% and 95th percentile <=20% for every parameter, <10% boundary hits, and
<5% optimization failure, separately for both species.

Measurement scenarios are conditional 1/2/5/10% because accepted evidence does
not select one. They include shared 50%-of-level shot/recovery correlation and
independent remaining assay error. Pilot adequacy therefore cannot be called
unconditional unless every scenario passes. E-optimal information and joint
synthetic recovery select designs; no minimum condition, replicate, fraction,
or spent-puck count is imposed by name.
