# SCI-MD-MASS-DELIVERY-007 research consumer

G1 / NO_GOVERNING_PHYSICS_CHANGE. [Producer issue #291](https://github.com/trbrewer/puckworks/issues/291); [consumer issue #197](https://github.com/trbrewer/espresso-whole-pull/issues/197).

This thin harness reuses research_conditional_tail_delivery and the exact frozen Puckworks source adapter. It verifies separately the immutable 006 parent producer/runtime/models and the new task execution producer. It accepts serialized typed pooled inputs plus coordinate-only queries. Mathematical integration stays in the parent runtime; production dependency locks are unchanged.

```bash
python scripts/research_grudeva_pooled_tail_delivery.py --execution-producer "$TASK007_PRODUCER" --parent-producer "$PARENT006_PRODUCER" --early-inputs "$PRIVATE_EARLY_INPUTS" --queries "$PRIVATE_QUERIES" --output "$PRIVATE_OUTPUT"
python scripts/research_grudeva_pooled_tail_delivery.py --execution-producer "$TASK007_PRODUCER" --parent-producer "$PARENT006_PRODUCER" --synthetic --output "$PRIVATE_SYNTHETIC_OUTPUT"
```

Use isolated committed producer checkouts at the exact HANDOFF identities. Source-derived rows remain private. No fit, scoring, native run or production adoption occurs in this consumer. [Protocol](PROTOCOL.md) and [limitations](MODEL_CARD.md). PHYSICAL_VALIDATION=NOT_ESTABLISHED.
