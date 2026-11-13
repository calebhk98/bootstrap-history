"""Complaint 613: foot carriage is the porter trade's work and port handling the dockworker trade's, both named by the
route mode data, and both are in the transport occupation group."""

import dataclasses
import json
import os
import unittest

from sim.economy import carriage_hours
from sim.economy.setup import SetupTrade
from sim.economy.tile_costs import Haul
from sim.freight import rules as freight_rules
from sim.geography import api as geography, freight_cost
from sim.labour.api import occupation_groups
from sim.tests import economy_fixture as fixture
from sim.tests.test_carriage_hours_by_route import Hauls

QUICK_TOPIC = True

FOOT_RATE = 0.1
FOOT_HOURS = 0.5
PORT_HOURS = 2.0
PORTER, DOCKWORKER = "porter", "dockworker"


def setup(handling_trade=DOCKWORKER):
    built = fixture.small_setup(
        carriage_rates={"foot": FOOT_RATE, "sail": 0.02}, handling_rates={"sail": 3.0},
        carriage_crew={"foot": (PORTER, FOOT_HOURS), "sail": ("sailor", 0.02)},
        carriage_handling={"sail": PORT_HOURS})
    built.trades.update({PORTER: SetupTrade(PORTER), DOCKWORKER: SetupTrade(DOCKWORKER)})
    return dataclasses.replace(built, carriage_handling_trade={"sail": handling_trade} if handling_trade else {})


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


HELD_BY_A_SOCIETY_WITH_DRAUGHT_ANIMALS = ["lnd_ox_transport", "lnd_mule_transport", "lnd_two_wheel_cart"]


class LandCarriageMeansTests(unittest.TestCase):
    """Complaint 613: a mode is offered only where its means are held, so a society without draught animals carries
    overland on foot, with porters for crew; with them, the cheaper of the modes carries."""

    def test_a_society_holding_no_transport_node_can_use_foot_and_no_cart_pack_boat_or_ship(self):
        usable = set(geography.usable_modes([[]]))
        self.assertIn("foot", usable)
        self.assertFalse(usable & {"cart", "pack", "road", "river_boat", "canal", "sail"})

    def test_a_society_holding_the_draught_nodes_can_use_cart_and_pack_as_well(self):
        usable = set(geography.usable_modes([HELD_BY_A_SOCIETY_WITH_DRAUGHT_ANIMALS]))
        self.assertTrue({"foot", "cart", "pack"} <= usable)

    def test_mode_costs_keep_the_usable_modes_only(self):
        costs = {"foot": 3.0, "cart": 1.0, "pack": 2.0}
        self.assertEqual(freight_rules.usable_mode_costs(costs, ["foot"]), {"foot": 3.0})
        self.assertEqual(freight_rules.usable_mode_costs(costs, ["foot", "cart"]), {"foot": 3.0, "cart": 1.0})
        self.assertEqual(freight_rules.usable_mode_costs(costs, []), {})

    def test_the_porter_carrier_is_priced_by_its_crew_hours_and_has_no_vehicle(self):
        inputs = geography.porter_carrier("foot")["inputs"]
        wage = 2.0
        rate = freight_cost.freight_money_per_tonne_km(inputs, 1.0, wage, freight_cost.CarrierPrices(0.0), 0.05, 250.0, 0.0)
        self.assertAlmostEqual(rate, inputs.driver_hours_per_tonne_km * wage)
        self.assertIsNone(geography.porter_carrier("cart"))

    def test_a_cart_needs_far_fewer_crew_hours_a_tonne_km_than_porters(self):
        rates = geography.carriage_rates(["foot", "cart"])
        self.assertLess(rates["cart"]["crew_hours_per_tonne_km"], rates["foot"]["crew_hours_per_tonne_km"])

    def test_port_handling_hours_are_priced_at_the_dockworker_wage(self):
        from sim.markets import port_setup
        wages = {"labourer": 1.0, DOCKWORKER: 1.5}
        self.assertEqual(port_setup.handling_wage(wages, DOCKWORKER, "labourer"), 1.5)

    def test_port_handling_falls_back_to_the_unskilled_wage_without_a_quote(self):
        from sim.markets import port_setup
        self.assertEqual(port_setup.handling_wage({"labourer": 1.0}, DOCKWORKER, "labourer"), 1.0)
        self.assertEqual(port_setup.handling_wage({"labourer": 1.0}, None, "labourer"), 1.0)


if __name__ == "__main__":
    unittest.main()
