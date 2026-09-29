# Research/filter views should distinguish "startable now" from "known but blocked"

A filtered research view that repeatedly includes things the player cannot access creates noise, especially under fog.

## WHY IT MATTERS

When players ask "what can I do?", showing hundreds of blocked-but-known items alongside a few startable ones makes the actionable set invisible. This is particularly frustrating under fog where the blocking reason gives no direction.

## WHAT WOULD RESOLVE IT

A research listing should support explicit states:
- Startable now
- Known, blocked
- Active
- Completed
- Hidden by fog

Default a "what can I do?" filtered view to "startable now", with a toggle for blocked known items.

If the current filter intentionally includes blocked items, make that visually explicit.

## WHERE IT LIVES

`sim/engine/proto/dispatch.py` for command dispatch, `sim/engine/proto/techtree.py` for research/capability view rendering, likely `sim/engine/proto/render.py` or `render_screens_big.py` for the tree display.

## Confidence

Design recommendation / reported UX issue

## Cross-references

Related to UX-004 (literal keyword search fragility). UX-002 (fog messages repetitive) is adjacent - users need clearer filtering to avoid noise.
