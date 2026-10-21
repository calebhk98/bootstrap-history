# A country's state originates no research: what research costs and the labour quote its plan prices hours at are the founder's

**Status:** open

Follow-up to Complaint 649. The hands a country's actor can put on research are now its own country's people by trade
(`CountryCrewView.research_hands`), but `Government.researches` (`sim/agents/government.py`) is still true for the home state alone, so
a country's state copies research it sees and does not originate it. Turning it on would price the work at home figures:

- `research_cost` and `copy_cost` (`sim/engine/agents_port_research.py`, `agents_port.py`) walk the founder's materials and labour at
  home prices, and `research.plan` subtracts a labour bill priced by `world.labour_market.quote`, which a `CountryWorld` forwards to
  the home market (firms of a country already research on this path).
- `Actor.copy_budget` is read in the founder's money.

**What it would take.** A country-scoped research cost (the node's materials at the country's prices, its hours at the country's pay)
and a country-scoped labour quote on `CountryWorld`; then `researches` is true for every government. Test: a country's state given its
own prices and pay prices a node from them and begins it (`sim/tests/test_country_research_hands.py` is where the hands checks are).
