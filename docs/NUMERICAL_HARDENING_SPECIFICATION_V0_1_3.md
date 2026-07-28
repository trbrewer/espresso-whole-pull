# WP-0.1H numerical-hardening specification — v0.1.3

## Purpose

Version 0.1.3 converts the successful WP-0.1 implementation into a candidate frozen numerical reference. It does not expand the physical claim. It corrects known numerical/geometry biases, adds independent fixtures, and declares the qualification evidence required before the reference implementation is frozen.

## Controlling baseline

The successful v0.1.2 target execution completed under OpenFOAM Foundation 12 using 64 MPI ranks. It reached 30 s, reconstructed all written fields, passed all required numerical gates, and reported liquid and solute residuals near machine precision. Its run-status JSON is retained in:

```text
baseline_evidence/v0_1_2/ESPRESSO_WHOLE_PULL_RUN_STATUS_V0_1_2.json
```

The baseline is regression evidence, not a reason to preserve identified bias.

## Corrections

### Straight-sided wedge scale

For wedge angle `theta`, the block cross-section is triangular with area:

```text
A_wedge = R^2 sin(theta) / 2
```

The equivalent-cylinder multiplier is therefore:

```text
S = pi R^2 / A_wedge = 2*pi/sin(theta)
```

For the 5° case:

```text
S = 72.09146648398465
```

The solver computes raw mesh volume, scaled volume, nominal cylindrical volume, and relative error. A mismatch above `1e-8` is fatal.

### Exact wetting-pressure integration

The sharp-front closure is advanced from the exact integral:

```text
z_f(t_1)^2 = z_f(t_0)^2
             + 2*K_wet/(phi*mu)
               * integral[t_0,t_1] max(p_in(t)-p_front,0) dt
```

The imposed pressure is piecewise linear during the ramp and constant afterward. Breakthrough time within the crossing time step is found by bisection against the exact integral. The R0 analytical event is `4.71169618523187 s` and is independent of the selected time step to the frozen event tolerance.

## `./Allrun` required gates

`./Allrun` must complete all of the following:

1. static package validation;
2. Python unit tests;
3. timestamp normalization and clean Foundation-12 build;
4. build provenance capture;
5. layered-pressure fixture mesh and topology checks;
6. layered-pressure serial solve and exact discrete acceptance;
7. reference mesh and topology checks;
8. serial or MPI reference solve;
9. field reconstruction where applicable;
10. reference numerical acceptance and OpenFOAM/B0 parity;
11. run-status and timing artifact generation.

The reference run is not accepted merely because the solver reaches 30 s.

## Mandatory layered-pressure fixture

The fixture is initially saturated and contains two axial permeability layers:

```text
upstream K   = 0.75e-15 m2
 downstream K = 3.00e-15 m2
interface     = half bed depth
```

It uses a zero initial pressure field and fixed 9 bar/0 bar boundary nodes. It must:

- produce nonzero PCG iterations on at least one solve;
- match the exact discrete finite-volume flow within `1e-7` relative error;
- match two volume-weighted pressure probes within 5 Pa;
- pass the wedge-volume and liquid-balance gates.

The independent reference uses the same declared linear face-mobility interpolation as the orthogonal finite-volume discretization, but does not parse or reuse OpenFOAM field values.

## OpenFOAM/B0 parity

The standard-library B0 twin independently advances:

- exact sharp-front wetting;
- the declared one-dimensional Darcy flow;
- implicit upwind advection/diffusion;
- the effective extraction source;
- remaining-solid, dissolved, cup, and inlet-backdiffusion inventories.

Hydraulic/event quantities use tight analytical tolerances. Inventory outputs use a `0.5%` parity tolerance because OpenFOAM is radial-axisymmetric while B0 is a one-dimensional finite-volume twin. Agreement is code-verification evidence, not physical validation.

## `./Allverify` matrix

### Time-step subset

| Run | Mesh | dt | Ranks |
|---|---:|---:|---:|
| coarse temporal | 256 × 512 | 0.020 s | 32 |
| reference temporal | 256 × 512 | 0.010 s | 32 |
| fine temporal | 256 × 512 | 0.005 s | 32 |

Against `dt=0.005 s`, the `0.020 s` and `0.010 s` cases must remain within `0.5%` and `0.25%`, respectively, for declared primary outputs; first drip must remain within `1e-8 s`.

### Mesh subset

| Run | Mesh | dt | Ranks |
|---|---:|---:|---:|
| coarse | 128 × 256 | 0.010 s | 16 |
| reference | 256 × 512 | 0.010 s | 32 |
| fine | 512 × 1024 | 0.010 s | 64 |

Against the fine mesh, the coarse and reference meshes must remain within `2.0%` and `0.75%`, respectively, for the declared outputs; first drip remains analytically exact. The tolerances include the more mesh-sensitive retained dissolved inventory.

### Rank subset

The 256 × 512, `dt=0.010 s` case is run at 1, 16, 32, and 64 ranks. Parallel primary outputs must match the serial result within `1e-6` relative error, with first drip within `1e-10 s`.

### Layered parallel subset

The layered fixture is run at 1 and 16 ranks. Flow and pressure probes must agree within `1e-8` relative error.

## Freeze decision

The reference implementation may be marked `QUALIFIED` only when the standard `./Allverify` report passes. Until then, `./Allrun` acceptance reports state:

```text
reference_freeze_status: PENDING_FULL_ALLVERIFY
```

A qualified numerical implementation still retains:

```text
physical_validation_status: NOT_ESTABLISHED
```
