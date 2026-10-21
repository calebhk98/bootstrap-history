"""Complaint 613: foot carriage is the porter trade's work and port handling the dockworker trade's, both named by the
route mode data, and both are in the transport occupation group."""

import json
import os
import unittest

from sim.economy import carriage_hours
from sim.economy.setup import TradeSpec
from sim.economy.tile_costs import Haul
from sim.geography import api as geography
from sim.labour.api import occupation_groups
from sim.tests import economy_fixture as fixture
from sim.tests.test_carriage_hours_by_route import Hauls

FOOT_RATE = 0.1
FOOT_HOURS = 0.5
PORT_HOURS = 2.0
PORTER, DOCKWORKER = "porter", "dockworker"


def setup(handling_trade=DOCKWORKER):
    built = fixture.small_setup(
        carriage_rates={"foot": FOOT_RATE, "sail": 0.02}, handling_rates={"sail": 3.0},
        carriage_crew={"foot": (PORTER, FOOT_HOURS), "sail": ("sailor", 0.02)},
        carriage_handling={"sail": PORT_HOURS})
    built.trades.update({PORTER: TradeSpec(PORTER), DOCKWORKER: TradeSpec(DOCKWORKER)})
    built.carriage_handling_trade = {"sail": handling_trade} if handling_trade else {}
    return built


def hours(built, haul):
    return carriage_hours.Crew(built, Hauls(haul), 0.0).hours_by_trade("a", "b")


class PorterAndDockworkerTests(unittest.TestCase):
    def test_foot_carriage_hours_are_booked_to_the_porter_trade(self):
        booked = hours(setup(), Haul(5.0, (("foot", 5.0),), (("foot", 1),)))
        self.assertAlmostEqual(booked[PORTER], 5.0 / FOOT_RATE * FOOT_HOURS)
        self.assertNotIn(fixture.LABOURER, booked)

    def test_port_handling_hours_are_booked_to_the_dockworker_trade(self):
        booked = hours(setup(), Haul(3.0, (("sail", 3.0),), (("sail", 2),)))
        self.assertAlmostEqual(booked[DOCKWORKER], 2 * PORT_HOURS)

    def test_a_mode_with_no_handling_trade_is_handled_by_the_unskilled_trade(self):
        booked = hours(setup(None), Haul(3.0, (("sail", 3.0),), (("sail", 1),)))
        self.assertAlmostEqual(booked[fixture.LABOURER], PORT_HOURS)

    def test_the_route_mode_data_names_both_trades(self):
        rates = geography.carriage_rates(["foot", "sail"])
        self.assertEqual(rates["foot"]["crew_trade"], PORTER)
        self.assertEqual(rates["sail"]["handling_trade"], DOCKWORKER)

    def test_both_trades_are_in_the_registry_and_the_transport_group(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "world", "trades.json")
        with open(path) as handle:
            registry = json.load(handle)["trades"]
        group = occupation_groups()["groups"]["transport"]["trades"]
        for trade in (PORTER, DOCKWORKER):
            self.assertIn(trade, registry)
            self.assertIn(trade, group)


if __name__ == "__main__":
    unittest.main()
