# VAL-CORPUS-002 Stage B1 exact-head semantic correction

Authorization: `VAL-CORPUS-002-B1-CALIBRATION-2026-08-03`  
Profile: `EWP_CALIBRATION_STAGE_V1`

This append-only correction preserves both optimizer attempts and every
execution artifact. It adds closed numerical-verification and retained-trace
semantic validation plus a deterministic finalize-only recovery path. No
OpenFOAM command, optimizer evaluation, transfer-result access, production P2
materialization, Stage B2 action, or merge is performed.

The original governed bundle remains immutable. Its selected configuration,
reduction, optimizer trace, and retained trace are byte-identical in the
strengthened bundle. The numerical-verification record is superseded solely
to remove the non-contract `selected_attempt` field and bind
`selected_evaluation_sequence` to global optimizer sequence `25` instead of
attempt-local evaluation sequence `5`. The attempt-local identity remains in
the separately verified recovery-provenance record.

The selected scientific values remain exactly:

- `k = 0.3439597024835067 s^-1` (`0x1.6036f8e53bf4ep-2`);
- `log(k) = -1.0672307724139207` (`-0x1.11360930cd77cp+0`);
- objective `0.003931989579189616`;
- model vector `[2.782144673131987, 4.227214080217558, 4.334636376028199] g`;
- final log-interval width `7.687140035628204e-09`.

Semantic reduction of the immutable trace passes. Saturation spans `[0,1]`,
concentration spans `[0,177.909739457668] kg/m3`, and the configured capacity
is `180 kg/m3` (descriptive comparison only). Maximum reconstructed liquid
and solute relative residuals are `1.0140569150050877e-13` and
`1.7794712945888162e-11`, respectively, against the unchanged `1e-8` gates.

The strengthened governed validator and P2 freeze barrier pass. This remains
a frozen calibration candidate pending final B1 review; it grants no Stage B2
authority.
