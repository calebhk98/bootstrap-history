"""Complaints/627: a haul's crew hours follow the modes the haul travels (a sea leg hires sailor hours), a
handled port adds handling hours, and the hours are bid and paid at the area the goods leave."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.economy import carriage_hours, merchants
from sim.economy.market_memory import market_key
from sim.economy.merchants import Merchant
from sim.economy.setup import labour_area
from sim.economy.tile_costs import Haul
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_merchants import SPECS, merchant, plan, world

CART_RATE = 0.1
SAIL_RATE = 0.02
CART_HOURS = 0.05
SAIL_HOURS = 0.02
PORT_HOURS = 2.0
PORT_MONEY = 3.0


class Hauls:
    """A carriage table that answers one haul for every pair."""

    def __init__(self, haul):
        self.answer = haul

    def haul(self, _source, _destination):
        return self.answer


def sea_setup():
    return fixture.small_setup(
        carriage_rates={"cart": CART_RATE, "sail": SAIL_RATE}, handling_rates={"sail": PORT_MONEY},
        carriage_crew={"cart": ("carter", CART_HOURS), "sail": ("sailor", SAIL_HOURS)},
        carriage_handling={"sail": PORT_HOURS})


def by_trade(setup, haul, imbalance=1.0):
    return carriage_hours.Crew(setup, Hauls(haul), imbalance).hours_by_trade("a", "b")


# a cart to the port, the sea, a cart from it: 4 of cart money, 10 of sea money and the port's handling
SEA_HAUL = Haul(30.0, (("cart", 4.0 + 1.0), ("sail", 10.0 + PORT_MONEY)), (("cart", 1), ("sail", 1)))
CART_HAUL = Haul(3.0, (("cart", 4.0),), (("cart", 1),))


class SailorHoursTests(unittest.TestCase):
    def test_a_sea_haul_hires_sailor_hours_over_the_tonne_km_its_sea_money_stands_for(self):
        hours = by_trade(sea_setup(), SEA_HAUL)
        self.assertAlmostEqual(hours["sailor"], 10.0 / SAIL_RATE * SAIL_HOURS * 2.0)

    def test_the_land_legs_of_the_same_haul_hire_carter_hours(self):
        hours = by_trade(sea_setup(), SEA_HAUL)
        self.assertAlmostEqual(hours["carter"], 5.0 / CART_RATE * CART_HOURS * 2.0)

    def test_a_haul_by_land_hires_no_sailors(self):
        self.assertNotIn("sailor", by_trade(sea_setup(), CART_HAUL))

    def test_the_hours_are_bid_in_the_trade_where_the_goods_leave(self):
        rows = carriage_hours.Crew(sea_setup(), Hauls(SEA_HAUL), 1.0).hours_per_tonne("a", "b")
        self.assertEqual({key for key, _hours in rows},
                         {market_key("sailor", "a"), market_key("carter", "a"), market_key(fixture.LABOURER, "a")})


class PortHandlingTests(unittest.TestCase):
    def test_a_handled_port_adds_its_handling_hours_in_the_unskilled_trade(self):
        hours = by_trade(sea_setup(), SEA_HAUL)
        self.assertAlmostEqual(hours[fixture.LABOURER], PORT_HOURS)      # the legs' crews are carters and sailors

    def test_handling_hours_are_counted_for_each_change_to_the_mode(self):
        twice = Haul(30.0, (("cart", 5.0), ("sail", 10.0 + 2 * PORT_MONEY)), (("cart", 1), ("sail", 2)))   # the same legs, a second port
        gap = by_trade(sea_setup(), twice)[fixture.LABOURER] - by_trade(sea_setup(), SEA_HAUL)[fixture.LABOURER]
        self.assertAlmostEqual(gap, PORT_HOURS)

    def test_the_money_of_a_handling_is_not_counted_as_a_legs_crew_hours(self):
        hours = by_trade(sea_setup(), Haul(30.0, (("sail", PORT_MONEY),), (("sail", 1),)))
        self.assertNotIn("sailor", hours)
        self.assertAlmostEqual(hours[fixture.LABOURER], PORT_HOURS)

    def test_a_mode_whose_handling_the_rates_do_not_price_has_no_handling_hours(self):
        hours = by_trade(sea_setup(), CART_HAUL)
        self.assertNotIn(fixture.LABOURER, hours)
        self.assertAlmostEqual(hours["carter"], 4.0 / CART_RATE * CART_HOURS * 2.0)


class AreaWageTests(unittest.TestCase):
    def test_a_shipment_is_paid_the_wage_of_the_area_it_leaves(self):
        carriage, _area_map, area_a, _area_b = world()
        who = merchant()
        plan(who, 2.0, 5.0)
        key_a = market_key(fixture.LABOURER, "a")
        key_b = market_key(fixture.LABOURER, "b")
        crew = merchants.CrewHire(lambda source, _destination: (((key_a if source == "a" else key_b), 0.5),),
                                  {key_a: 100.0, key_b: 100.0}, {key_a: 0.4, key_b: 0.9},
                                  lambda _key: 1.0, lambda _good, tile: "area_" + tile)
        result = merchants.dispatch(who, (), carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0}, crew=crew)
        self.assertAlmostEqual(result.transfers[0].amount, 10.0 - 10.0 * 0.5 * 0.4)       # ten units, half an hour each, 0.4 an hour

    def test_the_wage_scale_follows_the_area_the_flow_leaves_and_not_a_wage_elsewhere(self):
        setup = fixture.small_setup(carriage_rates={"cart": CART_RATE}, carriage_crew={"cart": (fixture.LABOURER, CART_HOURS)},
                                    carriage_wage=1.0)
        table = setup.carriage_table()
        carried = {fixture.TOWN: {fixture.FARMS: 5.0}}

        def scale(town_wage, farms_wage):
            wages = {market_key(fixture.LABOURER, labour_area(fixture.TOWN)): town_wage,
                     market_key(fixture.LABOURER, labour_area(fixture.FARMS)): farms_wage}
            record = type("Record", (), {"memory": type("Memory", (), {"wages": wages})(), "carried": carried,
                                         "area_imbalance": 1.0})()
            return carriage_hours.wage_scale(setup, record, table)
        self.assertEqual(scale(1.0, 9.0), 1.0)
        self.assertEqual(scale(1.0, 0.1), 1.0)
        self.assertGreater(scale(2.0, 1.0), 1.0)
        self.assertLess(scale(0.5, 1.0), 1.0)

    def test_hours_hired_in_a_shared_market_are_shared_by_the_hours_wanted(self):
        who = Merchant("m1", "town", "owner", 1.0)
        who.carriage_hours_wanted = {market_key(fixture.LABOURER, "hills"): 30.0, market_key(fixture.LABOURER, "farms"): 10.0}
        record = type("Record", (), {"cohorts": {"c": type("Cohort", (), {"tile": "town"})()}})()      # nobody lives on hills or farms
        index = {("m1", fixture.LABOURER, labour_area("town")): (20.0, 10.0)}
        hours, wages = carriage_hours.engaged(record, who, index)
        self.assertAlmostEqual(hours[market_key(fixture.LABOURER, "hills")], 15.0)
        self.assertAlmostEqual(hours[market_key(fixture.LABOURER, "farms")], 5.0)
        self.assertAlmostEqual(wages[market_key(fixture.LABOURER, "hills")], 0.5)


if __name__ == "__main__":
    unittest.main()
