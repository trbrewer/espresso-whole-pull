# VAL-CORPUS-002 Stage B1 Calibration Result

**Disposition:**
`VAL_CORPUS_002_STAGE_B1_CALIBRATION_NOT_FROZEN_INFRASTRUCTURE_OR_ORCHESTRATION_FAILURE`

The authorized Experiment-7/H1 calibration stopped without a frozen P2
candidate. Twenty evaluations completed and passed the target-mass,
boundedness and conservation gates. Evaluation 20 reached solver `End` but
returned exit 139 during MPI finalization, so it was retained as
`VALID_EXECUTION_WITH_TYPED_NUMERICAL_FAILURE` with no objective. The next
fresh case then exited 139 inside `blockMesh`; this is the terminal
`INFRASTRUCTURE_OR_ORCHESTRATION_FAILURE`.

The active log-k interval was
`[-1.0674358883689066, -1.0671314545614026]`, width
`0.00030443380750400095`, rather than the required `1e-8`. No optimizer row
was marked `SELECTED_FINAL`. No governed calibration or artifact manifest was
created, the governed validator and P2 freeze barrier were not invoked, and
the best completed evaluation is retained only as a diagnostic—not as a
selected or frozen rate.

The best completed diagnostic was sequence 17 at
`k=0.3439538670796447 s^-1` (`0x1.60357149c25c4p-2`) and
`log(k)=-1.0672477379285445` (`-0x1.113725d322116p+0`), with objective
`0.00393198959100366`. Its model cup-solute vector was
`[2.7821365737253676, 4.22720844512753, 4.33463605150242] g`; this is not a
calibration result.

The exact Foundation OpenFOAM 12 executable was reused without rebuilding.
Experiment 1–6, H0, Waszkiewicz chemistry, production, sensitivity, transfer,
and protected results were not accessed. No refitting occurred. Stage B2 is
not authorized and was not started.
