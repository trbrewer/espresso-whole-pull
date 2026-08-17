# SCI-MD-002C joint ordering feasibility bounds

The canonical calculations are in `validation/cases/sci_md_002c/SCI_MD_002C_FEASIBILITY_BOUNDS.json`. They use the selected 800-row saturated-window endpoints, not the full-overlay terminal values: P5 = 450428.3 Pa, P9 = 870708.2 Pa, and P11 = 1041755.1 Pa. The common resistance is the accepted observed-P9 full-overlay terminal-flow hydraulic scale, 461066511220.88336 Pa·s/m³, transferred unchanged; it is a reference scale rather than a clean-bed measurement.

The feasibility gate is the model ordering itself. For cake resistances `Rc5`, `Rc9`, and `Rc11`:

\[
R_{c9,required}(R_{c5})=(P_9/P_5)(R_b+R_{c5})-R_b,
\]

\[
R_{c11,required}(R_{c9})=(P_{11}/P_9)(R_b+R_{c9})-R_b.
\]

The optimistic `Rc5=0` joint thresholds are 430206066602.08014 Pa·s/m³ at P9 and 605292750627.3674 Pa·s/m³ at P11. They are necessary, not sufficient, bounds.

Mobilizable inventory is `dose × fines fraction × mobilizable fraction`; maximum depositable mass additionally multiplies retention. Cake resistance is `mu × alpha_c × m_deposit / A²`, with layer thickness `m_deposit/[rho_s(1-epsilon_c)A]`. The optimistic maximum assumes complete release, transport, and retention-adjusted available deposition by reporting time.

Across the 24 frozen closure regions, exactly one is potentially feasible: fines fraction 0.10, mobilizable fraction 0.75, retention 1.0, and specific cake resistance 1e13 m/kg, whose maximum resistance is 720462987844.896 Pa·s/m³. The other 23 regions are `CLEARLY_INVENTORY_IMPOSSIBLE`. No transient rows are pruned; impossible regions remain governed negative controls.

Disposition: `POTENTIALLY_FEASIBLE_ONLY_WITH_SYNTHETIC_CLOSURE_BOUNDS`. These bounds are not real-puck measurements.
