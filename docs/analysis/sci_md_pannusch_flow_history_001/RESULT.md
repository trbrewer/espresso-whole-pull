# SCI-MD-PANNUSCH-FLOW-HISTORY-001 result

`SCI_MD_PANNUSCH_FLOW_HISTORY_001_FLOW_AUTHORITY_INELIGIBLE`.

Released source establishes programmed flow endpoints as machine instructions, not measured inlet or puck-face flow. It supplies no ramp coordinate, programme zero, duration, support, or pre/post holds, so C07/C08 cannot be encoded as an exact source schedule. `MassData.flow` is not a scalar: the mass-scale script stores the vector `dm/dt = 2 a t + b` from a quadratic fit to beverage scale mass, in g/s. The script's `/0.98` conversion is plotted but not stored, and released extraction processing only copies the stored vector; it does not use it as Pannusch Q. Beverage outflow is not authorized as inlet flow, no applicable mass-to-volume conversion is established, and the scale, programme, and solver clocks are not mapped.

Therefore Q0 is the only eligible entry and is a baseline, not a nonidentity candidate. QP is exactly Q0 on C01/C02/C05/C06 and ineligible on C07/C08. The volume-equivalent diagnostic is gated off; QM and QD are ineligible. Phase B was prohibited before chemistry access, so no chemistry scores, winner selection, or retained-residual explanation were manufactured. Constant-q `simulate_fractions_qt` parity passed the frozen 1e-8 tolerance (hard ceiling 1e-6), with observed maximum normalized-share difference 0.

The existing scalar-start treatment is retained. `XSV-PANNUSCH-EWP-INPUT-MAPPING-001` is selected, not implemented. TARGET_EXPOSED; SOURCE_INTERNAL; NOT INDEPENDENT VALIDATION; NOT PHYSICAL VALIDATION; NOT HYDRAULIC VALIDATION; NOT PUCK_FACE_FLOW VALIDATION; NOT PRODUCTION QUALIFICATION. No production adoption occurred.
