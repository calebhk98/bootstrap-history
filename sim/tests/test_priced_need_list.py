"""The priced needs of a basket kept as columns (`priced_need_list.PricedNeeds` over an answered `priced_needs.PricedBatch`): the columns, the floor
cost and the readers that take columns equal the `PricedNeed` objects of the one-need-at-a-time path (`need_basket`), and no object is made while
only columns are read. No game."""

QUICK_TOPIC = True

import math
import random
import unittest
from unittest import mock

import numpy

from sim.economy import households_credit, households_store, labour_ask_floor, priced_need_list, priced_need_tables, priced_needs, store_return
from sim.economy.types import GoodSpec
from sim.tests.test_priced_need_kernel import basket_of, random_needs
from sim.world import need_basket
from sim.world.need_basket import NeedSpec

FOOD = NeedSpec("food", 200.0, 0.5, (("grain", 1.0), ("tallow", 2.0), ("fish", 0.5)))
LIGHT = NeedSpec("light", 0.0, 0.2, (("tallow", 1.0), ("oil", 1.5)), (("oil", 0.6),), (("tallow", 0.8),))
WARMTH = NeedSpec("warmth", 30.0, 0.3, (("wood", 5.0),))
PRICES = {"grain": 1.0, "tallow": 0.4, "oil": 0.9, "fish": 0.0}      # wood has no price: warmth is not priced, fish has a zero price


def expected_needs(specs, prices, substitution=2.0):
    exponent = 1.0 - substitution
    return [each for each in (need_basket.priced_need(spec, exponent, prices.get) for spec in specs) if each is not None]


class ColumnsEqualObjects(unittest.TestCase):
    def test_the_blocks_and_columns_equal_each_priced_need_written_out(self):
        priced = priced_needs.priced_needs_at(basket_of([FOOD, LIGHT, WARMTH]), PRICES)
        expected = expected_needs([FOOD, LIGHT, WARMTH], PRICES)
        self.assertEqual(len(priced), 2)
        columns = priced.columns
        for (spec, price_index, first, end), need in zip(priced.blocks(), expected):
            self.assertEqual(spec, need.spec)
            self.assertEqual(price_index, need.price_index)
            self.assertEqual(tuple(zip(columns.names[first:end], columns.price[first:end], columns.effect[first:end], columns.share[first:end])), need.goods)
            self.assertEqual(tuple(columns.ceiling[first:end]), need.ceilings)
        self.assertEqual([row[0] for row in expected[0].goods], ["grain", "tallow"], "a zero price takes no part")

    def test_random_baskets_equal_the_objects_and_the_floor_cost_is_the_same_sum(self):
        rng = random.Random(3)
        for _case in range(200):
            specs, prices = random_needs(rng)
            substitution = rng.choice([2.0, 3.5, 0.5])
            priced = priced_needs.priced_needs_at(basket_of(specs, substitution), prices)
            expected = expected_needs(specs, prices, substitution)
            self.assertEqual(priced.objects(), expected)
            self.assertEqual(priced.subsistence_cost_per_person(), need_basket.subsistence_cost_per_person(expected))

    def test_no_object_is_made_while_only_columns_are_read(self):
        priced = priced_needs.priced_needs_at(basket_of([FOOD, LIGHT]), PRICES)
        with mock.patch.object(priced_needs.PricedBatch, "need", side_effect=AssertionError("a PricedNeed was made")):
            list(priced.blocks())
            priced.subsistence_cost_per_person()
            households_store.staple_price_per_kg(priced, {"grain": GoodSpec("grain", 1.0, 0.0, 0.0, "food")})
            self.assertEqual(len(priced), 2)
        self.assertIsNone(priced._objects)

    def test_an_object_is_made_once_and_only_when_indexed(self):
        priced = priced_needs.priced_needs_at(basket_of([FOOD, LIGHT]), PRICES)
        self.assertIs(priced[0], priced[0])
        self.assertEqual([need.spec.need_id for need in priced], ["food", "light"])

    def test_a_batch_of_requests_gives_each_request_its_priced_needs_in_order(self):
        batch = priced_need_tables.NeedBatch()
        batch.add(0, -1.0, (FOOD, WARMTH))
        batch.add(1, -1.0, (WARMTH,))
        batch.add(0, -1.0, (WARMTH, LIGHT, FOOD))
        answer = priced_needs.PricedBatch(batch, priced_need_tables.price_matrix([PRICES, {"wood": 2.0}]))
        first, second, third = answer.positions_by_request()
        self.assertEqual([answer.specs[position].need_id for position in first], ["food"])
        self.assertEqual([answer.specs[position].need_id for position in second], ["warmth"])
        self.assertEqual([answer.specs[position].need_id for position in third], ["light", "food"])


class OfObjects(unittest.TestCase):
    def test_a_list_of_objects_read_as_columns_gives_the_same_blocks_and_arrays(self):
        expected = expected_needs([FOOD, LIGHT], PRICES)
        listed = priced_need_list.PricedNeeds.of(expected)
        tabled = priced_needs.priced_needs_at(basket_of([FOOD, LIGHT]), PRICES)
        self.assertEqual(list(listed.blocks()), list(tabled.blocks()))
        for name in ("good", "price", "effect", "share", "ceiling", "quality", "limit", "start", "stop"):
            self.assertTrue(numpy.array_equal(getattr(listed.columns.arrays, name), getattr(tabled.columns.arrays, name), equal_nan=True), name)
        self.assertIs(listed[0], expected[0])
        self.assertIs(priced_need_list.priced_needs_of(listed), listed)

    def test_equality_with_a_list_of_objects(self):
        priced = priced_needs.priced_needs_at(basket_of([FOOD, LIGHT]), PRICES)
        self.assertEqual(priced, expected_needs([FOOD, LIGHT], PRICES))
        self.assertNotEqual(priced, expected_needs([FOOD], PRICES))


SPECS = {"grain": GoodSpec("grain", 1.0, 0.0, 0.0, "food"), "tallow": GoodSpec("tallow", 0.5, 0.0, 0.0, "light"),
         "oil": GoodSpec("oil", 2.0, 0.0, 12.0, "light"), "fish": GoodSpec("fish", 1.0, 0.0, 0.0, "food")}


class Readers(unittest.TestCase):
    def priced(self):
        return priced_needs.priced_needs_at(basket_of([FOOD, LIGHT, WARMTH]), PRICES)

    def test_staple_price_per_kg_is_the_cheapest_floor_good_per_kilogram(self):
        priced, objects = self.priced(), expected_needs([FOOD, LIGHT, WARMTH], PRICES)
        cheapest = min(price / SPECS[good].unit_mass_kg for need in objects if need.spec.subsistence_per_person > 0.0
                       for good, price, _effect, _share in need.goods)
        self.assertEqual(households_store.staple_price_per_kg(priced, SPECS), cheapest)
        self.assertEqual(households_store.staple_price_per_kg(objects, SPECS), cheapest)
        self.assertEqual(households_store.staple_price_per_kg(priced_need_list.PricedNeeds.of([]), SPECS), math.inf)

    def test_service_values_per_year_adds_a_durable_over_the_needs_that_name_it(self):
        priced, objects = self.priced(), expected_needs([FOOD, LIGHT, WARMTH], PRICES)
        want = {}
        for need in objects:
            for good, _price, effect, _share in need.goods:
                if SPECS[good].service_life_years > 0.0 and effect > 0.0:
                    want[good] = want.get(good, 0.0) + effect * need.price_index / SPECS[good].service_life_years
        self.assertEqual(store_return.service_values_per_year(priced, SPECS), want)
        self.assertEqual(list(want), ["oil"])

    def test_floor_cost_unmet_takes_what_the_plot_grew_off_each_floor(self):
        priced, objects = self.priced(), expected_needs([FOOD, LIGHT, WARMTH], PRICES)
        cohort = mock.Mock(people=10.0)
        grown = {"food": 500.0}
        want = math.fsum(need.price_index * max(0.0, need.spec.subsistence_per_person * 10.0 - grown.get(need.spec.need_id, 0.0)) for need in objects)
        self.assertEqual(households_credit.floor_cost_unmet(cohort, priced, grown), want)
        self.assertEqual(households_credit.floor_cost_unmet(cohort, objects, grown), want)

    def test_the_wage_floor_reads_columns_as_it_read_objects(self):
        options = {"food": [(0.5, "grow", "grain", 1.0)]}
        priced, objects = self.priced(), expected_needs([FOOD, LIGHT, WARMTH], PRICES)
        per_hour = {"grow": 0.002}
        got = labour_ask_floor.wage_floor_per_worker_year(priced, options, 0.9, 2000.0, 3.0, per_hour, 0.4)
        self.assertEqual(got, labour_ask_floor.wage_floor_per_worker_year(objects, options, 0.9, 2000.0, 3.0, per_hour, 0.4))
        household_cost = need_basket.subsistence_cost_per_person(objects) * 3.0
        self.assertGreater(got, 0.0)
        self.assertGreaterEqual(got, household_cost - objects[0].price_index * 200.0 * 3.0)


if __name__ == "__main__":
    unittest.main()
