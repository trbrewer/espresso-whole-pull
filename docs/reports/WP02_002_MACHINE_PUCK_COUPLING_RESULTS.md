# WP02-002 machine/puck coupling results

## Scope and equations

WP02-002 adds the disabled-by-default `lumpedMachineCompliance` boundary while
retaining `prescribedPressure` as the default regression control. All new
machine values are `SYNTHETIC_NUMERICAL_FIXTURE` or
`SYNTHETIC_ENGINEERING_DEMONSTRATION`; they are not measurements of a real
machine.

The upstream state obeys

`C_u dp_u/dt = Q_s(t,p_u) - Q_p(t,p_b)`,

with `Q_s = Q_free(t) max(0,1-(p_u-p_o)/(p_shut-p_o))` and
`p_b = p_u - R_u Q_p`. Backward Euler and a bounded bisection solve determine
the new upstream pressure. During wetting, the nested demand solve uses the
finite pore-volume increment `A phi (z[n+1]-z[n])/dt`. After saturation, the
exact series relation `Q_p = G(p_u-p_o)/(1+G R_u)` supplies the operating
point, and the OpenFOAM Darcy solve uses the resulting basket pressure.
Compliance storage `C_u(p_u-p_u0)` is reported separately.

## Numerical verification

The independent linear-load reference does not import production coupling
code. Production pressure agreed with the exact backward-Euler recurrence to
`1.02404e-12` relative, below the `1e-10` gate. Continuous-solution endpoint
errors for `dt = 0.04, 0.02, 0.01 s` were respectively 2038.1395, 1022.4427,
and 512.0695 Pa, giving observed orders 0.99523 and 0.99761. A production
limit sequence reduced the relative difference from a prescribed 900 kPa
step from 0.80408 to 0.01461 to 0.0014805.

The 131,072-cell prescribed-pressure R0 control reproduced first drip
`4.711696185 s`, final beverage `40.957867483 g`, TDS `11.689306389 %`, and
EY `23.938453103 %`. A separate 103 s WP02 coupling-disabled run completed
without protected analysis; its final trace remained numerically operational
with the prior closure and configuration.

## Executed synthetic shots

All full shots used `dt=0.02 s`, 131,072 cells, and 32 MPI ranks.

| case | C (m3/Pa) | R (Pa s/m3) | peak pu (kPa) | peak pb (kPa) | first drip (s) | cup (g) | TDS (%) | EY (%) | max machine balance (m3) | max coupling residual (m3/s) | runtime |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MC-0 | 0 | 0 | 900.000 | 900.000 | 4.71170 | 40.9579 | 11.6893 | 23.9385 | 0 | 0 | 5.24 s |
| MC-1 | 1e-13 | 0 | 894.598 | 894.598 | 3.70757 | 41.9114 | 11.5953 | 24.2988 | 1.35e-18 | 6.26e-18 | 5.57 s |
| MC-2 | 2e-11 | 2e11 | 961.516 | 845.274 | 8.90051 | 27.6357 | 13.7916 | 19.0570 | 1.55e-18 | 5.81e-18 | 30.56 s |
| MC-3 | 5e-12 | 2e11 | 961.671 | 861.545 | 6.82578 | 30.7593 | 13.4609 | 20.7024 | 6.36e-18 | 4.99e-18 | 14.99 s |
| MC-4 | 8e-11 | 2e11 | 858.220 | 645.529 | 14.14333 | 16.8182 | 14.6717 | 12.3376 | 2.23e-18 | 6.58e-18 | 27.01 s |
| MC-5 | 2e-11 | 2e11 | 1184.502 | 1179.204 | 8.90051 | 3.2150 | 15.7015 | 2.5240 | 8.20e-19 | 5.81e-18 | 35.03 s |

Peak resident memory was 64.8 MB or less for every full-shot launcher.
No coupled step failed, no bracket failed, and no prescribed-pressure fallback
occurred.

## Interpretation

Relative to MC-0, finite compliance and upstream resistance in MC-2 delayed
first drip by 4.19 s and reduced the 30 s beverage mass by 13.32 g. At first
drip MC-2 had 640.1 kPa basket pressure and stored 17.02 mL in the synthetic
compliant volume. Lower compliance (MC-3) shortened the delay; four-times
higher compliance (MC-4) delayed first drip to 14.14 s and left much more
water in upstream storage. The upstream-to-basket difference persisted after
saturation because the synthetic upstream resistance carried puck flow.

MC-5 demonstrates stable numerical composition with the existing WP02
permeability evolution. As that branch reduced puck conductance, machine
pressure moved toward synthetic shutoff while outlet production fell. This is
a mechanism-level numerical result, not evidence that a real pump or
headspace behaves this way.

Apparatus prediction would require independent measurements of the pump curve,
effective compliance, group resistance, pressure-node locations, and dynamic
instrument response. The work advances the whole-pull model by replacing an
optional prescribed inlet with an executable machine-storage/puck operating
point while keeping the prior boundary as a control.

`PHYSICAL_VALIDATION: NOT_ESTABLISHED`
