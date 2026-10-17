# Some reads change state, and traders ship goods the home market has no book for

**Status:** closed

Found fixing `multi_year_step_log`: `project_resource_throttle` banks stock, records the year's opening stock, notes
draws and counts shortages when it is only asked; the multi-year step now uses a side-effect-free
`peek_project_resource_throttle`, but the `stuck` screen (`sim/ui/proto/dispatch_inspection_stuck.py`) and
`sim/engine/shortage_conditions.py` still call the mutating one, so looking at a screen can change the game.

Found fixing `foreign_actor_trade`: traders ship a large tonnage a year of cast iron to a home that has no market book
or producer for it, so the home price response is undefined for that cargo.

What it would take: one read-only throttle for every screen and query (and a test that any screen command leaves a
save dump unchanged); traders ship only goods the destination has a market for, or the destination opens a market
when cargo lands.

## Resolution

- `peek_resource_throttle` joins `peek_project_resource_throttle` (one shared restore in `sim/engine/economy_electricity.py`);
  the `stuck` screen, `slowed_projects` and `project_useful_hours` read through them.
- `sim/tests/test_read_only_commands_leave_state.py` runs every read-only command (plain and compact) twice on one
  unopened game and requires the save dump unchanged on the second look; every registered command must be classed as
  reading or changing, so a new one is forced into a class. The first look may set up defaults and "last seen" markers
  (score, log, commitments, programme, ventures, available, capacity); `pursue` changes state (it starts projects) and is
  classed so.
- Traders no longer route a cargo into a place with no market for the good (`World.has_market`, used by
  `gaining_routes`); regression check (d) in `sim/tests/test_foreign_actor_trade.py`.
