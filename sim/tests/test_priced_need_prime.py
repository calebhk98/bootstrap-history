"""Baskets asked of a view are priced again in one batch after a write to the memory (sim/economy/priced_need_prime.py): each list kept
by the batch equals the fresh one-need-at-a-time pricing, on random remembered prices, with share limits and quality factors."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import priced_reads
from sim.economy.priced_need_prime import TILE_BASKET_KEY, price_asked
from sim.tests.year_close_fixture import GOODS, TILES, economy_of
from sim.world import need_basket
from sim.world.need_basket import make_basket

NEED_DATA = {"needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 10.0},
                       "warmth": {"surplus_budget_share": 0.1, "subsistence_per_capita_per_year": 300.0},
                       "light": {"surplus_budget_share": 0.2, "subsistence_per_capita_per_year": 0.0}},
             "goods": {GOODS[0]: {"satisfies": {"food": 1.0}, "max_share_of_need": {"food": 0.4}},
                       GOODS[1]: {"satisfies": {"food": 0.8}, "quality": {"food": {"factor": 1.5}}},
                       GOODS[2]: {"satisfies": {"food": 0.3, "light": 1.0}},
                       GOODS[3]: {"satisfies": {"warmth": 15.0}},
                       GOODS[4]: {"satisfies": {"warmth": 9.0, "light": 2.0}},
                       "unlisted_good": {"satisfies": {"light": 3.0}}}}


def fresh(basket, view, tile):
    """The basket priced a good at a time, as `households_basket.need_prices` did without a block."""
    return list(need_basket.need_prices(basket, lambda good: view.offered_price(good, view.area_of(good, tile))))


class PrimedAfterAWrite(unittest.TestCase):
    def asked(self, seed):
        _setup, _record, view, _ledger, _area_map = economy_of(seed)
        baskets = {TILE_BASKET_KEY: make_basket(NEED_DATA, {})}
        for tile in TILES:
            for key, basket in baskets.items():
                priced_reads.kept_need_prices(view, lambda basket=basket: basket, tile, key)
        return view, baskets

    def test_each_list_after_a_write_equals_the_fresh_pricing(self):
        for seed in range(8):
            view, baskets = self.asked(seed)
            some_key = sorted(view._memory.prices)[0]
            view._memory.set_price(some_key, view._memory.prices[some_key] * 1.7)
            kept = priced_reads.kept_need_prices(view, lambda: baskets[TILE_BASKET_KEY], TILES[0], TILE_BASKET_KEY)
            self.assertEqual(kept, fresh(baskets[TILE_BASKET_KEY], view, TILES[0]))
            reads = view._current()
            for tile in TILES:
                for key, basket in baskets.items():
                    self.assertIn(("need_prices", tile, key), reads, "the batch priced every basket asked before")
                    self.assertEqual(reads[("need_prices", tile, key)], fresh(basket, view, tile), (seed, tile, key))

    def test_baskets_priced_together_that_hold_the_same_need_share_its_priced_object(self):
        _setup, _record, view, _ledger, _area_map = economy_of(0)
        plain = make_basket(NEED_DATA, {})
        part = dataclasses.replace(plain, needs=plain.needs[:2])
        reads = view._current()
        self.assertTrue(price_asked(view, reads, [(TILES[0], "plain", plain), (TILES[0], "part", part)]))
        whole, partial = reads[("need_prices", TILES[0], "plain")], reads[("need_prices", TILES[0], "part")]
        self.assertTrue(partial)
        self.assertIs(whole[0], partial[0])
        self.assertEqual(whole, fresh(plain, view, TILES[0]))
        self.assertEqual(partial, fresh(part, view, TILES[0]))

    def test_a_tile_the_grid_does_not_hold_is_left_to_the_one_at_a_time_path(self):
        _setup, _record, view, _ledger, _area_map = economy_of(0)
        reads = view._current()
        self.assertFalse(price_asked(view, reads, [("nowhere", "a", make_basket(NEED_DATA, {})), (TILES[0], "a", make_basket(NEED_DATA, {}))]))
        self.assertNotIn(("need_prices", TILES[0], "a"), reads)


class ManyAtOnce(unittest.TestCase):
    def test_the_lists_of_many_asks_equal_the_fresh_pricing_and_keep_their_order(self):
        for seed in range(4):
            _setup, _record, view, _ledger, _area_map = economy_of(seed)
            baskets = [make_basket(NEED_DATA, {}), make_basket(NEED_DATA, {}, substitution_elasticity=0.3)]
            asks = [(tile, ("many", index), lambda basket=basket: basket) for tile in TILES for index, basket in enumerate(baskets)]
            found = priced_reads.kept_need_prices_many(view, asks)
            self.assertEqual(len(found), len(asks))
            for (tile, _key, basket_of), kept in zip(asks, found):
                self.assertEqual(kept, fresh(basket_of(), view, tile))

    def test_a_view_without_kept_reads_answers_every_ask_by_itself(self):
        class Plain:
            def area_of(self, good, tile):
                return "area"

            def offered_price(self, good, area):
                return 2.0
        basket = make_basket(NEED_DATA, {})
        found = priced_reads.kept_need_prices_many(Plain(), [("t", "a", lambda: basket), ("u", "b", lambda: basket)])
        self.assertEqual(found[0], found[1])
        self.assertEqual(found[0], fresh(basket, Plain(), "t"))


if __name__ == "__main__":
    unittest.main()
