"""The economy's double-entry book: postings, atomic batches, reads, flows, conservation, save file."""
import json
import unittest

from sim.economy.accounts import (Book, DeliveredMove, InsufficientFunds, InsufficientGoods, NegativeAmount)
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Transfer


def funded(**purses):
    book = Book()
    for agent, amount in purses.items():
        book.transfer(Transfer(EDGE_MINT, agent, "coin", amount, "opening"))
    return book


class TransferTests(unittest.TestCase):
    def test_a_transfer_moves_money_and_keeps_the_total_at_zero(self):
        book = funded(alice=100.0)
        book.transfer(Transfer("alice", "bob", "coin", 30.0, "rent"))
        self.assertEqual(book.balance("alice", "coin"), 70.0)
        self.assertEqual(book.balance("bob", "coin"), 30.0)
        self.assertEqual(book.total("coin"), 0.0)
        self.assertEqual(book.money_supply("coin"), 100.0)

    def test_a_purse_cannot_go_below_zero(self):
        book = funded(alice=10.0)
        with self.assertRaises(InsufficientFunds) as raised:
            book.transfer(Transfer("alice", "bob", "coin", 10.5, "rent"))
        self.assertIn("alice", str(raised.exception))
        self.assertEqual(book.balance("alice", "coin"), 10.0)

    def test_an_edge_account_may_go_negative(self):
        book = funded(alice=10.0)
        self.assertEqual(book.balance(EDGE_MINT, "coin"), -10.0)

    def test_negative_amounts_are_refused(self):
        book = funded(alice=10.0)
        with self.assertRaises(NegativeAmount):
            book.transfer(Transfer("alice", "bob", "coin", -1.0, "rent"))
        with self.assertRaises(NegativeAmount):
            book.move(GoodsMove(EDGE_PRODUCTION, "alice", "grain", "t1", -1.0, "harvest"))

    def test_currencies_are_separate_purses(self):
        book = funded(alice=10.0)
        with self.assertRaises(InsufficientFunds):
            book.transfer(Transfer("alice", "bob", "other", 1.0, "rent"))

    def test_a_batch_applies_all_or_nothing(self):
        book = funded(alice=10.0)
        batch = [Transfer("alice", "bob", "coin", 6.0, "a"), Transfer("alice", "carol", "coin", 6.0, "b")]
        with self.assertRaises(InsufficientFunds):
            book.transfer_many(batch)
        self.assertEqual(book.balance("alice", "coin"), 10.0)
        self.assertEqual(book.balance("bob", "coin"), 0.0)

    def test_a_batch_may_spend_money_it_receives_earlier_in_the_batch(self):
        book = funded(alice=10.0)
        book.transfer_many([Transfer("alice", "bob", "coin", 10.0, "a"), Transfer("bob", "carol", "coin", 10.0, "b")])
        self.assertEqual(book.balance("carol", "coin"), 10.0)


class GoodsTests(unittest.TestCase):
    def setUp(self):
        self.book = Book()
        self.book.move(GoodsMove(EDGE_PRODUCTION, "farmer", "grain", "t1", 50.0, "harvest"))

    def test_goods_are_held_per_tile(self):
        self.book.move(GoodsMove("farmer", "miller", "grain", "t1", 20.0, "sale"))
        self.assertEqual(self.book.stock("farmer", "grain", "t1"), 30.0)
        self.assertEqual(self.book.stock("miller", "grain", "t1"), 20.0)
        self.assertEqual(self.book.stock("miller", "grain", "t2"), 0.0)
        self.assertEqual(self.book.goods_total("grain"), 0.0)

    def test_a_delivered_move_lands_on_the_receivers_tile(self):
        self.book.move(DeliveredMove("farmer", "miller", "grain", "t1", 20.0, "sale", "t2"))
        self.assertEqual(self.book.stock("miller", "grain", "t2"), 20.0)
        self.assertEqual(self.book.stock("miller", "grain", "t1"), 0.0)

    def test_a_giver_cannot_give_more_than_it_holds_on_the_tile(self):
        with self.assertRaises(InsufficientGoods):
            self.book.move(GoodsMove("farmer", "miller", "grain", "t2", 1.0, "sale"))
        with self.assertRaises(InsufficientGoods):
            self.book.move(GoodsMove("farmer", "miller", "grain", "t1", 50.5, "sale"))

    def test_a_goods_batch_applies_all_or_nothing(self):
        batch = [GoodsMove("farmer", "miller", "grain", "t1", 30.0, "a"), GoodsMove("farmer", "baker", "grain", "t1", 30.0, "b")]
        with self.assertRaises(InsufficientGoods):
            self.book.move_many(batch)
        self.assertEqual(self.book.stock("farmer", "grain", "t1"), 50.0)

    def test_post_is_atomic_across_money_and_goods(self):
        with self.assertRaises(InsufficientFunds):
            self.book.post([Transfer("miller", "farmer", "coin", 5.0, "pay")],
                           [GoodsMove("farmer", "miller", "grain", "t1", 5.0, "sale")])
        self.assertEqual(self.book.stock("miller", "grain", "t1"), 0.0)


class ReadTests(unittest.TestCase):
    def test_reads_are_sorted_and_complete(self):
        book = funded(zed=5.0, amy=7.0)
        book.move(GoodsMove(EDGE_PRODUCTION, "zed", "grain", "t1", 3.0, "harvest"))
        book.move(GoodsMove(EDGE_PRODUCTION, "amy", "grain", "t2", 4.0, "harvest"))
        self.assertEqual(book.agents(), sorted(book.agents()))
        self.assertEqual(book.holders_of("grain"), ["amy", "zed"])
        self.assertEqual(book.holdings("amy"), {"money": {"coin": 7.0}, "goods": {"grain": {"t2": 4.0}}})
        self.assertEqual(book.holders_of("iron"), [])

    def test_a_holder_who_gave_everything_away_is_not_listed(self):
        book = Book()
        book.move(GoodsMove(EDGE_PRODUCTION, "amy", "grain", "t1", 4.0, "harvest"))
        book.move(GoodsMove("amy", "zed", "grain", "t1", 4.0, "sale"))
        self.assertEqual(book.holders_of("grain"), ["zed"])


class FlowTests(unittest.TestCase):
    def test_flows_by_purpose_and_edge_reset_each_year_while_holdings_carry(self):
        book = funded(alice=100.0)
        book.transfer(Transfer("alice", "bob", "coin", 40.0, "rent"))
        book.transfer(Transfer("alice", EDGE_MINT, "coin", 10.0, "melt"))
        self.assertEqual(book.money_flow("coin"), {"melt": 10.0, "opening": 100.0, "rent": 40.0})
        self.assertEqual(book.edge_volume(EDGE_MINT, "coin"), 110.0)
        self.assertEqual(book.edge_net(EDGE_MINT, "coin"), 90.0)
        book.start_year()
        self.assertEqual(book.money_flow("coin"), {})
        self.assertEqual(book.edge_volume(EDGE_MINT, "coin"), 0.0)
        self.assertEqual(book.balance("bob", "coin"), 40.0)

    def test_goods_flows_are_recorded(self):
        book = Book()
        book.move(GoodsMove(EDGE_PRODUCTION, "farmer", "grain", "t1", 50.0, "harvest"))
        self.assertEqual(book.goods_flow("grain"), {"harvest": 50.0})
        self.assertEqual(book.edge_goods_volume(EDGE_PRODUCTION, "grain"), 50.0)
        self.assertEqual(book.edge_goods_net(EDGE_PRODUCTION, "grain"), 50.0)


class ConservationTests(unittest.TestCase):
    def test_a_clean_book_conserves(self):
        book = funded(alice=100.0)
        book.move(GoodsMove(EDGE_PRODUCTION, "alice", "grain", "t1", 3.0, "harvest"))
        report = book.check_conservation(1e-9)
        self.assertTrue(report.ok)
        self.assertEqual(report.money["coin"], 0.0)

    def test_a_corrupted_book_is_reported(self):
        book = funded(alice=100.0)
        book._money["alice"]["coin"] += 5.0
        report = book.check_conservation(1e-9)
        self.assertFalse(report.ok)
        self.assertTrue(any("coin" in line for line in report.breaches))


class RecordTests(unittest.TestCase):
    def test_the_record_round_trips_exactly_through_json(self):
        book = funded(alice=100.1, bob=3.3)
        book.transfer(Transfer("alice", "bob", "coin", 0.1 + 0.2, "rent"))
        book.move(GoodsMove(EDGE_PRODUCTION, "alice", "grain", "t1", 7.7, "harvest"))
        book.move(DeliveredMove("alice", "bob", "grain", "t1", 1.1, "sale", "t2"))
        record = json.loads(json.dumps(book.to_record()))
        again = Book.from_record(record)
        self.assertEqual(again.to_record(), book.to_record())
        self.assertEqual(again.holders_of("grain"), ["alice", "bob"])
        self.assertEqual(again.edge_volume(EDGE_MINT, "coin"), book.edge_volume(EDGE_MINT, "coin"))

    def test_the_record_keys_are_sorted(self):
        book = funded(zed=1.0, amy=1.0)
        self.assertEqual(list(book.to_record()["money"]), sorted(book.to_record()["money"]))


if __name__ == "__main__":
    unittest.main()
