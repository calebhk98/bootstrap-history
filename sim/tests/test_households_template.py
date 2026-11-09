"""The blocks of the year's cohort orders and close made from columns (`households_template`, `households_close_pack.PackedBaskets.add`,
`households_own.growing_needs`, `cohort_prime`) equal the object loops they replace, on written-out inputs. No game."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

import numpy as np

from sim.economy import cohort_prime, households_close_pack, households_own, households_template, priced_need_tables, priced_needs
from sim.economy import opening_demand_kernel as opening_kernel
from sim.economy.priced_need_tables import GOODS
from sim.economy.types import GoodSpec
from sim.tests.test_priced_need_kernel import basket_of
from sim.world.need_basket import NeedSpec

FOOD = NeedSpec("food", 200.0, 0.5, (("t_grain", 1.0), ("t_tallow", 2.0), ("t_fish", 0.5)), (("t_tallow", 0.9),))
LIGHT = NeedSpec("light", 0.0, 0.2, (("t_tallow", 1.0), ("t_oil", 1.5)), (), (("t_tallow", 0.8),))
WARMTH = NeedSpec("warmth", 30.0, 0.3, (("t_wood", 5.0), ("t_oil", 2.0)))
PRICES = {"t_grain": 1.0, "t_tallow": 0.4, "t_oil": 0.9, "t_fish": 0.0, "t_wood": 0.2}
SPECS = {"t_grain": GoodSpec("t_grain", 1.0, 0.05, 0.0, "food"), "t_tallow": GoodSpec("t_tallow", 0.5, 0.02, 0.0, "light"),
         "t_oil": GoodSpec("t_oil", 2.0, 0.0, 12.0, "light"), "t_wood": GoodSpec("t_wood", 3.0, 0.0, 30.0, "fuel")}


class Selection(unittest.TestCase):
    def test_rows_are_the_ranges_joined_in_order(self):
        got = households_template.selected_rows(np.array([2, 7, 4]), np.array([4, 10, 4]))
        self.assertEqual(got.tolist(), [2, 3, 7, 8, 9])

    def test_no_range_gives_no_rows(self):
        self.assertEqual(households_template.selected_rows(np.array([], dtype=np.int64), np.array([], dtype=np.int64)).tolist(), [])

    def test_local_numbers_follow_the_first_appearance_and_grow_with_the_goods(self):
        numbers = [GOODS.of(name) for name in ("t_a", "t_b", "t_c", "t_d")]
        local = households_template.LocalGoods()
        a, b, c, d = numbers
        self.assertEqual(local.of(np.array([c, a, c, d])).tolist(), [0, 1, 0, 2])
        self.assertEqual(local.of(np.array([d, b, a])).tolist(), [2, 3, 1])
        later = GOODS.of("t_later")
        self.assertEqual(local.of(np.array([later, a])).tolist(), [4, 1])
        self.assertEqual(local.count, 5)

    def test_the_first_need_that_names_a_good_is_its_unit(self):
        a, b, c, unnamed = GOODS.of("t_ua"), GOODS.of("t_ub"), GOODS.of("t_uc"), GOODS.of("t_unnamed")
        first = households_template.first_unit_of_goods([a, b, b, c], [0, 0, 1, 1])
        self.assertEqual((first[a], first[b], first[c], first[unnamed]), (0, 0, 1, -1))


def reference_rows(priced_objects, specs, first_unit):
    """The rows the object loop of `households_orders_pack` made: floats, the good of each row, first unit, priority."""
    floats, goods, units, priority = [], [], [], []
    for need in priced_objects:
        qualities, limits = dict(need.spec.qualities), dict(need.spec.share_limits)
        for (good, price, effect, share), ceiling in zip(need.goods, need.ceilings):
            spec = specs.get(good)
            floats.append([price, effect, share, ceiling, qualities.get(good, 1.0), 0.0, spec.service_life_years if spec else 0.0,
                           spec.spoilage_per_year if spec else 0.0, 0.0, limits.get(good, np.nan)])
            goods.append(good)
            units.append(first_unit.get(good, -1))
            priority.append(0 if need.spec.subsistence_per_person > 0.0 else 1)
    return floats, goods, units, priority


class TemplateRows(unittest.TestCase):
    def test_the_rows_equal_the_object_loop(self):
        basket = basket_of([FOOD, LIGHT, WARMTH])
        priced = priced_needs.priced_needs_at(basket, PRICES)
        objects = priced.objects()
        first_unit = {}
        for position, spec in enumerate(basket.needs):
            for good, _effect in spec.goods:
                first_unit.setdefault(good, position)
        _held, _specs, first_of_need, basket_goods, *_rest = priced_need_tables.basket_rows(basket.needs)
        counts = np.diff(np.array(first_of_need + [len(basket_goods)]))
        by_good = households_template.first_unit_of_goods(basket_goods, np.repeat(np.arange(len(counts)), counts).tolist())
        life = np.array([SPECS[name].service_life_years if name in SPECS else 0.0 for name in GOODS.names])
        spoilage = np.array([SPECS[name].spoilage_per_year if name in SPECS else 0.0 for name in GOODS.names])
        local = households_template.LocalGoods()
        rows = households_template.template_rows(priced, [spec.subsistence_per_person > 0.0 for spec, *_rest in priced.blocks()], by_good, life,
                                                 spoilage, local)
        floats, goods, units, priority = reference_rows(objects, SPECS, first_unit)
        self.assertEqual(rows.floats.shape, (len(floats), opening_kernel.RF_COUNT))
        self.assertTrue(np.array_equal(rows.floats, np.array(floats), equal_nan=True))
        self.assertEqual(GOODS.name_array()[rows.good_numbers].tolist(), goods)
        self.assertEqual(rows.first_unit.tolist(), units)
        self.assertEqual(rows.priority.tolist(), priority)
        self.assertEqual(rows.counts.tolist(), [len(need.goods) for need in objects])
        self.assertEqual(rows.order.tolist(), sorted(range(len(goods)), key=lambda row: (goods[row], row)))
        distinct = list(dict.fromkeys(goods))
        self.assertEqual(rows.local_goods.tolist(), [distinct.index(good) for good in goods])


class StaticRowsKept(unittest.TestCase):
    def test_a_second_template_with_the_same_goods_on_the_tile_asks_nothing(self):
        orders = mock.Mock()
        orders.good_id.side_effect = lambda good: len(good)
        orders.market_ids.side_effect = lambda goods, areas: [len(good) * 10 for good in goods]
        view = mock.Mock()
        view.area_of.side_effect = lambda good, tile: "area_" + tile
        cache = {}
        first = households_template.static_rows(cache, ["ab", "cde"], ("T0", b"x"), "T0", view, orders)
        again = households_template.static_rows(cache, ["ab", "cde"], ("T0", b"x"), "T0", view, orders)
        self.assertIs(first, again)
        self.assertEqual((first.areas, first.good_ids, first.market_ids), (["area_T0", "area_T0"], [2, 3], [20, 30]))
        self.assertEqual(orders.market_ids.call_count, 1)
        households_template.static_rows(cache, ["ab", "cde"], ("T1", b"x"), "T1", view, orders)
        self.assertEqual(orders.market_ids.call_count, 2)


class PackedBasketsAdd(unittest.TestCase):
    def test_the_arrays_equal_the_loop_over_needs_and_goods(self):
        basket = basket_of([FOOD, LIGHT, WARMTH])
        numbers = {"t_grain": 7, "t_tallow": 3, "t_oil": 9, "t_wood": 4}      # t_fish is not numbered in the book
        book = types.SimpleNamespace(good_ids=types.SimpleNamespace(numbers=numbers))
        packed = households_close_pack.PackedBaskets(book, SPECS)
        self.assertEqual(packed.add("a", basket), 0)
        self.assertEqual(packed.add("a", basket), 0)
        need_floor, row_start, good, effect, life, held, durables = [], [0], [], [], [], [], []
        place_of = {}
        for need in basket.needs:
            need_floor.append(need.subsistence_per_person)
            for name, each in need.goods:
                spec = SPECS.get(name)
                duration = spec.service_life_years if spec is not None and spec.service_life_years > 0.0 else 0.0
                good.append(numbers.get(name, -1))
                effect.append(each)
                life.append(duration)
                if duration > 0.0:
                    held.append(place_of.setdefault(name, len(place_of)))
                else:
                    held.append(-1)
            row_start.append(len(good))
        self.assertEqual(packed.need_floor, need_floor)
        self.assertEqual(packed.row_start, row_start)
        self.assertEqual(np.concatenate(packed.row_good).tolist(), good)
        self.assertEqual(np.concatenate(packed.row_effect).tolist(), effect)
        self.assertEqual(np.concatenate(packed.row_life).tolist(), life)
        self.assertEqual(np.concatenate(packed.row_held_place).tolist(), held)
        self.assertEqual(packed.durables, [list(place_of)])
        self.assertEqual(packed.need_start, [0, 3])

    def test_a_second_basket_continues_the_rows(self):
        book = types.SimpleNamespace(good_ids=types.SimpleNamespace(numbers={"t_grain": 1}))
        packed = households_close_pack.PackedBaskets(book, SPECS)
        packed.add("a", basket_of([FOOD]))
        packed.add("b", basket_of([WARMTH]))
        self.assertEqual(packed.row_start, [0, 3, 5])
        self.assertEqual(packed.need_start, [0, 1, 2])
        self.assertEqual(packed.durables, [[], ["t_wood", "t_oil"]])


class GrowingNeeds(unittest.TestCase):
    def test_the_needs_with_options_in_the_baskets_order(self):
        basket = basket_of([FOOD, LIGHT, WARMTH])
        options = {"warmth": [(1.0, "r", "t_wood", 5.0)], "food": [(1.0, "r", "t_grain", 1.0)], "light": []}
        self.assertEqual([need.need_id for need in households_own.growing_needs(basket, options)], ["food", "warmth"])
        options["light"] = [(1.0, "r", "t_oil", 1.5)]
        self.assertEqual([need.need_id for need in households_own.growing_needs(basket, options)], ["food", "light", "warmth"])


class Priming(unittest.TestCase):
    def setUp(self):
        from sim.tests.year_close_fixture import TILES, economy_of
        _setup, _record, self.view, _ledger, _area_map = economy_of(1)
        self.tiles = TILES
        self.basket = basket_of([NeedSpec("food", 10.0, 0.5, (("good0", 1.0), ("good1", 0.8)))])
        tiles = self.tiles + self.tiles[:1]
        store = types.SimpleNamespace(ids=["c%d" % number for number in range(len(tiles))], order=lambda: np.arange(len(tiles)),
                                      tile_names=lambda rows: [tiles[row] for row in rows.tolist()])
        self.record = types.SimpleNamespace(cohorts=store)
        work = cohort_prime.household_work_year
        self.patches = [mock.patch.object(cohort_prime, "table_of", lambda cohorts: cohorts),
                        mock.patch.object(work, "signatures_of", lambda record, each, rows, buying=True: [(tiles[row], buying) for row in rows.tolist()]),
                        mock.patch.object(work, "basket_of_signature", lambda setup, signature: self.basket),
                        mock.patch.object(work, "hearth_of", lambda record, tile, agent_id: tile != "T2"),
                        mock.patch.object(work, "tile_food_basket", lambda setup, tile, hearth: self.basket)]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_every_cohort_basket_is_priced_in_one_batch_under_the_key_the_cohorts_ask_by(self):
        reads = self.view._current()
        with mock.patch.object(cohort_prime, "price_asked", wraps=cohort_prime.price_asked) as asked:
            cohort_prime.prime_cohort_baskets(types.SimpleNamespace(), self.record, self.view, True)
            cohort_prime.prime_cohort_baskets(types.SimpleNamespace(), self.record, self.view, True)
        self.assertEqual(asked.call_count, 1, "the second pass finds the memory already primed")
        self.assertEqual(len(asked.call_args.args[2]), len(self.tiles), "a tile with two cohorts of one basket is asked once")
        for tile in self.tiles:
            kept = reads[("need_prices", tile, ("cohort_basket", (tile, True)))]
            self.assertEqual(kept.objects(), priced_needs.priced_needs_at(
                self.basket, {good: self.view.offered_price(good, self.view.area_of(good, tile)) for good in ("good0", "good1")}).objects())

    def test_the_food_baskets_are_asked_by_tile_and_hearth_only_with_a_milled_grain(self):
        reads = self.view._current()
        cohort_prime.prime_food_baskets(types.SimpleNamespace(milled_as={}), self.record, self.view)
        self.assertNotIn(("need_prices", "T0", ("food", True)), reads)
        cohort_prime.prime_food_baskets(types.SimpleNamespace(milled_as={"good0": "good1"}), self.record, self.view)
        self.assertIn(("need_prices", "T0", ("food", True)), reads)
        self.assertIn(("need_prices", "T2", ("food", False)), reads)
        self.assertNotIn(("need_prices", "T2", ("food", True)), reads)

    def test_a_view_without_kept_reads_primes_nothing(self):
        cohort_prime.prime_cohort_baskets(types.SimpleNamespace(), self.record, types.SimpleNamespace(), True)


if __name__ == "__main__":
    unittest.main()
