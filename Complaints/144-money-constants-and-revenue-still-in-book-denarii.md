# Money constants and technology revenue are still in book denarii

**Status:** open

Money is now anchored to each civilisation's coin, and costs are labour-hours
inside the engine, but some numbers are still written in the old book
denarii:

- engine money constants such as the "visibly rich" eminence threshold and
  fixed parts of living cost (one, the state's household-scale saturation,
  was converted to labourer-years);
- every technology's authored `rev` (revenue) and some cost fields in the
  tree. Against the new wages, payback times shifted for many nodes, and the
  pump payback guard in `sim/tests/test_early_playtest.py` was loosened to
  keep passing.

Find them with `grep -rn "denari" sim/engine --include=*.py` and the
`declare()` units in `python3 sim/constants.py --burndown`.

## What it would take

- Convert each constant to a physical unit (labour-hours, labourer-years, or
  a mass of the coin metal) and convert at the display edge.
- Derive a concern's revenue from what it produces and the market price of
  that output, instead of an authored `rev`, and restore the pump guard.

## Progress: one conversion boundary (units)

- [x] Authored book denarii convert once, through labour hours, into each
  civilisation's coin (`sim/engine/money_units.py`): node `rev`, `up`, `cap`,
  materials, the book goods table, and every declared money constant
  (`book_money=True` on `declare`; each `Sim` holds its own converted copy).
  `python3 sim/constants.py` lists the declared constants; grep for
  `book_money=True` for the converted set.
- [x] A `Sim` for a civilisation other than the loaded default gets its own
  copy of the tree in its coin (`data.nodes_in_civ_money`), and protocol
  screens read `sim.nodes`.
- [x] Tests: `sim/tests/test_money_units_one_boundary.py` (revenue over wage,
  material price over hourly wage, coin mass rescales every figure).
- [ ] The pump payback guard in `sim/tests/test_early_playtest.py` stays at its
  loosened threshold: the unit fix restores each node's payback ratio to what
  it was, and the remaining gap to the original guard comes from skilled-trade
  wages now following the training premium.
- [ ] Derive a concern's revenue from what it produces instead of an authored
  `rev` (still open).
- [ ] Inline money amounts in the auto policies were converted with
  `Sim.book_money`; any new money literal must go through it too.
