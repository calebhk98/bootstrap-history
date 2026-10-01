# Add batch start / filtered multi-select

**Status:** partly - `rush` previews count, total cost and yearly draw and takes limit, max_total_cost, max_annual_draw and reserve_cash; there is still no filter by subject, cost or hours, and the preview omits founder hours and trade bottlenecks

Several points in the Mexica run had dozens or hundreds of already-visible, legal projects: approximately 69 free/zero-hour techniques, approximately 180 visible projects below 500 currency, later 100+ projects in affordable tiers. Starting each individually is clerical work.

## WHY IT MATTERS

Mature play becomes bogged down in repetitive command entry. The strategic decision ("commit capital to broad development") gets buried under hundreds of individual `start` commands, making it impossible for the player to express their actual intent efficiently.

## WHAT WOULD RESOLVE IT

Examples:

```text
start all visible where cost=0 and hours=0
start filter:agriculture max_cost:500
start selected [...]
```

Always preview:
- count
- total committed capital
- total founder/director hours
- annual specialist bottlenecks
- calendar implications
- major risk/failure exposure

This is not automation of strategy if the player explicitly defines the filter and confirms the set.

## WHERE IT LIVES

`sim/engine/proto/dispatch.py` for command parsing, `sim/engine/proto/dispatch_money.py` or venture management code for batch start logic. `sim/engine/proto/render.py` for preview rendering.

## Confidence

Design recommendation

## Cross-references

Related to UX-006 (mature play needs development-program abstraction), UX-008 (project-start boilerplate), and UX-031 (idle directed hours handling).

Update: `rush preview` and `rush limit:N max_total_cost:N max_annual_draw:N reserve_cash:N` (sim/engine/proto/dispatch_ventures.py) give the confirmed, capped bulk start with a preview. What remains is choosing the set by filter (subject, cost, hours) and showing founder hours, specialist bottlenecks and risk exposure in the preview.
