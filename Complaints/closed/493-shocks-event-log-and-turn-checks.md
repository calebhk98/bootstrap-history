# No base-rate world shocks, no world event log, and the per-year checks miss ownership and anachronism

**Status:** closed - base-rate world hazards for every country, a saved world event log with a protocol command, and yearly ownership, technique and capacity checks

- Random events per seat are patron death, fire and banditry (`sim/engine/society_hazards.py`). Larger
  shocks are dated hazards in the one civilisation file (`sim/engine/shock_year.py` reads `self.civ`), so
  in a game of several countries only the home one is hit, and floods, earthquakes and bad rulers have no
  base rate (see 490 for plagues).
- The log is per seat (`household.log`) and the cause book keeps a few figures for a few years
  (`sim/engine/cause_book.py`). Nothing records world events (a battle, a change of owner, a famine abroad)
  with a date and a cause for every player to read.
- `sim/engine/invariants.py` checks finite and non-negative stocks and labour headcounts, and runs only
  when `sim.debug` is set (`sim/engine/year_run.py`). Nothing checks one owner per tile (483), that no
  actor uses a technique it does not hold, or that counts stay within production limits.

Why it matters: the group uses the simulator to keep a long timeline consistent; they asked for the
validation rules to run every turn and for a dated record of what changed and why.

What it would take: a world hazard source with base rates applied to every country; a world event log
saved with the game; the ownership, technique and capacity checks added to the invariants and run
every year in multi-country games.

## Resolution

- Base-rate shocks (flood, earthquake, bad ruler) are data in `data/world/world_hazards.json`, each labelled a
  temporary heuristic that names its retirement. `sim/engine/world_hazards.py` draws per country, kind and year
  from a hash of the game's seed (no shared dice) for the home country and every partner in the agent economy.
  A hit cuts that country's people: the home society by its cohort shock, a partner by its strata. The dated
  hazards in civilisation files are untouched (their retirement is 490).
- The world event log (`sim/engine/world_events.py`, saved in `state.economy.world_events`) holds dated
  records {year, kind, actors, tiles, cause, facts}. It is written by `transfer_tile` (tile ownership),
  the world hazards and a famine watch over every country's strata. Every seat reads it with the
  `world_events` command (`sim/ui/proto/dispatch_world_events.py`).
- `check_yearly_invariants` (`sim/engine/invariants.py`) runs ownership, technique and capacity checks every
  year when the game has more than one country, with or without `sim.debug`. Cost: measured by timing the checks and a full
  `step` in a Rome and Han game, the checks take a fraction of a millisecond against several seconds for the year.
- Tests: `sim/tests/test_world_events_and_hazards.py`.
- Not covered: plague abroad has no event, because the disease model runs for the home country only (490).
