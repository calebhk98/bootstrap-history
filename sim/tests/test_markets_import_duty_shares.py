"""`port_duty.import_duty_shares`: the share of a landed good's price that is the home state's tariff, per good."""
QUICK_TOPIC = True

import unittest

from sim.markets.port_duty import carried_tariffs, import_duty_shares

TARIFFS = {"north": 0.25, "south": 0.0, "east": 1.0}


def leg(partner, material, tonnes, kind="in"):
    return {"id": "cargo:%s:%s:%s" % (partner, material, kind), "kind": kind, "partner": partner, "material": material,
            "tonnes": tonnes}


class CarriedTariffs(unittest.TestCase):
    def test_each_economy_country_with_a_tariff_on_it_is_listed_by_source_and_the_home_country_and_untaxed_ones_are_left_out(self):
        self.assertEqual(carried_tariffs(("home", "north", "south", "east"), "home", lambda country: {"north": 0.25, "east": 1.0}.get(country, 0.0)),
                         {"north": 0.25, "east": 1.0})

    def test_the_home_country_is_not_a_source(self):
        self.assertEqual(carried_tariffs(("home",), "home", lambda country: 0.5), {})


class ImportDutyShares(unittest.TestCase):

    def test_a_tariff_on_the_value_at_the_source_is_that_share_of_the_landed_price_over_one_plus_it(self):
        shares = import_duty_shares([leg("north", "iron_kg", 10.0)], TARIFFS.get)
        self.assertAlmostEqual(shares["iron_kg"], 0.25 / 1.25)

    def test_a_good_landed_from_two_countries_has_the_tonnes_weighted_mean_share(self):
        shares = import_duty_shares([leg("north", "iron_kg", 3.0), leg("east", "iron_kg", 1.0)], TARIFFS.get)
        self.assertAlmostEqual(shares["iron_kg"], (3.0 * 0.2 + 1.0 * 0.5) / 4.0)

    def test_a_good_with_no_tariff_on_it_is_left_out(self):
        self.assertEqual(import_duty_shares([leg("south", "iron_kg", 5.0)], TARIFFS.get), {})

    def test_cargo_taken_abroad_or_carried_between_other_countries_pays_no_duty_here(self):
        legs = [leg("north", "iron_kg", 5.0, kind="out"), leg("north", "iron_kg", 5.0, kind="through")]
        self.assertEqual(import_duty_shares(legs, TARIFFS.get), {})
