# WP-0.3B non-protected extraction references

WP-0.3B independently re-expresses three public mathematical references and
adds explicit observable schemas. Moroney 2017 checks a flow-free,
three-inventory extraction limit by conservation and timestep refinement.
Matias 2023 checks a prescribed-transport kernel against its low- and
high-Peclet limits and front-gating trend. Liang 2021 checks the exact
`K`/`tau` rate transformation and synthetic transient identifiability without
opening or fitting the source figure.

The TDS, EY, and retained-liquid components are measurement bookkeeping.
They keep refractometric, gravimetric, oven-drying, and model-output meanings
distinct and expose every mass-balance correction. They are not extraction
physics.

Zero-flow extraction is deliberately separated from hydraulics so a later
extraction implementation can be checked without confusing pressure-flow
behavior with solute kinetics. Synthetic identifiability demonstrates only
what the frozen sampling and noise design can recover; it is not experimental
calibration.

Nothing here is connected to the OpenFOAM runtime or WP02. The references do
not establish parameter transfer, espresso extraction validity, multi-species
chemistry, or physical validation. Physical validation remains
`NOT_ESTABLISHED`.

## WP-0.3B-A1 governed amendment

The original canonical result remains a recorded failure: its endpoint-only
RK4 refinement ratio was saturated by binary64 roundoff. A1 replaces that
non-diagnostic observable—not its 0.35 threshold—with an aligned,
three-state trajectory norm and an explicit roundoff floor.

The publisher-literal equations 87–97 are preserved separately from a
`DERIVED_GOVERNING_ODE_CONSISTENT` second-order composite. The derived path
records the equation 46 and 80 sign findings, the equation 84/87 denominator,
the missing outer \(C_{h2}\), and the complete equation 95 common part. It is
not represented as an author correction. Author or publisher confirmation is
recommended before any claim about intended wording.

This commit freezes transcription, derivation, implementation, tests, and the
amended contract only. It contains no amended canonical result and authorizes
no OpenFOAM, Puckworks, protected-data, or WP02 execution.
