# SCI-MD-004 Stage E0 G1 parameterization and pre-holdout freeze

Governance class: **G1 — parameterization and pre-holdout freeze**.
Change declaration: **NO_GOVERNING_PHYSICS_CHANGE**.

This stage consumes the exact training and allowed input-side artifacts from
Puckworks merge commit
`5ce003e751aac516b5de3d9ede4e6910627e2b12`, tree
`d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`. The training-bundle manifest
SHA-256 remains
`112f8b3b943a5cea3399746fde512048e3898f99c8079433dae86bd142db8709`.

Exactly four values were fitted: `extractionRateConstant` and
`saturationConcentration` for caffeine and trigonelline. Beverage mass was
converted to elapsed time using the measured flow and the predeclared
1000 kg/m3 beverage-density operator. Fraction concentration was converted
from kg/kg beverage to kg/m3 on the same basis. The frozen reduced mapping is
`C_out(t) = C_sat exp(-k t)`; it is a training reduction of the already
accepted source law, not a validation claim.

Whole experiments, never individual fractions, are the cross-validation
blocks. Leave-one-experiment-out R2 is 0.631826 for caffeine and 0.600386 for
trigonelline, above the frozen 0.50 predictive-content floor. Both positive
parameters have positive 95% intervals; the maximum relative 95% half-widths
are 0.145897 and 0.170949, below the frozen 0.25 identifiability ceiling.
Fixed diffusivities come unchanged from the Pannusch scaling priors. Residual
extractables retain the exact legacy behavior and 0.28 total extractable
fraction.

Application timestep selection was checked against the exact integral of the
frozen smooth observation operator. Reference/fine differences are below
3.1e-7, against the 0.0025 ceiling. Spatial qualification is reused by hash
from the accepted Stage C separated-space/time evidence because the production
solver SHA-256 remains
`9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599`.
No species case was executed to obtain this freeze.

The 66 Angeloni input-side condition rows are frozen into 264 configurations:
H0 and H1 at reference and fine resolution for every row. Hydraulics use only
reported geometry, gauge pressure, temperature, dose, nominal beverage mass,
and duration. Outlet mass flow is conditional nominal yield divided by
reported duration. No permeability or pressure/response surface is fitted.
The cup observation operator is common to H0 and H1.

All configurations have status `FROZEN_NOT_EXECUTED`. Angeloni species
prediction count is zero, protected scorer invocation count is zero, and
protected targets were not part of the generator interface. The result is
ready for the single independent G1 pre-scoring audit. Physical validation
remains **NOT_ESTABLISHED**.
