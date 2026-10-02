# Harvest weather is the same in every game of a civilisation, whatever the seed

**Status:** open - waiting on an owner decision: changing it moves every recorded fingerprint

The harvest weather draw is seeded only by the civilisation id, the weather cell and the calendar year (`Sim._farm_year_weather_seed`, `sim/engine/core.py`). The docstring explains why it is a pure function: so that a year draws the same weather whether it is reached in one run or across many `--session` commands. The game's own seed (`--seed`, kept in the save as `_seed`) does not enter it. So every game of a civilisation replays one fixed sequence of good and bad harvests.

Why it matters:
- CLAUDE.md 4.2 asks for the historical record to be one plausible draw from an ensemble of baseline runs. With weather fixed per civilisation there is no ensemble of harvests: every seed gets the same famines in the same years.
- The agent economy's validation (`python3 sim/economy_validate.py --seeds 1,2,3`) shows identical results for different seeds, because harvest weather is the main source of yearly variation in its prices.

Evidence: `python3 sim/economy_validate.py --years 15 --seeds 1,2 --civs <civilisation>` prints the same row for both seeds.

What it would take: mix the game seed into `_farm_year_weather_seed`. It stays a pure function of saved values (seed, civilisation, cell, year), so a resumed game still draws the same weather as an unbroken one. Every fingerprint baseline would need recording again.

Related: 46, 49, 266.
