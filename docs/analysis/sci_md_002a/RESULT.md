# SCI-MD-002A reduced transient-poromechanics result

## Disposition

`SCI_MD_002A_REJECTED_WRONG_PRESSURE_ORDERING`

All 35 shared finite-rate constitutive sets increased apparent resistance in the required pressure direction and stayed within the frozen source-screen state bounds. None reproduced the retained terminal source flow ordering `Q5 > Q9 > Q11`; every set retained increasing terminal flow with pressure. Gate 2 therefore rejects this single-mode reversible consolidation family before aggregate-error ranking.

This is a post-observation reduced mechanism screen, not physical validation and not a production-physics result.

## Authority and lane isolation

- Starting `origin/main`: `3e8993f56badd575f3482ea7bfa0f87d24412100`; tree `ba7256d8d5813c87c72a3f896c0ac5f51cd06ee0`.
- Exact execution source: `dce4b6f2941bc379bac6acf377ffcc29c017e12f`; tree `bf310b624788de33e315b65d0c57b64c52efd47c`.
- Protocol SHA-256: `7290acd0e753a2786b48a07513f9d3d03a47034a72007b4ac8f65661a74619fa`.
- Matrix SHA-256: `b2aa5ab159bb36e802968b8ba26c54b295a6eca80f66951777efcc1a408e7e41`.
- Implementation SHA-256: `faf038627f79675299de26ef90d188174086ab56666fc2577eda4a9ca9d3af07`.
- Source-overlay SHA-256: `e69d2b7b0f0ee6945013a0b185da21803d404270a34f1c9d26aed6ecda370c0e`.
- External authority is represented as `SCI_MD_002A_EXTERNAL_BUNDLE/attempt4/adjudicative`; no absolute path is tracked.
- Issue #72 and draft PR #73 are task-owned. SCI-LC-001A issue #70, PR #71, branch, worktree, source files, and artifacts were read-only.

Two earlier external attempts are retained as diagnostic-only: attempt 1 exposed a Gate-1/2 reducer classification defect; attempts 2 and 3 exposed small-load cancellation in unload bed-height reporting. Neither contributes to the final disposition. The complete matrix was rerun from a fresh authority after each code correction.

## Model and mapping

The single state is load-equivalent consolidation pressure:

`tau_c d sigma_c/dt = (p_basket - p_outlet) - sigma_c`.

The accepted WP03 finite-porosity scalar integral is evaluated at `sigma_c`. Its depth-resolved effective-stress mapping supplies the secant puck conductance and bulk bed-height ratio; mechanical porosity and permeability use the same solid-volume-compatible and permeability closures. Backward Euler advances the reversible state. The fixed and quasi-static models are exact structural limits. The machine arm reuses `C_u dp_u/dt = Q_supply - Q_puck` and `p_b = p_u - R_line Q_puck` with the governed WP02 reference tuple.

The primary boundary is measured basket-top gauge pressure relative to ambient basket-bottom pressure. `pc=1,239,155 Pa` is source-derived from the existing closure. Other pressure scales and all consolidation times are `SYNTHETIC_SCREEN_BOUND`, `NOT_EWP_MEASURED`. No modulus is inferred as measured.

## Matrix and execution

The deterministic 580-row matrix contained:

| Arm | Trajectories |
|---|---:|
| analytical controls | 5 |
| equilibrium pressure screen | 15 |
| synthetic transient signatures | 175 |
| prescribed source pressure screen | 105 |
| machine transfer | 105 |
| generic relaxing-resistance control | 105 |
| unload measurement design | 70 |

Totals by evidence role are 210 source-conditioned, 245 synthetic signature, and 125 control trajectories. Grind/brew-ratio transfer was not executed because the governed corpus does not provide an admissible grind-to-initial-structure mapping; its disposition is `GRIND_DISCRIMINATION_ADDITIONAL_DATA_REQUIRED`.

### S2 machine-arm qualification

The executed S2 arm used one fixed governed machine parameter tuple. Its pressure-group labels did not define three independently specified 5-, 9-, and 11-bar machine programs. S2 is therefore a fixed-machine descriptive control, not an adjudicative cross-pressure machine-transfer demonstration. The rejection is unchanged because frozen Gate 2 was decided exclusively from the S1 prescribed-basket-pressure candidates. No S2 result broadens the accepted rejection beyond the frozen single-state reversible consolidation family.

The attempt-4 pilot executed 9 non-adjudicative trajectories in 2.22 s with zero failures and projected 143.1 s. The adjudicative run executed 580/580 valid trajectories in 120.75 s, used one process with nested threads fixed to one, launched no GPU work, and peaked at 135.8 MB RSS. The external bundle contains 580 atomic case records plus authority, snapshots, environment, manifest, logs, and timing.

## Verification

- Closed-form `J(x, phi)` and bed-height mapping match the independent high-precision WP03 reference.
- Constant-load backward-Euler response agrees with the analytical exponential within the frozen focused tolerance.
- Zero load and frozen deformation recover fixed hydraulics.
- Quasi-static evaluation uses the accepted equilibrium integral exactly.
- Machine storage residual is at most `2.39e-19 m3/s`.
- Across all final records: no nonfinite values, minimum bed-height ratio `0.9149396`, minimum mechanical porosity `0.0159204`, positive permeability/conductance, and no clipping.
- Five fast/intermediate/slow/high-pressure/near-bound refinement cases had a maximum base-versus-half-step relative difference of `2.38165e-4` across final flow, mass, maximum strain, and minimum porosity; no gate changed.
- Focused analytical/structural tests: 8/8 pass. Source-manifest verification and all 38 static gates pass at the executed source.

The pre-integration full repository suite ran 522 tests: 520 passed and 2 identified the expected shared-metadata count mismatch. The owner-authorized serial integration pass reconciled those records; the post-integration suite passes 522/522, the focused set passes 8/8, source verification passes 396/396, and static validation passes 38/38. The legacy v0.1.3 no-physics verifier reports 27/28 because current `main` legitimately contains later merged production physics; direct `origin/main` path comparison shows zero solver, case, or configuration changes in this lane.

Final execution counts: OpenFOAM launches 0, Puckworks calls 0, production solver modifications 0, SCI-LC-001A files modified 0, primary branch writes 0, and combined-mechanism trajectories 0.

## Gate-ordered scientific result

1. Artifact/numerical validity: pass, 580/580.
2. Resistance direction: pass, 35/35 global sets.
3. Pressure ordering: fail, 0/35.
4. Physical bounds: pass for all 35 source candidates.
5. Grind direction: not identifiable from available governed structure data.
6. Temporal shape: descriptive only after Gate 2 rejection; not used to rescue the family.
7. Cross-pressure transfer: fail because the shared law does not transfer ordering.
8. Distinctiveness: hydraulic evidence alone is not mechanism-identifying; synchronized deformation remains required.
9. Aggregate error: not an adjudicative rescue metric. The smallest three-pressure terminal-flow RMSE was `2.75234e-4 kg/s`.

### Retained S1 ordering margins

These post-execution reporting calculations use the original attempt-4 S1 case records and do not alter the frozen gate:

- Closest `Q5 > Q9` candidate: `pc=1,100,000 Pa`, `Theta_c=0.01`. `Q5=0.0015735766074527636 kg/s`, `Q9=0.0018287180470782172 kg/s`, so signed `Q5-Q9=-0.0002551414396254536 kg/s`. The governing records are `S1_SOURCE_PRESSURE_SCREEN-TPM_SINGLE_MODE_TRANSIENT-P5-PC1100000-TH0.01-SOURCE-PRESCRIBED_BASKET_PRESSURE` and its `P9` counterpart.
- Closest `Q9 > Q11` candidate: `pc=1,100,000 Pa`, `Theta_c=0.1`. `Q9=0.0018314950216231534 kg/s`, `Q11=0.0018316300300689492 kg/s`, so signed `Q9-Q11=-1.3500844579577773e-7 kg/s`. The governing records are `S1_SOURCE_PRESSURE_SCREEN-TPM_SINGLE_MODE_TRANSIENT-P9-PC1100000-TH0.1-SOURCE-PRESCRIBED_BASKET_PRESSURE` and its `P11` counterpart.

The prospective Gate-2 rule was strict signed ordering and froze no nonzero ordering-comparison tolerance, so neither comparison is within an applicable frozen pass tolerance. The `Q9-Q11` miss is nevertheless a numerical near-tie: its relative magnitude is approximately `7.37e-5`, smaller than the reported worst selected base-versus-half-step relative change (`2.38165e-4`). This qualification does not retrospectively change the strict Gate-2 failure.

Within the source screen, predicted maximum bulk axial strain ranged from `0.006554` to `0.085060`; the corresponding minimum bed-height ratio was about `0.91494`. These are reduced-model predictions under source-derived/synthetic screen parameters, not measurements. The smallest mechanical porosity across every control and signature case was `0.0159204`; proximity to this valid but extreme bound reinforces the rejection rather than rescuing it.

Fixed hydraulics cannot create the required resistance evolution. Quasi-static and finite-rate compaction increase resistance but not enough, within the frozen shared family, to reverse the pressure-driven flow ordering. Machine response changes pressure observability but does not repair the basket-pressure-conditioned ordering. The generic relaxing-resistance control remains hydraulically non-distinct without deformation observations.

## Measurement recommendation and claim ceiling

The discriminating package remains synchronized basket pressure, upstream pressure, flow, cup mass, and bed height/puck displacement during load, hold, and depressurization, plus grinder-specific packing/permeability characterization. Unload recovery is especially useful against swelling, fines, and irreversible damage, but no experiment is authorized here.

```text
EVIDENCE CLASS: POST_OBSERVATION_MECHANISM_DISCRIMINATION
MODEL CLASS: REDUCED_DIAGNOSTIC_TRANSIENT_CONSOLIDATION_MODEL
PRODUCTION OPENFOAM PHYSICS: UNCHANGED
PHYSICAL VALIDATION: NOT_ESTABLISHED
GENERAL WHOLE-SOLVER PHYSICAL VALIDATION: NOT_ESTABLISHED
WETTED-PUCK MODULUS: NOT_MEASURED BY THIS TASK
REAL-PUCK POROMECHANICAL PARAMETERS: NOT IDENTIFIED
EXPERIMENTAL COMMISSIONING: NOT AUTHORIZED
WP04-TPM-001: NOT AUTHORIZED BY THIS TASK ALONE
COMBINED MECHANISM MODEL: NOT AUTHORIZED
```

The screen establishes incapability of the frozen single-mode family to reproduce the required pressure ordering. It does not prove that real pucks are or are not poroelastic, does not identify a universal consolidation time, and does not authorize a combined mechanism or production implementation.

## External evidence retention

The valid attempt-4 external bundle remains retained under the symbolic authority `SCI_MD_002A_EXTERNAL_BUNDLE/attempt4/adjudicative`. Its manifest file SHA-256 is `20e206bcd24bf397ffbf4e17778f137037eab7b9361d818d0e1dc0f326085901`; the manifest's ordered-record aggregate SHA-256 is `8a9c954e19f7dffe814be1da6b8a808e6b33b4ac9b28524f6c2b56b148e897dc`; and the execution-authority file SHA-256 is `0ef48515a064e1f7641f8974f1d5bebb27271977294cd154160dd948f6460fe7`. All 580 atomic case records reverify by size and SHA-256: 105 S1, 105 S2, 175 T1, 105 generic-control, 70 unloading-design, 15 equilibrium, and 5 analytical-control records. Authority, protocol and matrix snapshots, environment, timing, stdout/stderr, and the manifest are also retained. The bundle plus the committed reducer, compact result, matrix, and protocol are sufficient to reproduce the reported reduction without treating a machine-specific absolute path as scientific authority.
