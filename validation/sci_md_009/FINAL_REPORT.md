# SCI-MD-009 final report

## Question, authority, and target blindness

This study asks whether one scalar effective initial inventory per species can
make the frozen production chemistry model testable and which smallest paired
pilot supplies the required observables. It is target-blind frozen-physics
sensitivity, identifiability, and design evidence—not fitting or validation.

Executable authority is espresso-whole-pull commit
`c33422204962e693d6410eae9024a79ddd776f94`, tree
`394b34ce13433e542d4c83d3b3ab8b50c4ccedbe`. Puckworks authority is commit
`5ce003e751aac516b5de3d9ede4e6910627e2b12`, tree
`d50c23028df01d6e1dc0a14ab331d0ea7453cb7f`; exact hashes are in
`INPUT_AND_PARAMETER_AUTHORITY.json`.

Frozen caffeine parameters are k=0.04423709010294066 s-1,
Csat=6.514777241461055 kg m-3, D=1e-10 m2 s-1. Trigonelline uses
k=0.0623465636881358 s-1, Csat=3.8839985660202996 kg m-3, and
D=9.687426142431468e-11 m2 s-1. Schmieder asymptotic inventories only center
dimensionless scales; they are training-derived estimates, not measurements.

The loader projected only experiment, replicate, temperature, flow, grind, and
fraction boundaries. It loaded no observed chemistry, generated no target
residual or score, and did not access Angeloni. `TARGET_BLINDNESS.json` binds
the whitelist and sanitized-artifact hashes.

## Implemented law, runs, and regimes

First-order solid release is capped by local liquid concentration capacity.
Inventory scale cancels from normalized output only in the dilute linear limit.
As C/Csat grows, the cap changes fraction shape; inventory depletion separately
truncates late fractions. These are algebraic and numerical properties of the
implementation, not physically validated coffee behavior.

All 498 scheduled production cases passed (500 hard cap). Tested ranges were
Lambda_full=0.0289–9.256 caffeine and 0.0242–7.368 trigonelline;
Da_shot=0.936–2.496 and 1.320–3.518; Pe=1.69e5–5.24e5. Maximum fraction-average
C/Csat ranged about 0.0045–0.83, spanning dilute, capacity-transition, and
capacity-influenced/depletion regimes.

B1/B2 chemistry was numerically indistinguishable: normalized fractions
differed at most 3.65e-14 and absolute mass at most 1.02e-13 relative. Required
pressure differed 24.6484%, so the joint equivalence gate failed and B2 was
retained through core M0/k sensitivities at every envelope plus Csat/D regime
cross-checks. Chemistry equivalence does not validate hydraulics.

## Sensitivity and identifiability

Caffeine M0 elasticities ranged 0.501–1.337 (median 0.769); trigonelline ranged
0.496–1.706 (median 0.807). k and Csat effects changed sign across fractions. D
elasticities were at most 1.73e-5 and were not promoted into the joint vector.

Combined [log(M0), log(k), log(Csat)] Jacobians had rank 3 above solver-derived
noise for both species. Condition numbers were 9.92 caffeine and 8.91
trigonelline; k/Csat correlations were 0.746 and 0.843. Seeded recovery gave
median M0 errors 0.4435% and 0.3085%, 95th percentiles 2.3266% and 1.4944%, and
no boundary hits. Scalar M0 is sufficient for the frozen model's scaling; this
does not prove real coffee has only one accessibility state.

O0 normalized shape is insufficient. O1/O2 absolute timed fraction masses make
the frozen-model parameters locally separable; O3 supplies M0 directly. O4
leaves accessibility unknown. O5 introduces an indispensable Q_s. O6/O7 are
strongest because paired initial/spent I_ref and absolute fractions expose the
mass-balance bridge. Q_s is species-specific and never fixed to one.

## Precision, pilot, and SCI-ED-002

B0/B1 shape-separation norms were 0.1381–0.3043; B1/B2 chemistry separation was
only 2.81e-14–5.55e-14. Under the frozen rule, all tested 0.5%–20% M0 uncertainty
levels retained a majority of B0/B1 blocks for both species. The tested maximum
permissible relative standard uncertainty is therefore 20%. No feasible
precision distinguishes B1 from B2 chemically; their difference is hydraulic.

The minimum O6 pilot is one homogenized lot, low/high flow, four replicates per
condition, six mass-defined fractions, paired initial/spent I_ref, absolute
caffeine/trigonelline fraction masses, endpoints, and telemetry: 8 shots, 96
species-fraction assays, 4 initial preparations, 8 spent preparations, and 60
chromatography injections. Robust O7 uses three flows and five replicates: 15
shots, 180 species-fraction assays, 5 initial and 15 spent preparations, and
110 injections. One condition, fewer than four replicates, fewer than six
fractions, or no spent-puck pairing is nonviable.

SCI-ED-002 requires a measured unobserved-tail bound below 6.7% of I_ref and
expanded inventory uncertainty no greater than 20%. The proposed stopping rule
remains unvalidated. Revisit requires real sequential-cycle data from at least
four preparations per species. Until then:
`EMPIRICAL_REFERENCE_EXTRACTION_TAIL_DATA_REQUIRED`.

## Disposition and claim ceiling

`SCI_MD_009_REFERENCE_TO_PRODUCTION_INVENTORY_BRIDGE_MUST_BE_MEASURED`

The frozen model is practically testable with paired absolute fractions and
inventory evidence, but I_ref cannot be used directly as M0. No physics or
parameter changed; no predictor or c_s0 mapping is authorized. Physical
validation remains `NOT_ESTABLISHED`. The strongest next action, if separately
authorized, is the minimum paired O6 mass-balance pilot.
