# Labour is mostly idle and prices sit far above cost on the agent economy

**Status:** partly - producers now sit where labour is, losers exit and plantless capacity follows use (round four); margins on goods with makers are still not competed away

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
