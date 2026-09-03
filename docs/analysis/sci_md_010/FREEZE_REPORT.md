# SCI-MD-010 R4 execution-contract addendum

The R3 scientific design is accepted and unchanged. R4 corrects verbatim row-index identity binding, real metadata-only partition preflight, paired normalized condition/brew uncertainty, uncertainty-aware decision enforcement, auditable failed folds, and independent result recomputation. Direct line pressure, endpoint_100s target, 56 brews, 11 folds, B0/B1/E1, and E2 NOT_ADJUDICATED remain frozen.

The real-binding preflight joins sources by source_row_id and copies physical_unit_id and condition_id verbatim from the row index; it stops before fitting or prediction. Each fold persists its training scale and exact physical memberships. B1/E1 bootstrap draws are paired in normalized fold-loss space, using 2,000 condition-then-brew draws, no refit, seed 20260902, nearest-rank intervals. Failed required folds yield a complete auditable blocked package and NOT_ADJUDICATED, without false scoring-complete flags. The result validator recomputes memberships, errors, scales, losses, uncertainty, diagnostics, lane/architecture, and experiment recommendation.

No real score occurred. A correction-limited final exact-freeze review is required.

Disposition: SCI_MD_010_R4_REAL_EXECUTION_AND_DECISION_CONTRACT_RECONCILED_READY_FOR_CORRECTION_LIMITED_FINAL_EXACT_FREEZE_REVIEW.
