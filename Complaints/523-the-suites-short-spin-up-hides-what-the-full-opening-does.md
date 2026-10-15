# The suite's short spin-up hides what the full-length opening does

**Status:** open

Tests open games on a shortened spin-up (`ROME_SPIN_UP_YEARS` in `sim/tests/harness.py`) to stay fast, while a
player's game runs the full-length spin-up (or the shipped openings, which are full-length). Found in 519: after one
step, a sited ore's price over its making cost differed between the two by more than an order of magnitude for
some ores (Rome's iron ore was far worse in the full-length opening than in the suite's), and earlier the bronze
complaint (502) and the money drain (473) were only visible over long runs. A relationship test that passes on the
short spin-up says little about the game a player opens.

What it would take: a slow-tier set of relationship checks (prices over making cost, money stock against wear, wage
over floor, settled-or-not) run on each civilisation's full-length opening, reusing the shipped openings so it costs
a cache read when nothing changed; `python3 sim/simulator.py openings` should refuse to write an opening that fails
them. Measure: run `sim/tests/test_sited_ore_price_over_cost.py` with and without `ROME_SPIN_UP_YEARS` set.
