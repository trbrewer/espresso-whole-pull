# SCI-MD-003 thin atlas consumer protocol

This no-governing-physics-change analysis consumes only the versioned Puckworks
`puckworks.response-atlas-export/v1` artifact pinned in `PUCKWORKS_ANALYSIS_PIN.json` and maps selected
retained EWP outputs. It does not import Puckworks internals, alter the runtime dependency lock, execute
OpenFOAM, use SCI-LC outputs, refit parameters, or promote validation. The selected retained sources are
WP03-002 corrected comparisons, VAL-CASE-001, and VAL-CORPUS-002. Missing observables remain unsupported.
