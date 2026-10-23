"""Complaint 564, the wiring: the floors the seat's household is billed are the economy's floors at its tile, in the economy's coin,
and a founder and a cohort household of the same size pay the same. Called on the fixture economy and a stand-in port; no game."""
import types
import unittest

from sim.economy import api as economy_api
from sim.economy import households
from sim.economy.api import country_figures
from sim.engine.economy_household_bill import HouseholdBillMixin
from sim.engine.economy_port_year import AgentEconomy
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = True

COIN_PER_UNIT = 3.0


def cohort_floor_per_person(economy, tile):
    view = country_figures._floor_view(economy)
    return economy.setup.coin_per_unit * sum(need.price_index * need.spec.subsistence_per_person
                                              for need in households.need_prices(economy.setup.basket_for(tile), view, tile))


class SeatFloorsTests(unittest.TestCase):
    def setUp(self):
        self.economy = economy_api.blank_economy(fixture.small_setup(coin_per_unit=COIN_PER_UNIT))
        self.port = types.SimpleNamespace(economy=lambda: self.economy)

    def test_the_seats_floors_are_the_economys_floors_at_its_tile_in_its_coin(self):
        floors = AgentEconomy.need_floor_costs_at_tile(self.port, fixture.TOWN)
        expected = cohort_floor_per_person(self.economy, fixture.TOWN)
        self.assertGreater(expected, 0.0)
        self.assertAlmostEqual(sum(floors.values()), expected, delta=1e-9 * expected)

    def test_a_founder_and_a_cohort_household_of_the_same_size_pay_the_same(self):
        floors = AgentEconomy.need_floor_costs_at_tile(self.port, fixture.TOWN)
        game = types.SimpleNamespace(
            economy=types.SimpleNamespace(agent_need_floor_costs_at=lambda: floors),
            household_dependant_people=lambda: 2.0)
        game.household_need_floors_per_person = lambda: HouseholdBillMixin.household_need_floors_per_person(game)
        game.household_bill_per_person = lambda: HouseholdBillMixin.household_bill_per_person(game)
        people = 1.0 + game.household_dependant_people()
        paid = game.household_bill_per_person() * people
        expected = people * cohort_floor_per_person(self.economy, fixture.TOWN)
        self.assertAlmostEqual(paid, expected, delta=1e-9 * expected)


if __name__ == "__main__":
    unittest.main()
