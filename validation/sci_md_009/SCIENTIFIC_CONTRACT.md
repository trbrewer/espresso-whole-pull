# SCI-MD-009 scientific contract

Change declaration: `NO_GOVERNING_PHYSICS_CHANGE`. Evidence class:
`TARGET-BLIND_FROZEN-PHYSICS_SENSITIVITY_IDENTIFIABILITY_AND_EXPERIMENTAL_DESIGN`.
Physical validation remains `NOT_ESTABLISHED`.

The production law, B1 uniform and B2 frozen axial-two-layer geometries, exact
fraction observer, prescribed-flow boundary, and caffeine/trigonelline
parameters are frozen at the starting espresso-whole-pull tree. No observed
species concentration or mass is permitted. Source operating fields are loaded
only through an explicit whitelist projection. Schmieder asymptotic inventories
are `TRAINING_DERIVED_NOMINAL_SCALE_FOR_DIMENSIONLESS_CENTERING`, never truth
or measurements.

The preregistered global inventory scales are 0.01, 0.03, 0.1, 0.3, 1, and 3.
The optional 10x point is prospectively omitted because it would make the
legacy total extractable fraction 2.8 and is therefore inadmissible. Local
log-derivatives use symmetric 0.5%, 1%, and 2% perturbations; the 1%
pair is adjudicative. Frozen k and Csat 95% intervals are used globally; D uses
-10%, nominal, and +10% target-blind sensitivity scenarios. The execution cap
is 500 production cases.

B1/B2 equivalence requires maximum normalized-fraction difference <=1e-6,
relative absolute-mass difference <=1e-5, relative pressure difference <=1e-6,
and final inventory-depletion difference <=1e-5. If passed, dense work uses B1
with B2 cross-checks at regime boundaries.

Finite-difference derivatives must agree across 0.5%, 1%, and 2% steps within
5% relative or 1e-8 absolute. Numerical Jacobian rank uses a derivative noise
floor equal to ten times the largest deterministic/resolution derivative
difference, never machine epsilon. A direction is resolved only when its
singular value exceeds that floor.

Practical scalar-inventory identifiability requires, separately for both
species: no M0-involving null direction; bounded nonlinear profile; <=10%
median and <=20% 95th-percentile synthetic M0 relative error; <10% boundary-hit
rate; and recovery error below the model-discrimination inventory-precision
limit. Seeded synthetic noise levels are 1%, 2%, and 5% relative.

The precision frontier evaluates 0.5%, 1%, 2%, 5%, 10%, and 20% inventory
uncertainty. A model comparison is informative only when the 95% inventory
interval occupies at most one-third of B0/B1 or B0/B2 separation in more than
half of independent condition/species/fraction blocks, neither species passes
fewer than half its blocks, and numerical uncertainty is at most one-tenth of
the claimed separation.

Pilot designs are selected target-blind by E-optimal scaled information and
direct seeded recovery. The minimum viable design is the least-resource design
meeting the frozen identifiability and precision rules; the robust design must
retain the decision after one lost replicate, one censored assay, or one failed
condition. Q is always an explicit unknown in I_ref bundles; Q=1 is prohibited.
