# The suite's short spin-up hides what the full-length opening does

**Status:** closed - the tooling is in place; the checks that fail today are expected failures owned by 473, 519 and 507 Stage 2 (see Resolution)

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

## Resolution

Built, no model change:

- `sim/engine/opening_checks.py`: plain functions returning a `CheckResult` (value, bound, passed, detail): price over
  making cost for the sited ores, the staple and the coin metal; the money stock against coin wear over the spin-up
  trace; the unskilled wage over the wage floor; whether the spin-up settled.
- `sim/engine/opening_checks_run.py`: opens a civilisation's full-length opening (the shipped entries when they match
  the source, else computed into the disk cache), takes the money trace (cached, and shipped with the openings), steps
  one year and runs the checks.
- `python3 sim/simulator.py opening-checks [--civs a,b]` prints the table for every civilisation.
- `python3 sim/simulator.py openings` runs the checks (`sim/engine/opening_checks_gate.py`, called from
  `shipped_openings_build.build_reporting`) and refuses to write an opening that fails them, unless
  `--allow-failing REASON` is given; the reason is printed.
- `sim/tests/test_full_length_opening_checks.py` (slow tier) asserts every check for every civilisation.
  `sim/tests/test_opening_checks.py` (quick) covers the functions and the gate.

Bounds and where they come from: a price over making cost stays within an order of magnitude either way (the widest
grade spread among one metal's deposits, as in `test_sited_ore_price_over_cost`; below the band nobody would make the
good); the money stock of the trace's last decade over its first decade stays above what one decade of unreplaced wear
leaves (the 473 test's reading: a mint that replaces wear may lag one decade, no more); the unskilled wage is at least
the wage floor; the spin-up's last yearly change is within `SPIN_UP_TOLERANCE`. A price check only reads goods whose
markets cleared lately (a stale good's shown price is its cost).

Expected failures (`EXPECTED_FAILURES` in the test, each marked `expectedFailure`, so the topic turns red when one
starts passing: remove its entry then). The current table is `python3 sim/simulator.py opening-checks`.

- sited ores over cost: Rome, Han, Mexica, Norse: 519.
- coin metal over cost: Rome, Han, Norse, England: 507 Stage 2.
- wage over floor: England: 507 Stage 2.
- money stock against wear: Rome, Han, England: 473.
- spin-up settled: every civilisation: 473.

Regenerating `openings/` (507 Stage 2) will run the gate; until those complaints close it needs `--allow-failing`.
