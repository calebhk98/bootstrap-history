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
