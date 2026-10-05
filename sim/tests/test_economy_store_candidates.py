"""Which goods households hold as a store of wealth, and in what proportion."""
import math
import unittest

from sim.economy.households_store import store_candidates
from sim.economy.types import GoodSpec

STAPLE_PRICE_PER_KG = 0.3


def spec(good, mass=1.0, spoilage=0.0, life=50.0):
    return GoodSpec(good, mass, spoilage, life, "test")


class StoreCandidateTests(unittest.TestCase):
    def test_the_denser_of_two_equal_goods_gets_more_weight(self):
        specs = {"dense": spec("dense", mass=1.0), "bulky": spec("bulky", mass=5.0)}
        prices = {"dense": 500.0, "bulky": 500.0}
        weights = store_candidates(specs, prices, STAPLE_PRICE_PER_KG)
        self.assertGreater(weights["dense"], weights["bulky"])

    def test_unfit_goods_are_left_out(self):
        specs = {"fit": spec("fit"), "spoils": spec("spoils", spoilage=0.2),
                 "massless": spec("massless", mass=math.inf), "used_up": spec("used_up", life=0.0),
                 "cheap": spec("cheap")}
        prices = {"fit": 500.0, "spoils": 500.0, "massless": 500.0, "used_up": 500.0, "cheap": 1.0}
        self.assertEqual(list(store_candidates(specs, prices, STAPLE_PRICE_PER_KG)), ["fit"])

    def test_weights_sum_to_one(self):
        specs = {"a": spec("a"), "b": spec("b", life=10.0), "c": spec("c", mass=2.0)}
        prices = {"a": 500.0, "b": 400.0, "c": 900.0}
        self.assertAlmostEqual(sum(store_candidates(specs, prices, STAPLE_PRICE_PER_KG).values()), 1.0)

    def test_no_candidates_gives_an_empty_dict(self):
        self.assertEqual(store_candidates({"a": spec("a", life=0.0)}, {"a": 500.0}, STAPLE_PRICE_PER_KG), {})
        self.assertEqual(store_candidates({}, {}, STAPLE_PRICE_PER_KG), {})


if __name__ == "__main__":
    unittest.main()
