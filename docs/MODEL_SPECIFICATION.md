# WP-0.1 model specification — v0.1.4 frozen-candidate release

## Indexed passive-species extension

For each configured species, Stage C applies
`d(phi C_i)/dt + div(q C_i) - div(phi D_i grad(C_i)) = R_i`, where
`R_i = k_i M_i wetMask max(1-C_i/Csat_i,0)` and
`0 <= R_i <= M_i/delta_t`. Inventory updates as
`M_i(new)=max(M_i(old)-delta_t R_i,0)`. Filling retains the existing local
bulk-dissolved-mass rule independently for every species. Outlet advection,
inlet back diffusion, cup accumulation, and conservation accounting use the
unchanged legacy operators per species. A structural-balance species receives
the legacy extractable fraction not allocated to explicit species and inherits
the exact legacy scalar parameters.

## Release boundary

Version 0.1.4 contains the same governing model as the numerically qualified v0.1.3 release. Its changes are limited to freeze finalization, provenance, diagnostics, explicit acceptance gates, and the routine MPI default.

## Release invariance

The package verifies the OpenFOAM solver source and independent reduced mathematics against the bundled qualified v0.1.3 source contract after version-label normalization. Physical configuration projections, Make files, initial fields, and `fvSchemes`/`fvSolution` must also match. The routine default rank count and reporting/freeze machinery are not governing physics.

## Geometry

The reference mesh is a straight-sided 5° one-cell-thick axisymmetric wedge. The axial coordinate runs from bed top (`inlet`) to basket bottom (`outlet`). Basket radius is 29 mm. Bed depth is derived from:

```text
H = dose / [particle solid density * (1-porosity) * circular area]
```

Using 20 g, 1400 kg/m³, and porosity 0.40 gives:

```text
H = 0.009011660896432553 m
```

This assumes a dry bulk density of `1400*(1-0.40) = 840 kg/m³`;
it is not a measured depth or bulk density of the R0 coffee. Skeletal density,
particle-envelope density and bulk density have different volume bases.
Intraparticle voids cannot be added to the single R0 porosity while also
treating that porosity as interparticle hydraulic space without a new storage
contract. A depth-only sensitivity at fixed porosity is consequently a
diagnostic scenario, not a source-qualified replacement material.

The native initial soluble inventory is `dryDose*extractableFraction`, divided
by the actual full mesh volume to initialize `remainingExtractable` in kg/m³
of bed. Changing depth at fixed dose therefore changes inventory concentration,
as well as `phi*A*H` water storage and `A*k/(mu*H)` saturated conductance.
Scaling permeability with depth preserves that conductance algebraically;
it is not an independent calibration or validation.

The exact full-cylinder multiplier for the straight-sided block is:

```text
sectorScale = 2*pi/sin(wedgeAngle)
```

For 5° this is `72.09146648398465`. The scaled mesh volume must match `pi*R²*H` within `1e-8` relative error.

## Wetting and storage

The sharp wetting front obeys:

```text
d(z_f²)/dt = 2*K_wet*max(p_in(t)-p_front,0)/(phi*mu)
```

The positive piecewise-linear pressure history is integrated exactly within every time step, and a sub-step crossing solve identifies breakthrough. The saturation display field uses a one-cell smoothing transition before breakthrough; after breakthrough the bed is saturated.

Before first drip, outlet flow is zero and admitted water is stored in the wetted pore volume. This is a declared sharp-front closure, not a resolved two-phase air–water model.

## Saturated flow

After breakthrough:

```text
div[(K/mu) grad(p)] = 0
u = -(K/mu) grad(p)
```

The inlet is bed-top gauge pressure and the outlet is basket-bottom ambient gauge pressure. The matrix flux is used for inlet/outlet accounting.

The R0 case uses uniform permeability. The solver also supports an `axial_two_layer` permeability profile for numerical verification. The mandatory layered fixture requires a nonzero pressure iteration count and compares outlet flow and two internal pressure probes with an independent discrete finite-volume reference.

## Solute transport and extraction

The effective-solute equation is:

```text
phi*d(c)/dt + div(q*c) - div(phi*D_eff*grad(c)) = R_ext
```

with:

```text
R_ext = k_ext*m_s*wetMask*max(1-c/c_sat,0)
d(m_s)/dt = -R_ext
```

During filling, dissolved bulk mass is conserved as the wetted volume increases. After breakthrough, the finite-volume transport equation advances solute through the saturated bed. Inlet diffusive back-loss is accumulated explicitly.

`m_s` is remaining soluble mass per bulk cell volume, `c` is mass per liquid
volume, and `R_ext` is mass per bulk volume per second. Each scalar or indexed
source uses the beginning-of-step inventory and concentration, the current
wet mask, and an inventory cap `R_ext <= m_s/delta_t`. The concentration
factor suppresses release when `c >= c_sat`; it does not project the solved
concentration onto `c <= c_sat`. Negative concentrations are clipped after
the transport solve. Boundedness and conservation must therefore be checked
for the actual scenario and timestep; a successful R0 capacity check is not
a global discrete maximum principle.

For example, a fully saturated, closed, zero-diffusion R0-volume cell starts
with `m_s=235.2 kg/m³` of bed and `c=0`. A deliberately coarse 5 s step at
`k_ext=0.15 s^-1` releases `176.4 kg/m³` of bed, yielding
`c=176.4/0.4=441 kg/m³`. The following step suppresses further release.
This diagnostic conserves soluble mass while exceeding `c_sat=180 kg/m³`;
it is not an admissible R0 timestep or a proposed parameter change.

## Cup and inventory accounting

At every step:

```text
initial stored water + cumulative inlet water
= current stored water + cup water + liquid residual
```

and:

```text
initial extractable solid
= remaining solid + dissolved in puck + exported to cup
  + inlet backdiffusion + solute residual
```

Cup beverage mass is cup water plus cup solute. TDS and extraction yield are calculated from the cup and initial dose inventories. Retained water and dissolved solute remain separate outputs.

The frozen R0 30 s endpoint is 40.957867483 g beverage, 23.938453103% EY and
11.689306389% TDS. At the distinct 40 g beverage event, linear interpolation
of native accumulated masses gives 29.374480171 s, 23.624029229% EY and
11.812014614% TDS. Interpolation is exact for the solver's constant per-step
cup increments; continuum timestep error remains separate. A scenario that
has not crossed 40 g by its end time has no 40 g event result.

## Primary fields

```text
p
U
darcyFlux
saturation
wetMask
porosity
permeability
hydraulicMobility
dissolvedConcentration
remainingExtractable
localExtractionRate
```

## Reference configuration

```text
basket diameter                58 mm
dry dose                       20 g
initial porosity               0.40
fixed temperature              93 °C
bed-top pressure ramp          0 to 9 bar gauge in 3 s
end time                       30 s
reference mesh                 256 axial x 512 radial x 1 wedge
reference time step            0.020 s
routine MPI default            32 ranks
saturated permeability         1.77e-15 m²
wetting permeability           1.77e-15 m²
extraction rate constant       0.15 s⁻¹
concentration capacity         180 kg/m³
```

Permeability remains the declared R0 hydraulic calibration scale. The extraction rate and capacity remain WP-0.1 engineering assumptions.

## Verification hierarchy

1. closed-form first drip, Darcy flow, cylinder volume, and pore water;
2. discrete layered-pressure finite-volume reference;
3. independent B0 one-dimensional reduced twin;
4. OpenFOAM mesh, solver, boundedness, conservation, and field gates;
5. standard time-step, mesh, and MPI-rank qualification;
6. immutable source, executable, artifact, acceptance, and field-file binding.

These layers establish code verification and numerical qualification. They do not establish independent physical validation.
