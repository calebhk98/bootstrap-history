"""`posting_sequence.post_in_order` leaves the book as posting the steps one by one leaves it, and a refused step raises the book's
own error with the steps before it applied and the steps after it not."""
QUICK_TOPIC = True

import unittest

from sim.book import Book, GoodsMove, InsufficientFunds, Transfer
from sim.book_apply import RULE_BATCH, RULE_SINGLE
from sim.economy.posting_sequence import post_in_order


def funded_book():
    book = Book()
    book.transfer(Transfer("edge:mint", "amy", "coin", 100.0, "start"))
    book.move(GoodsMove("edge:production", "amy", "grain", "t1", 50.0, "start"))
    return book


def steps():
    return [([Transfer("amy", "zed", "coin", 30.0, "stake")], ()),
            ([Transfer("amy", "bob", "coin", 20.0, "stake"), Transfer("bob", "cat", "coin", 5.0, "dividend")], ()),
            ((), [GoodsMove("amy", "cat", "grain", "t1", 12.0, "stock")])]


class PostInOrder(unittest.TestCase):
    def test_the_book_ends_as_if_each_step_were_posted_on_its_own(self):
        for rule in (RULE_BATCH, RULE_SINGLE):
            together, apart = funded_book(), funded_book()
            post_in_order(together, steps(), rule)
            for transfers, moves in steps():
                apart.post(transfers, moves)
            for agent in ("amy", "bob", "cat", "zed"):
                self.assertEqual(together.balance(agent, "coin"), apart.balance(agent, "coin"))
                self.assertEqual(together.goods_of(agent), apart.goods_of(agent))
            self.assertEqual(together.agent_ids.name_list, apart.agent_ids.name_list)

    def test_a_refused_step_raises_with_the_earlier_steps_applied_and_the_later_ones_not(self):
        book = funded_book()
        sequence = [([Transfer("amy", "bob", "coin", 40.0, "stake")], ()), ([Transfer("amy", "bob", "coin", 500.0, "stake")], ()),
                    ([Transfer("amy", "cat", "coin", 10.0, "stake")], ())]
        with self.assertRaises(InsufficientFunds):
            post_in_order(book, sequence, RULE_SINGLE)
        self.assertEqual((book.balance("amy", "coin"), book.balance("bob", "coin"), book.balance("cat", "coin")), (60.0, 40.0, 0.0))

    def test_no_steps_do_nothing(self):
        book = funded_book()
        post_in_order(book, [])
        post_in_order(book, [((), ()), ([], [])])
        self.assertEqual(book.balance("amy", "coin"), 100.0)


if __name__ == "__main__":
    unittest.main()
