# Large completion waves should be summary-first

At mature scale, 10-25 technologies could complete in a turn. Full per-project narration becomes log spam.

## WHY IT MATTERS

When dozens of projects complete, individual completion messages become noise that obscure the strategic picture. The player loses the ability to see what happened and what changed.

## WHAT WOULD RESOLVE IT

Suggested default:

```text
22 projects completed
1 failed
3 major unlocks
Literacy +2.1 points
Recurring net +8,100/year
New bottleneck: scribes
```

Expandable list for every project.

## WHERE IT LIVES

Event aggregation and rendering logic in `sim/engine/proto/render_screens_big.py` or completion-event handling. Project-completion notification system.

## Confidence

Design recommendation

## Cross-references

Related to the repetition audit (section 5, item 7: "Large completion waves"). Also connects to UX-011 (event severity hierarchy) and the recommended UI philosophy in section 5 of the findings.
