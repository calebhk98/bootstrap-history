"""Complaint 564, the wiring: the floors the seat's household is billed are the economy's floors at its tile, in the economy's coin,
and the bill of a person is the sum of those floors, the figure a cohort household of the same size pays. Called on stand-ins whose
figures are written out; no game and no economy."""
import types
import unittest
from unittest import mock

from sim.engine.economy_household_bill import HouseholdBillMixin
from sim.engine.economy_port_year import AgentEconomy

QUICK_TOPIC = True

COIN_PER_UNIT = 3.0
FLOORS_IN_ECONOMY_UNITS = {"food": 10.0, "shelter": 4.0}


class SeatFloorsTests(unittest.TestCase):
    def test_the_seats_floors_are_the_economys_floors_at_its_tile_in_its_coin(self):
        economy = types.SimpleNamespace(setup=types.SimpleNamespace(coin_per_unit=COIN_PER_UNIT))
        port = types.SimpleNamespace(economy=lambda: economy)
        with mock.patch("sim.engine.economy_port_year.economy_api.country_figures.tile_need_floor_costs",
                        return_value=dict(FLOORS_IN_ECONOMY_UNITS)) as floors_at:
            floors = AgentEconomy.need_floor_costs_at_tile(port, "town")
        floors_at.assert_called_once_with(economy, "town")
        self.assertEqual(floors, {"food": 30.0, "shelter": 12.0})

    def test_a_persons_bill_is_the_sum_of_the_floors_so_founder_and_cohort_households_of_one_size_pay_alike(self):
        game = types.SimpleNamespace(household_need_floors_per_person=lambda: {"food": 30.0, "shelter": 12.0})
        bill = HouseholdBillMixin.household_bill_per_person(game)
        people = 3.0
        self.assertAlmostEqual(bill * people, people * sum({"food": 30.0, "shelter": 12.0}.values()))
        self.assertEqual(bill, 42.0)


if __name__ == "__main__":
    unittest.main()
