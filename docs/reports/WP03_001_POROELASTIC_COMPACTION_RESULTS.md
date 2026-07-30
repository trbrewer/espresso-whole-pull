# WP03-001 — Saturated quasi-static poroelastic compaction

## Disposition

`SOLVER_BEARING_WORK_PACKAGE_COMPLETE_PR_OPEN`

This work is numerical verification and a source-linked/synthetic mechanism
diagnostic. It is not physical validation.

## Model and boundary

After saturation, the implementation uses

\[
\sigma=p_b-p,\quad e=\Phi\sigma/P_c,\quad
\phi_m=(\Phi-e)/(1-e),\quad
k=k_0(1-\sigma/P_c)^3/(1-\Phi\sigma/P_c).
\]

The finite-volume pressure equation uses this permeability field directly.
An exact constitutive secant mobility is evaluated at each face, followed by a
bounded Picard solve and reconstruction of `U` and `darcyFlux`. The machine
branch solves independently bracketed upstream and basket roots using the exact
finite-porosity puck demand. The wetting branch is unchanged and compaction is
inactive until the puck is saturated at timestep start.

`mechanicalPorosity` is deliberately separate from transport `porosity`.
Predicted bed height and mechanical pore-volume change are fixed-reference-mesh
diagnostics; neither changes storage, the liquid balance, transport capacity,
or mesh geometry.

## Verification

OpenFOAM Foundation 12 built executable
`0b9a8dd28aae6a2853e287a590162b0088116be9268a6012c037bada9699549c`.
Every fail-closed result gate passed.

- Production scalar flow error: 0.
- Maximum production/reference compaction-strain error: 0.
- Maximum production/reference mechanical-porosity error:
  \(9.99\times10^{-16}\).
- Maximum production/reference permeability-ratio error:
  \(2.71\times10^{-15}\).
- R0, WP02-001, WP02-002 MC-2, WP02-003, and WP02-004 numerical predecessor
  errors: 0, \(1.18\times10^{-16}\), 0, \(6.57\times10^{-13}\), and 0.
- Maximum 5/9/11-bar OpenFOAM flow error: \(8.99\times10^{-11}\).
- Maximum pressure-probe error: \(2.66\times10^{-11}\).
- Maximum porosity/permeability error: \(3.11\times10^{-15}\).
- Maximum bed-height-ratio error: \(3.34\times10^{-8}\).
- Rigid-bed limit error: \(5.85\times10^{-9}\).
- Analytical 9-bar match error: \(1.36\times10^{-16}\).
- OpenFOAM 9-bar match error: \(1.71\times10^{-13}\).
- Machine reference error: \(6.23\times10^{-13}\).
- Maximum machine/field mismatch: 0.
- Wetting/first-drip isolation error: 0 s.
- Fine timestep change: 0.0004194.
- Fine axial-mesh change: 0.0005922.
- Maximum water-balance residual: \(3.28\times10^{-14}\) kg.
- Maximum solute-balance residual: \(3.96\times10^{-13}\) kg.
- Failed nonlinear timesteps, critical-stress violations, bracket failures,
  and fallbacks: 0.

The finite-\(\Phi\) universal-limit errors for \(\Phi=10^{-2},10^{-4},10^{-8}\)
were respectively 0.0005260, \(5.25\times10^{-6}\), and
\(5.25\times10^{-10}\), decreasing monotonically.

## Full-shot results

All flows are post-saturation means. TDS and EY are mass fractions.

| Case | Construction | Pressure | Flow (mL/s) | min \(\phi_m\) | min \(k/k_0\) | \(h/h_0\) | First drip (s) | Cup (g) | TDS | EY | Runtime | Peak RSS (kB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PE-0 | R0 Darcy | 9 bar | 1.48268 | 0.4000 | 1.0000 | 1.0000 | 4.71170 | 40.9579 | 0.11689 | 0.23938 | 5.39 s | 67036 |
| PE-1 | rigid limit | 9 bar | 1.48268 | 0.4000 | 1.0000 | 1.0000 | 4.71170 | 40.9579 | 0.11689 | 0.23938 | 15.64 s | 66868 |
| PE-2 | direct R0 \(k\) as stress-free | 9 bar | 0.55363 | 0.1543 | 0.02890 | 0.91666 | 4.71170 | 15.8475 | 0.14776 | 0.11708 | 21.25 s | 66904 |
| PE-3 | analytically matched | 9 bar | 1.48268 | 0.1543 | 0.02890 | 0.91666 | 4.71170 | 40.9579 | 0.11689 | 0.23938 | 21.19 s | 67856 |
| PE-4 | matched transfer | 5 bar | 1.27449 | 0.2845 | 0.25309 | 0.93664 | 7.28105 | 32.1728 | 0.13224 | 0.21273 | 17.03 s | 67960 |
| PE-5 | matched transfer | 11 bar | 1.49350 | 0.06965 | 0.002196 | 0.91502 | 4.12775 | 42.1133 | 0.11500 | 0.24216 | 21.03 s | 67812 |
| PE-6 | machine Darcy | coupled | 1.17118 | 0.4000 | 1.0000 | 1.0000 | 8.90055 | 27.6357 | 0.13792 | 0.19057 | 52.65 s | 67816 |
| PE-7 | machine compaction | coupled | 1.38896 | 0.2433 | 0.14148 | 0.92634 | 8.90055 | 32.4557 | 0.12944 | 0.21006 | 31.93 s | 66892 |

## Source reconstruction

The locked calibration was reconstructed without refitting:

- \(P_c=12.39155\) bar;
- \(Q_c=1.8969919955\) g/s;
- \(\Phi=2.257/18.5=0.122\);
- radius 0.028 m, reference depth 0.01 m;
- viscosity \(3.15\times10^{-4}\) Pa s and declared density 965 kg/m³;
- derived \(k_0=7.9141396927\times10^{-15}\) m².

Ten source pressure points strictly below \(P_c\) were executed. Maximum
OpenFOAM versus exact finite-\(\Phi\) flow error was
\(7.98\times10^{-11}\). The 13-bar nominal endpoint has basket pressure equal
to \(P_c\), is retained as context, and is classified
`OUTSIDE_LOCAL_CONSTITUTIVE_DOMAIN`; it was not executed. Residuals to measured
source flow are post-fit reconstruction context, not independent validation.
The largest finite-\(\Phi\) versus source universal-curve difference occurs at
the lowest retained pressure (about 2.13%) and falls below 0.006% near 10.4 bar.

The retained source sweep reproduces the pinned Puckworks last-timepoint
curve. The source paper describes equilibrium flow using a final-ten-second
average, so this is a pinned-model reconstruction rather than an exact
recreation of that averaging operation.

## Interpretation

Compaction concentrates at the outlet, where matrix stress is greatest. At the
matched 9-bar endpoint the outlet permeability falls to 2.89% of stress-free
permeability even though the integrated flow is identical to R0 by analytical
construction. Reusing the R0 effective permeability as \(k_0\) instead reduces
mean saturated flow by about 63%, cup mass by about 61%, and EY by about 51%;
this is a compatibility warning, not improved prediction.

The 9-bar normalization does not transfer linearly. At 5 bar the matched branch
has much less compaction and a different hydraulic/cup endpoint; at 11 bar the
outlet approaches the constitutive limit (\(k/k_0\approx0.00220\)) while total
flow shows pressure-flow saturation. The near-critical case remained bounded
but required declared 0.7 Picard relaxation.

Machine compliance changes the operating point materially. Relative to the
machine Darcy control, PE-7 has higher post-saturation flow and cup mass because
the matched stress-free permeability is larger and the coupled basket pressure
does not reproduce the 9-bar normalization point. TDS decreases while EY
increases through the changed water/advection history. This is a synthetic
composition result, not calibration.

Before coupling mechanical porosity to storage, the model would need a
mechanically consistent transient liquid balance, deformation/mesh or
reference-volume mapping, solid velocity, loading history, and independent
measurements of pressure-flow response, wet-puck modulus, puck-height change,
depth-resolved porosity/permeability, hysteresis, repeated cycling, and imaging
under pressure.

## Claim boundary

    PHYSICAL_VALIDATION: NOT_ESTABLISHED
    EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
    HOLDOUT_ACQUISITION: NOT_PERFORMED
    PROTECTED_SCORING: NOT_PERFORMED
    RESULT_CLASS:
      NUMERICAL_VERIFICATION_AND_SOURCE_LINKED_QUASISTATIC_COMPACTION_DIAGNOSTIC
