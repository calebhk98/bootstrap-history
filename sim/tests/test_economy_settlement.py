"""Settlement: clearing results become postings; unpaid and undelivered parts are reported, not crashed on."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy.accounts import Book, InsufficientFunds
from sim.economy.settlement import CANNOT_DELIVER, CANNOT_PAY, book_legacy, settle_goods, settle_labour
from sim.economy.types import (EDGE_LEGACY, EDGE_MINT, EDGE_PRODUCTION, ClearingResult, Fill, GoodsMove, LabourResult,
                               Transfer)


def fill(agent, side, quantity, price, tile="t1", good="grain"):
    return Fill(agent, good, "area", tile, quantity, price, side)


def result(fills, price=2.0, good="grain"):
    return ClearingResult(good, "area", "coin", price, sum(f.quantity for f in fills if f.side == "buy"),
                          0.0, 0.0, 0.0, tuple(fills))


def world(purses, stocks):
    book = Book()
    for agent, amount in purses.items():
        book.transfer(Transfer(EDGE_MINT, agent, "coin", amount, "opening"))
    for (agent, tile), quantity in stocks.items():
        book.move(GoodsMove(EDGE_PRODUCTION, agent, "grain", tile, quantity, "harvest"))
    return book


def money_postings(outcome):
    return [posting for posting in outcome.postings if isinstance(posting, Transfer)]


class GoodsSettlementTests(unittest.TestCase):
    def test_one_buyer_one_seller(self):
        book = world({"buyer": 100.0}, {("seller", "t1"): 10.0})
        outcome = settle_goods(book, result([fill("buyer", "buy", 10.0, 2.0, "t2"), fill("seller", "sell", 10.0, 2.0)]))
        self.assertTrue(outcome.complete)
        self.assertAlmostEqual(book.balance("seller", "coin"), 20.0)
        self.assertAlmostEqual(book.balance("buyer", "coin"), 80.0)
        self.assertAlmostEqual(book.stock("buyer", "grain", "t2"), 10.0)
        self.assertAlmostEqual(book.stock("seller", "grain", "t1"), 0.0)
        self.assertIn("sale of grain", book.money_flow("coin"))

    def test_each_fill_total_matches_what_the_fill_says(self):
        book = world({"b1": 100.0, "b2": 100.0}, {("s1", "t1"): 6.0, ("s2", "t3"): 4.0})
        fills = [fill("b1", "buy", 7.0, 3.0, "t2"), fill("b2", "buy", 3.0, 3.0, "t4"),
                 fill("s1", "sell", 6.0, 3.0, "t1"), fill("s2", "sell", 4.0, 3.0, "t3")]
        settle_goods(book, result(fills, price=3.0))
        self.assertAlmostEqual(100.0 - book.balance("b1", "coin"), 21.0)
        self.assertAlmostEqual(100.0 - book.balance("b2", "coin"), 9.0)
        self.assertAlmostEqual(book.balance("s1", "coin"), 18.0)
        self.assertAlmostEqual(book.balance("s2", "coin"), 12.0)
        self.assertAlmostEqual(book.stock("b1", "grain", "t2"), 7.0)
        self.assertAlmostEqual(book.stock("b2", "grain", "t4"), 3.0)
        self.assertAlmostEqual(book.stock("s2", "grain", "t3"), 0.0)

    def test_buyers_and_sellers_are_matched_in_order(self):
        book = world({"b1": 100.0, "b2": 100.0}, {("s1", "t1"): 6.0, ("s2", "t1"): 4.0})
        fills = [fill("b2", "buy", 5.0, 1.0), fill("b1", "buy", 5.0, 1.0),
                 fill("s2", "sell", 4.0, 1.0), fill("s1", "sell", 6.0, 1.0)]
        outcome = settle_goods(book, result(fills, price=1.0))
        paid = {(posting.payer, posting.payee): posting.amount for posting in money_postings(outcome)}
        self.assertEqual(set(paid), {("b1", "s1"), ("b2", "s1"), ("b2", "s2")})
        self.assertAlmostEqual(paid[("b1", "s1")], 5.0)
        self.assertAlmostEqual(paid[("b2", "s1")], 1.0)
        self.assertAlmostEqual(paid[("b2", "s2")], 4.0)

    def test_postings_grow_with_buyers_plus_sellers_not_their_product(self):
        buyers, sellers = 60, 7
        book = world({"b%02d" % index: 1e6 for index in range(buyers)},
                     {("s%d" % index, "t1"): 100.0 for index in range(sellers)})
        fills = [fill("b%02d" % index, "buy", 10.0, 2.0, "t2") for index in range(buyers)]
        fills += [fill("s%d" % index, "sell", 600.0 / sellers, 2.0) for index in range(sellers)]
        outcome = settle_goods(book, result(fills))
        self.assertLessEqual(len(money_postings(outcome)), buyers + sellers)
        self.assertAlmostEqual(book.stock("b00", "grain", "t2"), 10.0)
        self.assertAlmostEqual(sum(book.balance("s%d" % index, "coin") for index in range(sellers)), 1200.0)
        self.assertTrue(book.check_conservation(1e-9).ok)

    def test_unequal_totals_settle_the_smaller_side(self):
        book = world({"buyer": 100.0}, {("s1", "t1"): 4.0, ("s2", "t1"): 4.0})
        outcome = settle_goods(book, result([fill("buyer", "buy", 5.0, 1.0), fill("s1", "sell", 4.0, 1.0),
                                             fill("s2", "sell", 4.0, 1.0)], price=1.0))
        self.assertAlmostEqual(book.stock("buyer", "grain", "t1"), 5.0)
        self.assertAlmostEqual(book.balance("buyer", "coin"), 95.0)
        self.assertTrue(outcome.complete)

    def test_a_buyer_who_cannot_pay_gets_only_what_it_can_pay_for(self):
        book = world({"buyer": 10.0}, {("seller", "t1"): 10.0})
        outcome = settle_goods(book, result([fill("buyer", "buy", 10.0, 2.0), fill("seller", "sell", 10.0, 2.0)]))
        self.assertAlmostEqual(book.stock("buyer", "grain", "t1"), 5.0)
        self.assertAlmostEqual(book.stock("seller", "grain", "t1"), 5.0)
        self.assertGreaterEqual(book.balance("buyer", "coin"), 0.0)
        self.assertEqual(len(outcome.shortfalls), 1)
        shortfall = outcome.shortfalls[0]
        self.assertEqual((shortfall.agent, shortfall.kind), ("buyer", CANNOT_PAY))
        self.assertAlmostEqual(shortfall.unsettled_quantity, 5.0)
        self.assertAlmostEqual(shortfall.unpaid_amount, 10.0)

    def test_a_seller_short_of_goods_delivers_what_it_has(self):
        book = world({"buyer": 100.0}, {("seller", "t1"): 4.0})
        outcome = settle_goods(book, result([fill("buyer", "buy", 10.0, 2.0), fill("seller", "sell", 10.0, 2.0)]))
        self.assertAlmostEqual(book.stock("buyer", "grain", "t1"), 4.0)
        self.assertAlmostEqual(book.balance("buyer", "coin"), 92.0)
        self.assertEqual([(item.agent, item.kind) for item in outcome.shortfalls], [("seller", CANNOT_DELIVER)])

    def test_a_negative_price_makes_the_seller_pay_the_taker(self):
        book = world({"seller": 100.0}, {("seller", "t1"): 10.0})
        fills = [fill("buyer", "buy", 10.0, -1.0, "t2"), fill("seller", "sell", 10.0, -1.0)]
        settle_goods(book, result(fills, price=-1.0))
        self.assertAlmostEqual(book.balance("buyer", "coin"), 10.0)
        self.assertAlmostEqual(book.balance("seller", "coin"), 90.0)
        self.assertAlmostEqual(book.stock("buyer", "grain", "t2"), 10.0)

    def test_an_empty_result_settles_nothing(self):
        self.assertEqual(settle_goods(world({}, {}), result([])).postings, [])

    def test_a_purse_spent_to_the_last_coin_does_not_trip_rounding(self):
        third = 1.0 / 3.0
        book = world({"buyer": 1.0}, {("s1", "t1"): 1.0, ("s2", "t1"): 1.0, ("s3", "t1"): 1.0})
        fills = [fill("buyer", "buy", 3.0, third), fill("s1", "sell", 1.0, third),
                 fill("s2", "sell", 1.0, third), fill("s3", "sell", 1.0, third)]
        outcome = settle_goods(book, result(fills, price=third))
        self.assertGreaterEqual(book.balance("buyer", "coin"), 0.0)
        self.assertAlmostEqual(book.stock("buyer", "grain", "t1"), 3.0)
        self.assertTrue(outcome.complete)


class LabourSettlementTests(unittest.TestCase):
    def labour_result(self):
        fills = (Fill("farm", "ploughing", "area", "t1", 40.0, 0.5, "buy"),
                 Fill("household", "ploughing", "area", "t1", 40.0, 0.5, "sell"))
        return LabourResult("ploughing", "area", "coin", 0.5, 40.0, 0.0, 0.0, fills)

    def test_wages_flow_from_employer_to_worker(self):
        book = world({"farm": 100.0}, {})
        outcome = settle_labour(book, self.labour_result())
        self.assertTrue(outcome.complete)
        self.assertAlmostEqual(book.balance("household", "coin"), 20.0)
        self.assertAlmostEqual(book.money_flow("coin")["wages for ploughing"], 20.0)

    def test_an_employer_who_cannot_pay_pays_for_fewer_hours(self):
        book = world({"farm": 10.0}, {})
        outcome = settle_labour(book, self.labour_result())
        self.assertAlmostEqual(book.balance("household", "coin"), 10.0)
        self.assertAlmostEqual(outcome.shortfalls[0].unsettled_quantity, 20.0)


class LegacyTests(unittest.TestCase):
    def test_a_legacy_posting_is_booked_against_the_legacy_edge(self):
        book = Book()
        book_legacy(book, "alice", "coin", 10.0, "engine grant")
        self.assertEqual(book.balance("alice", "coin"), 10.0)
        self.assertEqual(book.balance(EDGE_LEGACY, "coin"), -10.0)
        book_legacy(book, "alice", "coin", -4.0, "engine charge")
        self.assertEqual(book.balance("alice", "coin"), 6.0)
        self.assertEqual(book.total("coin"), 0.0)

    def test_a_legacy_charge_cannot_overdraw_an_agent(self):
        with self.assertRaises(InsufficientFunds):
            book_legacy(Book(), "alice", "coin", -4.0, "engine charge")


class RandomisedTests(unittest.TestCase):
    def test_random_postings_and_settlements_conserve_and_never_overdraw(self):
        rng = random.Random(20240601)
        agents = ["a%d" % number for number in range(8)]
        book = Book()
        for agent in agents:
            book.transfer(Transfer(EDGE_MINT, agent, "coin", rng.uniform(0.0, 200.0), "opening"))
            book.move(GoodsMove(EDGE_PRODUCTION, agent, "grain", "t%d" % rng.randrange(3), rng.uniform(0.0, 50.0), "harvest"))
        for _step in range(300):
            if rng.random() < 0.5:
                payer, payee = rng.sample(agents, 2)
                try:
                    book.transfer(Transfer(payer, payee, "coin", rng.uniform(0.0, 80.0), "random"))
                except InsufficientFunds:
                    pass
            else:
                buyers = rng.sample(agents, rng.randrange(1, 4))
                sellers = [agent for agent in agents if agent not in buyers][:rng.randrange(1, 4)]
                price = rng.uniform(-0.5, 5.0)
                fills = [fill(agent, "buy", rng.uniform(1.0, 30.0), price, "t%d" % rng.randrange(3)) for agent in buyers]
                fills += [fill(agent, "sell", rng.uniform(1.0, 30.0), price, "t%d" % rng.randrange(3)) for agent in sellers]
                settle_goods(book, result(fills, price=price))
            self.assertLess(abs(book.total("coin")), 1e-6)
            for agent in agents:
                self.assertGreaterEqual(book.balance(agent, "coin"), 0.0)
                for by_tile in book.holdings(agent)["goods"].values():
                    for held in by_tile.values():
                        self.assertGreaterEqual(held, 0.0)
        self.assertTrue(book.check_conservation(1e-9).ok)


if __name__ == "__main__":
    unittest.main()
