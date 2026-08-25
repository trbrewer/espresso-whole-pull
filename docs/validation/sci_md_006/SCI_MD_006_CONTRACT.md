# SCI-MD-006 contract

G1; `NO_GOVERNING_PHYSICS_CHANGE`. H0-HIST is the historical SCI-MD-004 common-parameter indexed transport model and is excluded from optimization and decision. H0-SHARED fits one shared k and one shared absolute Csat. H1-SPECIES fits exactly species-specific k and absolute Csat values through the same adapter. Positive parameters use natural-log bounds k [0.002, 0.5] s^-1 and Csat [0.2, 100] kg/m3.

The primary inventory is the per-species arithmetic mean over training experiments only. Whole experiments are leave-one-out blocks. The objective is 0.5 mean caffeine log-ratio squared plus 0.5 mean trigonelline log-ratio squared. Blocked scores are computed over concatenated OOF rows. Advancement requires 15% joint improvement, 5% species noninferiority, identifiability, no boundary distances <=0.01, optimizer, nesting, parity, numerical, governance, and integrity gates.

Reduced/full fallback thresholds frozen before scoring: species NRMSE <=0.01 and endpoint cup-mass relative discrepancy <=0.005. Profiles use chi-square(1)=3.841458820694124 and relative 95% half-width <=0.25. No Angeloni access, new holdout, solver change, fitted inventory/diffusivity/hydraulics, commissioning, or physical-validation claim is permitted.

SCI-MD-006 may establish only whether four species-specific production parameters outperform two shared production parameters under the frozen same-lineage Schmieder training evidence, the fold-safe pooled inventory policy, the frozen reduced/full application, and the declared blocked-CV decision rule. It does not establish independent predictive or physical validation.
