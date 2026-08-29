# SCI-MD-008 final report

The question was whether the frozen SCI-MD-004 caffeine and trigonelline
parameters, when used in the production PDE with measured flow and exact
mass-defined observation, add explanatory value over the reduced model. The
evidence is source-dependent reconstruction evidence, not validation.

Authority is espresso-whole-pull commit
`3874865e124dba0340ca93626b9bbf80f1385664`, tree
`b9ace201b4bbcda9fad5631faeaca1f811cb6a2b`, and Puckworks scientific commit
`5ce003e751aac516b5de3d9ede4e6910627e2b12`, tree
`d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`. Exact source and parameter hashes
are in `SOURCE_AND_PARAMETER_AUTHORITY.json`. The frozen parameters are
caffeine k=0.04423709010294066 1/s, Csat=6.514777241461055 kg/m3,
D=1e-10 m2/s; trigonelline k=0.0623465636881358 1/s,
Csat=3.8839985660202996 kg/m3, D=9.687426142431468e-11 m2/s. No fitting occurred.

The accepted source contains 15 experiments, 48 replicate shots, and six
measured fraction indices per species. Constant measured full-basket flow is
mapped directly to XSV-FLOW-001. The union of exact reported lower/upper mass
boundaries is mapped to XSV-FRAC-001; reported gaps remain gaps.

The inventory gate executed 18 production cases: low, middle, and high flow;
B1 and B2; and 0.01x, 0.1x, and 1x inventory. Both species were solved together.
All retained prescribed-flow runtime gates passed and pressure was invariant
to inventory scale. Fraction shape was not invariant: the maximum absolute
normalized-vector difference was 0.08011412483893848 against 1e-6. Absolute
extracted mass also failed simple proportional scaling (see CSV).

Disposition:
`SCI_MD_008_STOP_FRACTION_OUTPUT_REMAINS_INVENTORY_SCALE_DEPENDENT`.

Consequently numerical convergence qualification, the 48-condition B0/B1/B2
matrix, caffeine and trigonelline reconstruction scores, paired incremental
value, and the primary hydraulic comparison were not adjudicated. Their tables
contain explicit BLOCKED rows; none were silently omitted. This does not
validate the solver, predict flow, validate hydraulics, predict inventory,
establish transfer, repair prior tasks, or raise physical validation above
`NOT_ESTABLISHED`.

The strongest next action is direct source-condition inventory measurement (or
an independently justified fixed inventory authority) before another
fraction-trajectory comparison; descriptor prediction is not authorized.

