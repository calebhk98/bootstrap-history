"""A held durable good's service counts in its return: what its yearly use would cost to buy anew."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy.households_store import store_candidates
from sim.economy.store_return import carrying_return, service_values_per_year
from sim.economy.types import GoodSpec

PLATE_PRICE = 600.0
PLATE_EFFECT = 1.0


def spec(good, life=50.0):
    return GoodSpec(good, 1.0, 0.0, life, "test")


def display_need(price_index, goods):
    """A priced need standing in for the real one: only its price index and goods are read."""
    return SimpleNamespace(price_index=price_index,
                           goods=tuple((good, price, effect, 1.0 / len(goods)) for good, price, effect in goods))


class StoreServiceTests(unittest.TestCase):
    def test_a_good_that_meets_a_need_is_worth_its_effect_over_its_life_at_the_needs_price(self):
        need = display_need(PLATE_PRICE, [("plate", PLATE_PRICE, PLATE_EFFECT)])
        values = service_values_per_year([need], {"plate": spec("plate", life=50.0)})
        self.assertAlmostEqual(values["plate"], PLATE_PRICE * PLATE_EFFECT / 50.0)

    def test_a_good_that_meets_no_need_has_no_service(self):
        need = display_need(PLATE_PRICE, [("plate", PLATE_PRICE, PLATE_EFFECT)])
        self.assertNotIn("bar", service_values_per_year([need], {"bar": spec("bar"), "plate": spec("plate")}))

    def test_a_used_up_good_has_no_held_service(self):
        need = display_need(PLATE_PRICE, [("plate", PLATE_PRICE, PLATE_EFFECT)])
        self.assertEqual(service_values_per_year([need], {"plate": spec("plate", life=0.0)}), {})

    def test_service_raises_the_return_by_its_share_of_the_price(self):
        plain = carrying_return(spec("plate"), PLATE_PRICE, None)
        served = carrying_return(spec("plate"), PLATE_PRICE, None, service_value=12.0)
        self.assertAlmostEqual(served - plain, 12.0 / PLATE_PRICE)

    def test_the_dearer_good_gains_less_service_per_unit_of_value(self):
        # both serve the need alike per kilogram, and the need is priced at the cheaper good's price
        need = display_need(300.0, [("cheap", 300.0, 1.0), ("dear", 3000.0, 1.0)])
        specs = {"cheap": spec("cheap"), "dear": spec("dear")}
        values = service_values_per_year([need], specs)
        weights = store_candidates(specs, {"cheap": 300.0, "dear": 3000.0}, 0.3, service_values=values)
        self.assertGreater(weights["cheap"], weights["dear"])


if __name__ == "__main__":
    unittest.main()
