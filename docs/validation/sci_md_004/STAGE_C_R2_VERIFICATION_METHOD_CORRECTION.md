# SCI-MD-004 Stage C R2 verification-method correction

Stage C R0 remains `SCI_MD_004_STAGE_C_IMPLEMENTATION_VERIFICATION_FAILED`.
Stage C R1 remains
`SCI_MD_004_STAGE_C_R1_MATERIAL_POSITIVE_DIFFUSION_MESH_DEPENDENCE` under its
frozen v2 contract. Neither historical result is reclassified or passed by
R2. The owner separately adjudicated that R1 established no material solver
defect: V15A was byte-identical across legacy and indexed routes, and the R1
application sensitivity was the same inherited inlet-back-diffusion response
in every route.

R1 compared production output at a finite Euler timestep with a continuous-
time solution, then treated the resulting temporal truncation error as a
spatial error. In particular, the manufactured remaining inventory obeys the
spatially uniform production update

`M^(m+1) = (1 - k delta_t) M^m`,

not the continuous exponential at finite `delta_t`. Its leading global error
is first order in time and is mesh-independent. R1 also gated on the scalar
difference between numerical and analytical maxima. That scalar can exhibit
error cancellation even when the full pointwise profile converges.

R2 corrects the verification method without changing direct error limits. It
compares production at fixed timestep to an exact-discrete-time,
continuous-space oracle for spatial convergence. It separately compares that
oracle with the continuous-time eigenfunction solution for temporal
convergence. The pointwise spatial metric is the volume-aware profile
L-infinity norm; remaining mass is a spatial invariant. Scalar maximum-value
differences and ratios between differences of error magnitudes are diagnostic
only.

The discrete oracle implements both direct recurrence and closed form for
each mode. It independently evaluates cumulative inlet loss using a
beginning-of-step-source, implicit-Euler boundary-flux accumulation and mass
closure. Actual OpenFOAM cell centers and cell volumes are used. Modal tails
must have an estimated relative remainder no larger than `1.0e-10`.

The generated V15B schemes are frozen as Euler time discretization, Gauss
linear corrected Laplacian, Gauss linear gradient, linear interpolation, and
corrected surface-normal gradient. The manufactured saturation concentration
is `1.0e30 kg/m3`, with capacity ratio at most `1.0e-16`.

The complete branch is still a `GOVERNING_PHYSICS_CHANGE` relative to main,
but R2 is `NO_ADDITIONAL_PRODUCTION_SOLVER_CHANGE`. The production solver
source remains frozen at SHA-256
`9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599`.

Stage A is merged and unchanged. R0 and R1 are failed and preserved. R2 is the
active separated-space-time verification correction. No parameterization or
protected holdout scoring is authorized, and physical validation remains
`NOT_ESTABLISHED`.
