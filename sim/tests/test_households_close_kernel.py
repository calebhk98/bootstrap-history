"""The households' year end over arrays: `households_close_pack.unmet_by_cohort` (the kernel `households_close_kernel.unmet_floors` over every
cohort) equals `households_close.unmet_floor_by_need` cohort by cohort, bit for bit, on random baskets, receipts, holdings of durables and
people. No game."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.book import Book
from sim.book_types import GoodsMove
from sim.economy import households_close, households_close_pack
from sim.economy.households_cohort import Cohort
from sim.economy.types import EDGE_PRODUCTION
from sim.tests.test_opening_demand_kernel import NEED_DATA, SPECS
from sim.world import need_basket


class BookView:
    """The one read `unmet_floor_by_need` makes of a view: the stock a cohort holds."""

    def __init__(self, book):
        self.book = book

    def stock(self, agent, good, tile):
        return self.book.stock(agent, good, tile)


def cohort_of(agent, tile, people):
    return Cohort(agent, tile, 0, people, people * 0.4, 0.3)


class UnmetFloorsAgree(unittest.TestCase):
    def test_kernel_equals_the_python_cohort_by_cohort(self):
        rng = random.Random(7)
        short = durable_served = 0
        for _case in range(120):
            data = {"needs": dict(NEED_DATA["needs"]), "goods": dict(NEED_DATA["goods"])}
            data["needs"]["tools"] = {"surplus_budget_share": 0.2, "subsistence_per_capita_per_year": rng.choice([0.0, 0.5, 3.0])}
            data["needs"]["ornament"] = {"surplus_budget_share": 0.1, "subsistence_per_capita_per_year": rng.choice([0.0, 0.2])}
            basket = need_basket.make_basket(data, {})
            second = need_basket.make_basket(data, {}, substitution_elasticity=3.0)
            book = Book()
            names = sorted(SPECS) + ["unnumbered_good"]
            for good in sorted(SPECS):
                book.good_number(good)
            cohorts, received, baskets = [], [], []
            for number in range(rng.randint(1, 6)):
                agent, tile = "household:t%d:%d" % (number % 2, number), "t%d" % (number % 2)
                cohorts.append(cohort_of(agent, tile, rng.choice([0.0, rng.uniform(10.0, 4000.0)])))
                for good in ("hoe", "gold"):
                    if rng.random() < 0.5:
                        book.post((), [GoodsMove(EDGE_PRODUCTION, agent, good, tile, rng.uniform(0.0, 200.0), "test holding")])
                got = {good: rng.uniform(0.0, 5000.0) for good in rng.sample(names, rng.randint(0, len(names)))}
                received.append(got)
                baskets.append(rng.choice([("a", basket), ("b", second)]))
            packed = households_close_pack.PackedBaskets(book, SPECS)
            numbers = [packed.add(key, each) for key, each in baskets]
            start, goods, amounts = [0], [], []
            for got in received:
                for good, quantity in got.items():
                    number = book.good_ids.numbers.get(good)
                    if number is not None:
                        goods.append(number)
                        amounts.append(quantity)
                start.append(len(goods))
            answers = households_close_pack.unmet_by_cohort(book, packed, cohorts, numbers, np.array(start, dtype=np.int64),
                                                             np.array(goods, dtype=np.int64), np.array(amounts, dtype=np.float64))
            for cohort, got, (_key, each), answer in zip(cohorts, received, baskets, answers):
                numbered = {good: quantity for good, quantity in got.items() if good in book.good_ids.numbers}
                expected = households_close.unmet_floor_by_need(cohort, numbered, BookView(book), SPECS, each)
                self.assertEqual(answer, expected)
                self.assertEqual(list(answer), list(expected))
                short += bool(expected)
                durable_served += bool(book.stock(cohort.agent_id, "hoe", cohort.tile))
        self.assertGreater(short, 100, "shortages are exercised")
        self.assertGreater(durable_served, 50, "held durables are exercised")

    def test_a_cohort_with_no_people_has_no_floor_and_no_shortage(self):
        book = Book()
        book.good_number("bread")
        packed = households_close_pack.PackedBaskets(book, SPECS)
        basket = need_basket.make_basket(NEED_DATA, {})
        answers = households_close_pack.unmet_by_cohort(
            book, packed, [cohort_of("household:t0:0", "t0", 0.0)], [packed.add("a", basket)], np.array([0, 0], dtype=np.int64),
            np.array([], dtype=np.int64), np.array([], dtype=np.float64))
        self.assertEqual(answers, [{}])


if __name__ == "__main__":
    unittest.main()
