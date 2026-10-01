# Silver is too cheap to produce

**Status:** partly - the silver chain now agrees with the deposits and counts both lead reductions; the opening Rome wage is still well under the attested day wage and the remaining gap is not a recipe error

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

## Progress

- [x] Measured (`python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`,
  the figure the engine anchors money to): Rome's solved silver cost fell
  from about 1112 to about 1381 labour hours per kg after the fix below, so
  one denarius went from 3.00 to 3.73 labour hours (the coin is 2.7 g).
  England and Norse (also silver-coined) move by a few percent; Han (bronze)
  and Mexica (cotton) do not move.
- [x] The lead recipe reduced the ore once but the cupellation litharge is
  reduced back to lead a second time; fuel and furnace hours now count both
  passes (labelled heuristic: second pass equal to the first).
- [x] The direct silver-ore recipe used a 5 kg/t grade and 25 h/t of mining;
  the silver deposits give about 0.8 kg/t and about 54 h/t of rock. Both now
  follow the deposits, and `sim/tests/test_silver_chain_physics.py` pins the
  agreement.
- [x] Curated per-tonne mining running costs are gone; mining opex is the
  deposits' extraction labour at the miner wage (see 144).

## Remains

- Silver is still roughly three times cheaper in labour hours than the
  attested day-wage ratio implies. Measured causes, none of them tuned away:
  the batch is split between lead and silver by demand-anchored value, so
  silver bears most of the batch whatever the physical effort (the market
  and demand agent's area); ore dressing (crushing, washing, concentrating)
  is not costed apart from the rock-breaking figure; drainage and ventilation
  of deep workings are folded into one haulage multiplier.
- The recipe's 0.46 kg of silver per tonne of lead is far leaner than both
  the deposits (`britannia_lead` carries about 3.3 kg per tonne of lead) and
  the empire totals in `data/world/resources.json` (silver output over lead
  output is several times larger). Making it consistent would make silver
  cheaper still, so it was left, and needs the deposit byproduct data
  reconciled first.
