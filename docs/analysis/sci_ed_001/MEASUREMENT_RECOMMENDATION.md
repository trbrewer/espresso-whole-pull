# SCI-ED-001 bounded measurement recommendation

The smallest defensible package produced by the frozen screen is a **partial**, not complete, discriminator:

- program: `P8_SLOW_RAMP_5_TO_9`;
- measured nodes: basket-top gauge pressure, basket-bottom outlet flow, and cumulative delivered mass (`M0`);
- preconditioning: 500,000 Pa gauge for 4.65666677903568 s, preserving all evolved states;
- program: a 10 s linear ramp from 500,000 to 900,000 Pa gauge, then 900,000 Pa through 80 s;
- planning targets: basket pressure 8 kPa, outlet flow 0.02 mL/s, cumulative mass 0.5 g, native sampling and inter-channel synchronization 20 ms;
- interpretation: three of six frozen family pairs separated under N1; three remained overlapping.

No alternative frozen program achieved even this partial pair coverage. Therefore no apparatus-infeasibility fallback can be claimed as an equivalent discriminator from this screen.

A complete future discrimination package cannot yet be defensibly specified. Deformation is scientifically relevant to reversible consolidation, fines/turbidity is relevant to deposition, and wetting timing is relevant to swelling, but the present family interfaces do not provide common definitions for those outputs. The fines/turbidity measurement target is also unquantified. Separate upstream pressure is `MACHINE_LAYER_NOT_COMMON` and cannot identify a puck mechanism by itself.

Before any future commissioning decision, independent work would need to establish apparatus feasibility, preparation metadata, common direct-observable definitions, instrument mappings, and frozen uncertainty bounds. That work is not authorized here. The pressure waveform and planning targets are model-informed design inputs, not procurement specifications or demonstrated sensor capabilities.

`MODEL_INFORMED_FUTURE_DESIGN_ONLY`

`EXPERIMENTAL_COMMISSIONING_NOT_AUTHORIZED`

