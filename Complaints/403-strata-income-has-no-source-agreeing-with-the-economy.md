# Bodies of people earn from figures that disagree with each other: the agent economy's cohorts are not reachable

**Status:** open

Strata (`sim/agents/stratum.py`, `stratum_year.py`) take wage income as members times a working
share times `world.pay_per_person_year(trade)`. Property income is `world.society_output()` times a
property share. Food is `world.subsistence_cost_per_person_year()` (`sim/engine/agents_port_cast.py`).
In a Rome start these three disagree:

- A labourer's yearly pay is below one person's subsistence food. Complaint 388 already reports
  low unskilled wages in Rome.
- Society output per head is many times that pay.

So landless strata starve at the engine's wage, and a stratum with property income is rich beyond any
record. Strata with land have a floor: own-plot subsistence, the rule `sim/economy/year_labour.py`
uses for its outside option.

Measure it with a Rome game: run `advance_actors` for a few years and print each `stratum:*` record's
`shortfall`, `last_growth` and `money`. There is no command for this yet.

The agent economy already keeps household cohorts by tile and income class, with people, income and
the floors of their needs (`sim/economy/households_cohort.py`, `households_basket.py`). Strata ask
`world.observed_stratum(country, name)` for exactly this and use it in place of their own books. The
adapter returns None today because only `sim/engine/economy_port*.py` may reach `sim/economy/`.

What it would take:
- An economy-port member summarising cohorts by income class for the home country: people, income,
  and the cost of their need floors.
- A mapping from income classes to stratum names (data, beside the strata definitions).
- `observed_stratum` answering from that mapping.
