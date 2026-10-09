# Labour is mostly idle and prices sit far above cost on the agent economy

**Status:** partly - done on fixtures: the wage floor is the household's need basket at local prices less its plot, entry is drawn by a lasting margin on smoothed prices with no one-newcomer-a-market-a-year cap, and `simulator.py economy-check` prints the decomposition. Remaining: draught animals and their fodder in the plough crops' recipes (from 395), and a whole-game run of `economy-check` to see whether idle labour and wide margins fall out

In every civilisation only a small share of the hours households offer is hired, and the rest go unhired or to own plots, so the unskilled wage sits at the workers' ask (the family's subsistence floor per offered hour) almost everywhere. Wages are a small part of household income; most of it is property income (dividends) and food grown for itself. At the same time goods sell far above the cost of the labour in them, with little land rent, and few makers enter. An economy with idle hands, free land and wide margins is not in competition: entry fires only where buyers are turned away (`sim/economy/entry.py`), so incumbents keep their margins and pay them out as dividends.

This, not the wage rule, is what Complaint 388 measures: the wage in kg of wheat is the subsistence basket's cost over the wheat price. Wheat is a minor and dear food in Rome and Mexica, so the wheat wage reads low there; in food-need units the civilisations are close. Mexica also has no maize good in the data.

Evidence: shares of hours hired, wage over floor and price over labour cost were measured by decomposition scripts in a scratch directory (not committed; no command prints them yet). The figures are in Complaints/reports/agent-economy-review-round-three.md. `python3 sim/economy_validate.py` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`) shows the wheat wage.

What it would take:
- Entry that competes margins away without chasing one-year price spikes (an entry-on-price rule was tried; see the review report).
- Recipes with their full inputs, so that labour cost is a fair floor (Complaint 395).
- A validation wage measured against the household basket, not wheat alone (`sim/economy_validate.py`).

Related: 388, 393, 395.


## Round four

See `Complaints/reports/agent-economy-review-round-four.md`. Producers were all on each market's anchor tile while each tile is its own labour market, so most people off the anchor could not be hired: they are now spread by labour, cost and site limits (`sim/economy/location.py`). Losers now exit (`producers_close.py`, `producer_exit.py`). Entry drawn by a lasting margin was built and taken out: it made grain prices swing; the report records what it drew in and the design for the next attempt.
## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 388 (`closed/388-unskilled-wages-low-in-rome-and-mexica.md`): unskilled wages look low in Rome and Mexica; needs sourced day wages.
- 393 (`closed/393-land-has-no-price-so-free-entry-drives-food-to-labour-cost.md`): land has a market now; entry on price is off and rents swing.
- 395 (`closed/395-recipes-for-crops-carry-no-seed-or-draught-input.md`): crop recipes carry no seed or draught input; physical shares needed in the wheat entries and other crops.

Owner decision (2026-10-09): the model is wrong where a seller (of a good or of their own hours) who cannot sell keeps the same ask. A seller who cannot sell lowers the ask year by year until it sells (a household that cannot sell its hours must eat), and a seller who sells out raises it until it no longer does; margins and idle labour should fall out of that. Look at how the industrial revolution moved wages off subsistence for the shape to expect.


## Round five: asks follow sales

Done (fixtures only; `python3 -m sim.tests --only asks_follow_sales,economy_labour_ask_floor,labour_core_clearing`):
- Labour: the core remembers each (area, trade) ask as a multiple of the reservation wage (`MarketState.asks`). Hours employers would not take at the wage lower it by the unsold share; demand beyond supply raises it (never past the wage the hours fetched). Speed: `ASK_ADJUSTMENT_SHARE_PER_YEAR`, a labelled heuristic. A quote with hours on offer and no bidder drifts down to the ask instead of staying put.
- The subsistence floor is no longer a bound under the ask. The bound is what the family has without selling hours: the value of its own plot (`labour_ask_floor.py`, from the same land-only recipes and fertility `households_own.py` grows with). A tile whose families have no plot option has no floor; their wage can fall toward nothing, and the engine's population response is what must stop it.
- Entrants and switchers value a wage under the outside option as the outside option (the hours go to the plot), so a glutted trade does not repel entrants below the floor.
- Goods: a producer that worked last year and holds no stock beyond its needs raises its expected price (and so its ask) by `SOLD_OUT_ASK_RAISE_SHARE`; the markdown of unsold stock was already there.

Not done:
- No whole-game run (about half an hour cold): the effect on idle hours, wage over floor, price over labour cost and on durable swings (Complaint 468) is unmeasured. A slow topic that runs the sim and prints those shares is the next step.
- In the economy fixture (no plot recipes) the unskilled wage falls to a few per cent of the floor in thirty years because demand is fixed by capacity and population is fixed; `test_economy_labour_core` now measures the trained-trade premium in units of the opening floor wage, not as a ratio of wages.
- Entry: with sellers raising asks until they no longer sell out, the price rises to clear and buyers are no longer turned away, so the "unmet demand" trigger in `entry.py` goes quiet exactly when margins are wide. Entry needs a margin trigger that does not chase one year's spike (the design in the round-four report); not rebuilt here.

Owner decision (2026-10-09): the labour wage floor is whatever is realistic: the lowest a worker's ask can fall is what keeping that worker's household alive and working costs (food, shelter, clothing, fuel), less what the household's own plot provides; below that people leave the trade, migrate or do not survive, rather than keep selling hours.


## Round six: the realistic floor, entry on a lasting margin, the decomposition figures

Done (fixtures only; `python3 -m sim.tests --only economy_labour_ask_floor,economy_entry,economy_entry_margin,economy_entry_trial,economy_diagnostics,asks_follow_sales`):
- Wage floor: the lowest a worker's ask falls to is the floors of every need in the basket at the tile's prices, for him and the people he supports, less what the family's plot grows (`wage_floor_per_worker_year` in `sim/economy/labour_ask_floor.py`). A family whose plot feeds it needs a wage only for the rest; one with no plot needs the whole basket. Below it people leave the trade, move or go short.
- Entry on a lasting margin (`sim/economy/entry_margin.py`): where makers exist, a market whose usual (smoothed) price has stood above its cheapest recipe's entry price (full cost with rent and the capital charge, plus a band) for as many years as a loser waits to exit draws newcomers. Size: a share of what the bids take at the entry price beyond capacity and plant coming (a floor stays a floor), no faster than incumbents change their own output, which is the Nerlove-style partial adjustment the round-four report asks for. It reads the usual price, not the last one, so a harvest spike draws nobody.
- No per-year cap: `entry.py`, the margin path and the trial path no longer stop at one newcomer per market a year; each recipe that pays takes a share of the part of the gap the better ones leave (Complaint 345's owner decision).
- Decomposition: `python3 sim/simulator.py economy-check` prints the median hired share, the unskilled wage, the wage floor, the wage over the floor and the staple's price over its labour cost (`sim/economy/diagnostics.py`; the outcome carries `wage_floor_per_hour`).
- Seed (395): wheat's yield is already net of the seed corn held back (`yield_basis` in `data/production/40_organics.json`), the other grains say the same; the seed share is a physical fact in the output.
- Wage against the household basket, not wheat alone (388): `wage_over_floor`.

Not done:
- Draught animals and their fodder as inputs of the plough crops (395). Plant goods would need the oxen as a held, priced capital good and fodder needs a good that does not exist in the data; an input would also take the crop out of households' own plots (`households_own.own_production_options` takes land-only recipes), which the wage floor above reads. Needs a design decision on how a farm holds and feeds its team, then data from Cato and Columella.
- Not measured on a whole game (about 45 minutes cold here): the effect on idle hours, wage over floor and price over labour cost, and on durable swings (Complaint 468). Run `python3 sim/simulator.py economy-check --civs rome_100ad --years 12`.
- Mineral entry kept only for a lasting, observed shortfall, and a gate on observed spending growth (the round-four report's list): the pace limit and the smoothed price stand in for them.
