# SCI-MD-004 Stage C R1 recovery

This owner-authorized `GOVERNING_PHYSICS_CHANGE` recovery preserves the Stage C
R0 failure at commit `53ce8dbeb73d71da512bf368d8de0f7402348f9c`, closed
issue #90, and closed PR #91. R0 remains
`SCI_MD_004_STAGE_C_IMPLEMENTATION_VERIFICATION_FAILED`; its zero-diffusivity
mesh sequence does not qualify positive diffusion.

The required no-mutation V15 diagnostic used the archived base executable,
candidate legacy route, and candidate explicit indexed one-species route at
512x32, 1024x32, and 2048x32. At every mesh, the aggregate trace was
byte-identical among all three routes. The original 9.67% coarse/fine and
6.00% reference/fine sensitivity was reproduced in inlet back-diffusion mass.
It is inherited from the fixed-zero inlet concentration boundary and is not a
new indexed-species defect. Production solver source was not changed in R1.

V15B then exercised the frozen, fully wetted, no-flow, positive-diffusivity
two-species manufactured case at 64, 128, and 256 axial cells, the doubled
radial reference mesh, and timestep-halved reference and fine meshes. Direct
analytical errors were below their absolute mesh limits, analytical closure
was below `1e-10` relative, production conservation was below `1e-12 kg`, and
radial changes were below `1e-10` relative. The complete V15B subgate still
failed its mandatory convergence rules:

- remaining-mass error is controlled by temporal inventory integration and
  has no positive spatial order;
- species B maximum-concentration error increases slightly with refinement;
- timestep-halving changes several reported errors by far more than 10% of
  the already very small reference/fine spatial error difference.

These requirements were frozen before the series and were not relaxed after
inspection. V15B failure requires
`MATERIAL_POSITIVE_DIFFUSION_MESH_DEPENDENCE` under the owner authorization.
No adjudicative PASS matrix, performance acceptance, exact candidate freeze,
PR, independent review, or merge is eligible. The fail-closed primary result
is `SCI_MD_004_STAGE_C_R1_MATERIAL_POSITIVE_DIFFUSION_MESH_DEPENDENCE`.

Angeloni remains `PROTECTED_EXTERNAL_NO_RETUNING_ENDPOINT_HOLDOUT` with
`PREEXISTING_EXPOSURE = TRUE`. No target values were accessed; no holdout
prediction, score, fit, or post-holdout retuning event occurred. Physical
validation remains `NOT_ESTABLISHED`.

