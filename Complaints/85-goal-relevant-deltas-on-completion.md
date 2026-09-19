# Show goal-relevant deltas on completion/event messages

A technology could materially change the literacy ceiling or actual literacy, but the completion message did not necessarily say so. The player had to query state and infer the cause.

## WHY IT MATTERS

Without explicit feedback about how completions affect the current goal, players cannot understand the game's interconnections or plan effectively. They must manually cross-check goal state after every potentially relevant completion.

## WHAT WOULD RESOLVE IT

If a completion changes the current goal metric or one of its live determinants, append:

```text
Goal effect:
- General literacy: 30.0% -> 40.5%
- Literacy ceiling: unchanged
- Schooling speed: +...
```

Under fog, reveal only effects of the thing just completed, not hidden future dependencies.

## WHERE IT LIVES

Completion message rendering in `sim/engine/proto/render_screens_big.py` or related project-completion handlers. Goal-state tracking and delta calculation.

## Confidence

Design recommendation

## Cross-references

Related to UX-001 (measurement goals need anatomy view) and UX-015 in the findings. Together these address goal-feedback clarity.
