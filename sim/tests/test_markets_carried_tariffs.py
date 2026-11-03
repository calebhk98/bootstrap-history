"""`port_duty.carried_tariffs`: the tariff share toward each other country of the economy."""
QUICK_TOPIC = True

import unittest

from sim.markets.port_duty import carried_tariffs

class CarriedTariffs(unittest.TestCase):
    def test_each_economy_country_with_a_tariff_on_it_is_listed_by_source_and_the_home_country_and_untaxed_ones_are_left_out(self):
        self.assertEqual(carried_tariffs(("home", "north", "south", "east"), "home", lambda country: {"north": 0.25, "east": 1.0}.get(country, 0.0)),
                         {"north": 0.25, "east": 1.0})

    def test_the_home_country_is_not_a_source(self):
        self.assertEqual(carried_tariffs(("home",), "home", lambda country: 0.5), {})
