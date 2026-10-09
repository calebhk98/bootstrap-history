"""The usual price holders compare a durable good's price with: remembered slowly, read by the store."""

QUICK_TOPIC = True

import unittest

from sim.economy import households_basket
from sim.economy.households_store import store_holding
from sim.economy.market_memory import USUAL_PRICE_SPEED, MarketMemory
from sim.economy.types import GoodSpec
from sim.tests import economy_store_view as store_view

OTHER = "other_durable_kg"


class UsualPriceMemoryTests(unittest.TestCase):
    def test_it_starts_at_the_first_price_and_follows_later_prices_slowly(self):
        memory = MarketMemory(prices={"k": 10.0})
        memory.note_usual_price("k")
        self.assertEqual(memory.usual_prices["k"], 10.0)
        memory.prices["k"] = 20.0
        memory.note_usual_price("k")
        self.assertAlmostEqual(memory.usual_prices["k"], 10.0 + USUAL_PRICE_SPEED * 10.0)

    def test_a_market_with_no_price_has_no_usual_price(self):
        memory = MarketMemory()
        memory.note_usual_price("k")
        self.assertEqual(memory.usual_prices, {})


class UsualPriceView(store_view.View):
    def __init__(self, usual, **kwargs):
        super().__init__(**kwargs)
        self.usual = usual

    def usual_price(self, good, area):
        return self.usual.get(good)


class StoreHoldingTests(unittest.TestCase):
    def holding(self, view):
        specs = dict(store_view.SPECS)
        specs[OTHER] = GoodSpec(OTHER, 1.0, 0.0, 20.0, "metal")
        view.prices[OTHER] = view.prices["metal_kg"]
        priced = households_basket.need_prices(store_view.BASKET, view, store_view.TILE)
        weights, _prices, _held = store_holding(store_view.cohort(), view, specs, priced)
        return weights

    def test_a_good_priced_above_its_usual_price_draws_a_smaller_share(self):
        plain = self.holding(store_view.View())
        self.assertAlmostEqual(plain["metal_kg"], plain[OTHER])
        view = UsualPriceView({"metal_kg": 50.0, OTHER: 95.0})
        risen = self.holding(view)
        self.assertLess(risen["metal_kg"], risen[OTHER])
        view = UsualPriceView({"metal_kg": 190.0, OTHER: 95.0})
        fallen = self.holding(view)
        self.assertGreater(fallen["metal_kg"], fallen[OTHER])


if __name__ == "__main__":
    unittest.main()
