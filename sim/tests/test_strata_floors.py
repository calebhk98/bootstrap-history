"""A stratum pays the floor of each need in turn, at the costs the world reports for them."""
import unittest

from sim.agents.api import ActorRegistry, ActorsState, CountryProfile
from sim.agents.strata_seed import strata_spawner

from .agents_fake_world import FakeWorld


class FloorWorld(FakeWorld):
    def __init__(self, floor_costs):
        super().__init__()
        self.floor_costs = floor_costs

    def need_floor_costs_per_person_year(self):
        return dict(self.floor_costs)

    def subsistence_cost_per_person_year(self):
        return self.floor_costs["food"]

    def pay_per_person_year(self, trade):
        return 0.0

    def observed_stratum(self, country, name):
        return None


def run_one_year(money, floor_costs):
    state = ActorsState(home_country="home")
    state.countries["home"] = CountryProfile(
        country="home", population=100.0, strata=[{"name": "body", "share": 1.0, "literacy": 0.1}])
    registry = ActorRegistry(state)
    world = FloorWorld(floor_costs)
    strata_spawner(registry, world)
    body = registry.actors["stratum:home:body"]
    body.record.money = body.record.allowance = money
    registry.advance(world)
    return body.record


FLOORS = {"food": 100.0, "shelter": 40.0, "clothing": 10.0}


class StratumFloorsTest(unittest.TestCase):
    def test_a_stratum_whose_money_covers_the_floors_has_no_shortfall(self):
        record = run_one_year(100.0 * sum(FLOORS.values()) * 2.0, FLOORS)
        self.assertEqual(record.shortfall, {"food": 0.0, "shelter": 0.0, "clothing": 0.0})

    def test_shortfall_never_rises_with_money(self):
        previous = None
        for money in (0.0, 2000.0, 8000.0, 12000.0, 15000.0, 40000.0):
            shortfall = run_one_year(money, FLOORS).shortfall
            if previous is not None:
                for need_id, unmet in shortfall.items():
                    self.assertLessEqual(unmet, previous[need_id] + 1e-12)
            previous = shortfall

    def test_food_is_paid_before_the_other_floors(self):
        record = run_one_year(100.0 * FLOORS["food"], FLOORS)
        self.assertEqual(record.shortfall["food"], 0.0)
        self.assertEqual(record.shortfall["shelter"], 1.0)

    def test_welfare_falls_when_a_need_gets_dearer(self):
        cheap = run_one_year(8000.0, FLOORS).welfare
        dear = run_one_year(8000.0, dict(FLOORS, food=FLOORS["food"] * 2.0)).welfare
        self.assertLess(dear, cheap)


if __name__ == "__main__":
    unittest.main()
