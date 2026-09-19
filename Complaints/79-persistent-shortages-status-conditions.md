# Persistent shortages should become status conditions, not identical annual messages

Messages such as "buy ~1 more hectare of coppice" repeated year after year with nearly identical wording.

## WHY IT MATTERS

A stable shortage that persists for years is important state information, but when it generates an identical message every turn, the player learns to ignore it. The signal disappears into noise.

## WHAT WOULD RESOLVE IT

Create persistent conditions:

```text
CHARCOAL CONSTRAINED
Throughput: 46%
Deficit: 12.4 t/year
Duration: 4 years
Trend: improving
Pending relief: 500 t/year coal shaft in 1 year
```

Only generate a new event when the condition materially changes.

## WHERE IT LIVES

`sim/engine/proto/render_screens_economy.py` for capacity/shortage display, `sim/engine/proto/render_screens_status.py` for status condition rendering. Also event generation logic that creates shortage messages.

## Confidence

Design recommendation

## Cross-references

Related to the repetition audit in the findings (section 5, item 5: "Persistent resource warnings"). UX-009 in findings is this complaint.
