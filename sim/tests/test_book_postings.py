"""Posting to the book (sim/book_post.py): the converter door `apply_postings`, refusals as causes, and the errors the
methods have always raised."""
QUICK_TOPIC = True

import unittest

from sim.book import Book, DeliveredMove, GoodsMove, InsufficientFunds, InsufficientGoods, NegativeAmount, Transfer
from sim.book_apply import RULE_BATCH
from sim.book_tables import (GOODS_MOVE_POSTINGS, INSUFFICIENT_FUNDS, INSUFFICIENT_GOODS, TRANSFER_POSTINGS, GoodsMovePostings,
                             TransferPostings)


def funded_book():
    book = Book()
    book.transfer(Transfer("edge:mint", "amy", "coin", 100.0, "start"))
    book.move(GoodsMove("edge:production", "amy", "grain", "t1", 50.0, "start"))
    return book


def three_batches(book):
    """Transfer postings of three batches (amy pays bob 30, amy pays bob 500, bob pays amy 10) and no moves."""
    amy, bob, coin = book.agent_number("amy"), book.agent_number("bob"), book.currency_number("coin")
    return (TRANSFER_POSTINGS.table_of(TransferPostings, payer=[amy, amy, bob], payee=[bob, bob, amy], currency=[coin] * 3,
                                       amount=[30.0, 500.0, 10.0], purpose_code=[0] * 3, purpose_reference=[0] * 3,
                                       batch=[0, 1, 2]),
            GOODS_MOVE_POSTINGS.table_of(GoodsMovePostings, giver=[], receiver=[], good=[], tile=[], receiver_tile=[], quantity=[],
                                         purpose_code=[], purpose_reference=[], batch=[]))


class ApplyPostingsTests(unittest.TestCase):
    def test_each_batch_has_its_own_outcome_and_a_refused_one_leaves_the_others_applied(self):
        book = funded_book()
        transfers, moves = three_batches(book)
        outcomes, _scratch = book.apply_postings(transfers, moves, 3)
        self.assertEqual((outcomes.code[:3].tolist(), book.balance("amy", "coin"), book.balance("bob", "coin")),
                         ([0, INSUFFICIENT_FUNDS, 0], 80.0, 20.0))

    def test_stopping_at_the_first_refusal_applies_only_what_came_before(self):
        book = funded_book()
        transfers, moves = three_batches(book)
        outcomes, _scratch = book.apply_postings(transfers, moves, 3, RULE_BATCH, stop_on_refusal=True)
        self.assertEqual((int(outcomes.row_count[0]), book.balance("amy", "coin"), book.balance("bob", "coin")), (2, 70.0, 30.0))

    def test_the_refusal_names_the_cause_and_the_cell(self):
        book = funded_book()
        transfers, moves = three_batches(book)
        outcomes, _scratch = book.apply_postings(transfers, moves, 3)
        refusal = book.refusal_of(outcomes, 1)
        self.assertEqual((refusal.cause, refusal.facts["agent"], refusal.facts["currency"], refusal.facts["batch"]),
                         ("insufficient_funds", "amy", "coin", 1))

    def test_a_goods_refusal_names_the_good_and_the_tile(self):
        book = funded_book()
        amy, bob, grain, tile = (book.agent_number("amy"), book.agent_number("bob"), book.good_number("grain"),
                                 book.tile_number("t1"))
        moves = GOODS_MOVE_POSTINGS.table_of(GoodsMovePostings, giver=[amy], receiver=[bob], good=[grain], tile=[tile],
                                             receiver_tile=[tile], quantity=[500.0], purpose_code=[0], purpose_reference=[0],
                                             batch=[0])
        transfers = TRANSFER_POSTINGS.table_of(TransferPostings, payer=[], payee=[], currency=[], amount=[], purpose_code=[],
                                               purpose_reference=[], batch=[])
        outcomes, _scratch = book.apply_postings(transfers, moves, 1)
        refusal = book.refusal_of(outcomes, 0)
        self.assertEqual((outcomes.code[0], refusal.cause, refusal.facts["good"], refusal.facts["tile"]),
                         (INSUFFICIENT_GOODS, "insufficient_goods", "grain", "t1"))


class RefusalMessageTests(unittest.TestCase):
    # presentation: the wording of the errors callers have always been shown
    def test_a_single_transfer_says_what_the_payer_holds_and_must_pay(self):
        book = funded_book()
        with self.assertRaises(InsufficientFunds) as raised:
            book.transfer(Transfer("amy", "bob", "coin", 500.0, "rent"))
        self.assertEqual(str(raised.exception), "amy holds 100 coin but must pay 500 (rent)")

    def test_a_batch_says_what_the_agent_would_hold_after_it(self):
        book = funded_book()
        with self.assertRaises(InsufficientFunds) as raised:
            book.transfer_many([Transfer("amy", "bob", "coin", 70.0, "x"), Transfer("amy", "bob", "coin", 70.0, "x")])
        self.assertEqual(str(raised.exception), "amy would hold -40 coin after the batch")

    def test_the_agent_named_is_the_first_by_name_among_those_overdrawn(self):
        book = funded_book()
        book.transfer(Transfer("edge:mint", "zoe", "coin", 1.0, "start"))
        with self.assertRaises(InsufficientFunds) as raised:
            book.transfer_many([Transfer("zoe", "bob", "coin", 5.0, "x"), Transfer("amy", "bob", "coin", 500.0, "x")])
        self.assertTrue(str(raised.exception).startswith("amy would hold"))

    def test_a_single_move_says_what_the_giver_holds_on_the_tile(self):
        book = funded_book()
        with self.assertRaises(InsufficientGoods) as raised:
            book.move(GoodsMove("amy", "bob", "grain", "t1", 90.0, "sale"))
        self.assertEqual(str(raised.exception), "amy holds 50 grain on t1 but must give 90 (sale)")

    def test_a_negative_single_transfer_tells_the_caller_to_reverse_it(self):
        with self.assertRaises(NegativeAmount) as raised:
            funded_book().transfer(Transfer("amy", "bob", "coin", -1.0, "oops"))
        self.assertEqual(str(raised.exception), "transfer of -1.0 coin (oops) is negative; reverse payer and payee")

    def test_a_negative_move_in_a_batch_names_the_move(self):
        with self.assertRaises(NegativeAmount) as raised:
            funded_book().post([], [GoodsMove("amy", "bob", "grain", "t1", -2.0, "oops")])
        self.assertEqual(str(raised.exception), "move of -2.0 grain (oops) is negative")


class SinglePostingTests(unittest.TestCase):
    def test_a_zero_transfer_does_nothing_and_makes_nobody_known(self):
        book = Book()
        book.transfer(Transfer("amy", "bob", "coin", 0.0, "x"))
        self.assertEqual(book.agents(), [])

    def test_a_delivered_move_lands_on_the_receivers_tile(self):
        book = funded_book()
        book.move(DeliveredMove("amy", "bob", "grain", "t1", 5.0, "sale", "t2"))
        self.assertEqual((book.stock("amy", "grain", "t1"), book.stock("bob", "grain", "t2"), book.stock("bob", "grain", "t1")),
                         (45.0, 5.0, 0.0))

    def test_purposes_come_back_as_their_text_in_the_goods_flow(self):
        book = funded_book()
        book.post([], [GoodsMove("amy", "bob", "grain", "t1", 5.0, "sale of grain"), GoodsMove("amy", "bob", "grain", "t1", 1.0, "wear")])
        self.assertEqual(book.goods_flow("grain"), {"sale of grain": 5.0, "start": 50.0, "wear": 1.0})


if __name__ == "__main__":
    unittest.main()
