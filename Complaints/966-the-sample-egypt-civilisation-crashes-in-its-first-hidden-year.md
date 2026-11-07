# The sample Egypt civilisation crashes in its first hidden year

**Status:** open - found while timing every civilisation's year on branch speed-year-step-and-openings; not investigated

`sample_egypt_100bc_e7k2:egypt` is a mod civilisation with no shipped opening, so a new game runs its own spin-up, and
the first hidden year raises `KeyError: 'meat_kg'` in `MarketAreaMap.area_of` (`sim/economy/market_areas.py`), reached
from `year_close.close_agents` through `expected_sales.market_capacities`. The good has no bucket in the area map, so
some producer or market names a good the map was not built for.

Reproduce (a cold opening, so it takes minutes):

    printf '{"cmd":"state"}\n{"cmd":"quit"}\n' | python3 sim/simulator.py agent --civ sample_egypt_100bc_e7k2:egypt --seed 1

**Why it matters.** A mod civilisation that cannot open is a scenario no player can start, and `civs` still lists it.

**What it would take.** Find which producer, recipe or market carries `meat_kg` into `market_capacities` without a
market-area bucket (the area map is built from the goods the setup declares), then a regression test on the smallest
setup that carries a good the map lacks.
