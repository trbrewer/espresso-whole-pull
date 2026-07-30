# WP02-004 Static Radial Heterogeneity Results

## Disposition and physics

`SOLVER_BEARING_WORK_PACKAGE_COMPLETE_PR_OPEN`.

The optional `radial_two_zone` profile classifies cells and outlet faces by
`sqrt(y^2+z^2) < interfaceRadiusM` (inner; equality is outer). It is active
only after saturation. The existing scalar sharp-front wetting branch,
transition treatment, and first-drip event remain unchanged.

Each saturated zone is an exact parallel hydraulic path. Darcy paths use
`R_D=mu L/(A k)`; Darcy–Forchheimer paths additionally use
`R_I=rho L/(A^2 k_I)` and the stable positive root. The machine solver nests a
bracketed basket-pressure root inside the existing bracketed upstream
compliance root. The OpenFOAM pressure equation independently solves the
cell-valued heterogeneous mobility. Zone water, solute, remaining
extractable material, retained liquid, concentration, and extraction are
integrated from face and cell fields.

The principal profiles use `r_i/R=0.5`, hence area fractions 0.25/0.75.
Contrasts 4 and 16 were constructed before execution so
`0.25 k_inner + 0.75 k_outer = k0`. They are
`SYNTHETIC_ENGINEERING_DEMONSTRATION`, not measured puck profiles.

## Verification

Foundation OpenFOAM 12 built and executed the solver. Executable SHA-256:
`6b2844328d33a630499d72fa00c7207025f73313a05779221a147483eb889200`.

| Gate quantity | Maximum error/result |
|---|---:|
| predecessor regression | `5.57e-11` |
| equal-zone identity | `0` |
| Darcy zone/total reference | `2.40e-12` |
| Forchheimer zone/total reference | `1.82e-11` |
| production machine reference | `1.43e-16` |
| matched conductance | `1.11e-16` |
| matched total flow | `6.71e-15` |
| machine matched hydraulics | `4.78e-13` |
| zone liquid/solute conservation | `8.54e-15` |
| wetting isolation | `0` |
| maximum radial/axial velocity ratio | `7.40e-10` |
| total machine/field mismatch | `1.30e-11` |
| zone machine/field mismatch | `1.99e-10` |
| fine timestep change | `4.19e-4` |
| fine radial-mesh change | `3.69e-4` |
| maximum water residual | `1.92e-14 kg` |
| maximum solute residual | `1.13e-11 kg` |
| nonlinear failures / bracket failures / fallbacks | `0 / 0 / 0` |

The radial meshes used 256, 512, and 1024 radial cells with 256 axial cells
(131,072; 262,144; and 524,288 total cells) on 32 MPI ranks. The first
preflight was stopped when an arithmetic error in the not-yet-executed
matched-profile table failed the area-weighted identity; formula-derived
values were corrected and the run specification was rehashed before the
governed matrix was restarted. No result-dependent tuning or tolerance change
occurred.

## Full-shot results

All cases used 32 MPI ranks and `dt=0.02 s`.

| Case | pressure / flow / profile | high zone, contrast | mean flow (mL/s) | inner / outer flow | M_Q / A_eff | first drip (s) | cup (g) | TDS | EY | inner / outer extraction | M_E | runtime / RSS |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RH-0 | prescribed / Darcy / uniform | — | 1.48268 | .250 / .750 | 0 / 1.000 | 4.71170 | 40.9579 | 11.689% | 23.938% | — | — | 5.46 s / 66,904 kB |
| RH-1 | prescribed / Darcy / equal radial | none, 1 | 1.48268 | .250 / .750 | 0 / 1.000 | 4.71170 | 40.9579 | 11.689% | 23.938% | .889 / .889 | 0 | 5.07 s / 66,848 kB |
| RH-2 | prescribed / Darcy / radial | core, 4 | 1.48268 | .571 / .429 | .321 / .645 | 4.71170 | 40.1289 | 9.865% | 19.793% | .960 / .728 | .055 | 4.97 s / 66,824 kB |
| RH-3 | prescribed / Darcy / radial | annulus, 4 | 1.48268 | .077 / .923 | .173 / .862 | 4.71170 | 40.4276 | 10.531% | 21.287% | .539 / .920 | .087 | 5.00 s / 66,944 kB |
| RH-4 | prescribed / Darcy / radial | core, 16 | 1.48268 | .842 / .158 | .592 / .348 | 4.71170 | 38.5133 | 6.084% | 11.715% | .969 / .464 | .161 | 5.28 s / 66,868 kB |
| RH-5 | machine / Darcy / uniform | — | 1.17118 | .250 / .750 | 0 / 1.000 | 8.90055 | 27.6357 | 13.792% | 19.057% | — | — | 30.61 s / 66,884 kB |
| RH-6 | machine / Darcy / radial | core, 4 | 1.17118 | .571 / .429 | .321 / .645 | 8.90055 | 26.8534 | 11.280% | 15.145% | .913 / .584 | .093 | 31.76 s / 66,860 kB |
| RH-7 | machine / Darcy / radial | annulus, 4 | 1.17118 | .077 / .923 | .173 / .862 | 8.90055 | 27.3449 | 12.875% | 17.603% | .455 / .818 | .094 | 31.23 s / 66,904 kB |
| RH-8 | machine / Forchheimer / radial | core, 4 | .80263 | .586 / .414 | .336 / .624 | 8.90055 | 18.6698 | 12.547% | 11.713% | .871 / .488 | .123 | 65.28 s / 66,932 kB |

## Interpretation

Matched Darcy conductance preserves the total water-flow and, under machine
coupling, the upstream-pressure, basket-pressure, compliance-storage, and
total-flow trajectories to numerical precision. It does not preserve spatial
extraction. In RH-6, 25% of the puck area carries 57.1% of flow
(`F_inner=2.286`), while the outer 75% carries 42.9%
(`F_outer=0.571`). Effective hydraulic area falls to 64.5%.

Placement matters. A 4:1 high core produces more hydraulic maldistribution
than a 4:1 high annulus because the small core must carry a disproportionate
share. The annular case nevertheless leaves the low-flow core much less
extracted. At 16:1 core contrast, 84.2% of flow traverses 25% of area and
effective hydraulic area falls to 34.8%; outer extraction is only 46.4%.
Thus nearly identical total cup-water trajectories conceal large differences
in local depletion, TDS, and aggregate extraction yield.

The high-flow zone depletes first. Low-flow zones retain substantially more
extractable material at 30 s. This agrees qualitatively with the locked
Puckworks static-streamtube mechanism expectation: mean-preserving parallel
heterogeneity can leave bulk flow nearly unchanged while lowering finite-time
aggregate extraction. It is a `CROSS_MODEL_MECHANISM_COMPARISON`, not
equivalence or validation. OpenFOAM additionally contains explicit spatial
advection/diffusion, radial solute exchange, finite shot duration, and machine
compliance.

Wadsworth resistance reduces total flow and slightly amplifies the core flow
share (57.1% to 58.6%) for this synthetic profile; it is not a matched
nonlinear-resistance case. Computed radial velocities are below
`7.40e-10` of axial velocity and are numerical noise, not physical lateral
flow. No result demonstrates dynamic channel growth or a validated channel.

Physical identification would require spatially resolved basket-exit flow,
upstream and basket pressure, segmented beverage concentration, post-shot
spatial solubles, imaging or tomography, local permeability measurements, and
repeated-shot variability. None was acquired here.

## Claim boundary

```text
PHYSICAL_VALIDATION: NOT_ESTABLISHED
EXPERIMENTAL_COMMISSIONING: NOT_AUTHORIZED
HOLDOUT_ACQUISITION: NOT_PERFORMED
PROTECTED_SCORING: NOT_PERFORMED
RESULT_CLASS:
  NUMERICAL_VERIFICATION_AND_SYNTHETIC_SPATIAL_HETEROGENEITY_DIAGNOSTIC
```
