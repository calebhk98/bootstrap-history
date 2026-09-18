# “Waiting on money” can still make progress

**Type:** Misleading status text  
**Priority:** Medium
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `sim/engine/proto/state.py` now prints exactly the two states suggested here: "unfunded now; will fund opportunistically as revenue..." and "fully blocked until funding is available...". See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

Crop rotation was labelled “waiting on money” because its next 470-den instalment could not be raised. During the same year it nevertheless received 470.3 den as revenue arrived.

## Why it matters

The wording implies no progress, which can cause unnecessary stopping or replanning.

## Suggested change

Use distinct states such as “unfunded now; will fund opportunistically this year” and “fully blocked until funding is available.”
