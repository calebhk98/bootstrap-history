# Silver is too cheap to produce

**Status:** open

Money is anchored to each civilisation's coin metal at its solved production
cost. For Rome the solved cost of silver makes the opening labourer wage about
three times the commonly attested first-century day wage of about one
denarius. The model is not tuned to history (CLAUDE.md 4.1), but the record
should be a plausible outcome (4.2), and a threefold miss points at the
production side: silver's extraction and smelting labour (ore grade, recovery,
cupellation losses, mining labour per tonne at the deposit depths) is likely
too low.

Measure with the solved silver price in labour-hours
(`python3 sim/solve_prices.py`) and the opening wage (`help` / `state` in a
Rome game), and compare to the attested day wage.

## What it would take

Re-derive the silver chain in `data/production/` from physical sources
(Laurion and Rio Tinto ore grades, cupellation yields, shaft labour at depth
from `sim/world/deposits.py`), then re-measure the wage. Do not adjust any
number to hit the day wage.
