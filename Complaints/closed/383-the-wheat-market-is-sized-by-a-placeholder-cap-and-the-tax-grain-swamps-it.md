# The wheat market is sized by a placeholder cap, so the state's tax grain swamps it and farm output collapses

**Status:** closed - the agent economy is the default: every market is sized by producers' real output and the state's tax grain is held and spent through the markets, not dumped as a price-taker (regression in sim/tests/test_agent_economy_wiring.py)

Rome, seed 1. The state's land tax takes a tenth of the harvest in wheat (`data/civilizations/rome_100ad.json`, form `land_tax`). It sells what its budget lines will not draw (`sim/engine/actors/government_stores.py`, `sell_surplus`), as a price-taker, through `world.market_sale`. The harvest is the farm model's whole gross harvest (`harvest_tonnes`, `sim/engine/actors/world_revenue.py`).

The wheat market book opens at `_society_output_tonnes`, which for wheat falls through to `_generic_national_output_uncached` (`sim/engine/economy_materials.py`). That formula, for a cheap material, binds at `GENERIC_OUTPUT_CEILING_T_PER_YR`, a defensive cap labelled as not fitted. Household demand is sized from that reference too. The state's tax grain alone is several times the whole reference market.

The result:
- Wheat clears at the price floor every year.
- Society farm capacity in the book shrinks toward zero, and unsold stock piles up.

The book and the farm model never reconcile. The harvest is not the market's supply, and the tax grain is a second seller of grain the farmers already grew.

Evidence: the probe below prints the book entry and who sold wheat for the first five years.

```
python3 - <<'EOF'
import random, sys
sys.argv = ["x"]
from sim import simulator as S
TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_L, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
sim = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
sim.goal, sim.done_year = GOAL, {}
for year in range(5):
    sim.step()
    print(sim.state.economy.market_book["wheat_kg"], sim.state.economy.market_flows.get("sold", {}).get("wheat_kg"))
EOF
```

Wheat is also the food price the subsistence wage floor is built from, so the cap leaks into every wage.

What it would take: a market's size comes from what producers actually make (the farm model's harvest is the wheat producers' output). The tax grain is a transfer out of that output into the state's stores, not added supply. The new economy does both; a regression test checks that wheat clears off the floor with the state selling its tax grain.

Related: 102, 135, 375, 315.
