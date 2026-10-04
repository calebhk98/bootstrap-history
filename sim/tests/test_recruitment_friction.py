"""A big hire is slower and dearer per head than a small one, and scarcer skills are harder to find
(complaint 271). Stub world, no Sim; invented trade ids."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.labour.labour_market_api import LabourMarket

HOURS = 2000.0
POOLS = {"common": 5000.0, "rare": 30.0}


class StubLabour:
    def __init__(self, world):
        self._world = world

    def market_supply(self, trade):
        extra = self._world.state.household.employees.get(trade, 0.0)
        return (POOLS[trade] + extra) * HOURS

    def wage_schedule(self):
        return SimpleNamespace(training_years={"gleaner": 0.0, "common": 1.0, "rare": 8.0})

    def base_annual_wage(self, trade):
        return 100.0

    def wage_cost_factors(self, trade):
        return {"weighted": 1.0}


def stub_market():
    household = SimpleNamespace(labour_pressure_records={}, employees={})
    world = SimpleNamespace(
        state=SimpleNamespace(household=household, scenario=SimpleNamespace(year=0)),
        HOURS_PER_PERSON_YEAR=HOURS, wages={"gleaner": 1, "common": 1, "rare": 1},
        trade_family=lambda trade: "craft", price_index=1.0, wage_index=1.0,
        actor_staff_fte=lambda trade: 0.0,
        economy=SimpleNamespace(agent_wage_per_hour=lambda trade: 0.05))
    return LabourMarket(StubLabour(world))


market = stub_market()
check("one person in an ample market is found", market.whole_recruits("common", 1) == 1)
check("one person is found even in a thin market", market.whole_recruits("rare", 1) == 1)
check("one person costs the going rate",
      abs(market.hire_cost("common", 1) - market.unscarce_annual("common") * market.price_factor("common")) < 1e-9)

check("a small hire in an ample market is filled", market.whole_recruits("common", 3) == 3)
check("a big hire in a thin market finds fewer than asked", market.whole_recruits("rare", 20) < 20)
check("the same big hire is found in full in the common trade", market.whole_recruits("common", 20) == 20)

per_head_one = market.hire_cost("rare", 1)
per_head_many = market.hire_cost("rare", 10) / 10
check("ten of a rare trade cost more per head than one", per_head_many > per_head_one * 1.001,
      (per_head_one, per_head_many))
check("a big hire of the common trade is cheaper per head than of the rare one",
      market.hire_cost("common", 20) / 20 < market.hire_cost("rare", 20) / 20)

check("a premium finds more people", market.whole_recruits("rare", 20, 0.5) > market.whole_recruits("rare", 20))
check("a premium costs more", market.hire_cost("rare", 5, 0.5) > market.hire_cost("rare", 5))
check("nothing asked costs nothing and finds nobody",
      market.hire_cost("rare", 0) == 0.0 and market.whole_recruits("rare", 0) == 0)
