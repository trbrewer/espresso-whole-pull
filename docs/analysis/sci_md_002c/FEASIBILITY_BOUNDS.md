# SCI-MD-002C feasibility bounds

The canonical calculations are in `validation/cases/sci_md_002c/SCI_MD_002C_FEASIBILITY_BOUNDS.json`.

Using governed terminal observed pressure and flow, the effective resistances are approximately (2.1123\times10^{11}), (4.6107\times10^{11}), and (5.6552\times10^{11}) Pa·s/m³ for P5, P9, and P11. The common hydraulic convention is the observed P9 terminal-flow scale, transferred unchanged. It is a reference scale, not a clean-bed physical measurement.

At the P11 governed terminal pressure, at least (8.9091\times10^{10}) Pa·s/m³ additional resistance is required to reduce predicted flow below the governed P9 observed terminal flow. Matching the P11 observed terminal flow relative to the P9 anchor requires (1.0446\times10^{11}) Pa·s/m³. The analogous P9-vs-P5 threshold is zero under this convention because the common-anchor P9 prediction is already below the observed P5 target.

The mobilizable inventory is `dose × fines mass fraction × mobilizable fraction`, with 18.5 g dose, fines fractions 0.02/0.06/0.10, and mobilizable fractions 0.25/0.75. The resulting range is 0.0925–1.3875 g; the model never treats all coffee as mobilizable fines.

For deposited mass (m_d), compact-layer porosity \(\epsilon_c\), solids density \(\rho_s\), and filter area \(A\):

\[
h_c=\frac{m_d}{\rho_s(1-\epsilon_c)A},\qquad
R_c=\frac{\mu\alpha_c m_d}{A^2}.
\]

The implied permeability is (k_c=1/[\rho_s(1-\epsilon_c)\alpha_c]), which recovers (R_c=\mu h_c/(A k_c)). The matrix brackets \(\alpha_c\) at (10^{12}) and (10^{13}) m/kg. Regions whose full-inventory resistance remains below the frozen P11 ordering threshold are `CLEARLY_INVENTORY_IMPOSSIBLE`; others are `POTENTIALLY_FEASIBLE`. No analytic pruning is applied to the transient matrix, so closure dependence remains visible.

Disposition: `POTENTIALLY_FEASIBLE_ONLY_WITH_SYNTHETIC_CLOSURE_BOUNDS`. The bounds are not real-puck measurements.

