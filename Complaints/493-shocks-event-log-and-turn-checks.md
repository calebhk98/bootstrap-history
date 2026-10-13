# No base-rate world shocks, no world event log, and the per-year checks miss ownership and anachronism

**Status:** open

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
