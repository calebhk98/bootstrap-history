# Bare `rush` mutates the portfolio without preview

**Type:** Destructive command UX  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `_cmd_rush` (`sim/engine/proto/dispatch.py`) now returns a `preview`/`nothing_changed` response and requires `rush force` or `rush limit:N` to actually act - exactly the fix suggested here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

Trying bare `rush` for discovery immediately started 57 projects before founder-hour capacity stopped it. No time advanced, but the player had to stop all projects to restore the portfolio.

## Suggested change

Make bare `rush` preview the set and require confirmation; retain an explicit force form for direct execution.
