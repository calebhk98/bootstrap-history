# Labour is mostly idle and prices sit far above cost on the agent economy

**Status:** open

In every civilisation only a small share of the hours households offer is hired, and the rest go unhired or to own plots, so the unskilled wage sits at the workers' ask (the family's subsistence floor per offered hour) almost everywhere. Wages are a small part of household income; most of it is property income (dividends) and food grown for itself. At the same time goods sell far above the cost of the labour in them, with little land rent, and few makers enter. An economy with idle hands, free land and wide margins is not in competition: entry fires only where buyers are turned away (`sim/economy/entry.py`), so incumbents keep their margins and pay them out as dividends.

This, not the wage rule, is what Complaint 388 measures: the wage in kg of wheat is the subsistence basket's cost over the wheat price. Wheat is a minor and dear food in Rome and Mexica, so the wheat wage reads low there; in food-need units the civilisations are close. Mexica also has no maize good in the data.

Evidence: shares of hours hired, wage over floor and price over labour cost were measured by decomposition scripts in a scratch directory (not committed; no command prints them yet). The figures are in Complaints/reports/agent-economy-review.md. `python3 sim/economy_validate.py` shows the wheat wage.

What it would take:
- Entry that competes margins away without chasing one-year price spikes (an entry-on-price rule was tried; see the review report).
- Recipes with their full inputs, so that labour cost is a fair floor (Complaint 395).
- A validation wage measured against the household basket, not wheat alone (`sim/economy_validate.py`).

Related: 388, 393, 395.
