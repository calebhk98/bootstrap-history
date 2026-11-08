"""The book's storage (sim/book_store.py): ids admitted in sorted batches, flags set at admission, growth, numbering saved."""
QUICK_TOPIC = True

import unittest

from sim.book import Book, GoodsMove, InsufficientFunds, Transfer


class AdmitAgentsTests(unittest.TestCase):
    def test_a_batch_of_new_agents_is_numbered_in_sorted_order(self):
        book = Book()
        self.assertEqual(book._admit_agents(["zed", "amy", "kim"]), [2, 0, 1])

    def test_a_later_agent_continues_the_numbering(self):
        book = Book()
        book._admit_agents(["b", "c"])
        self.assertEqual(book.agent_number("a"), 2)

    def test_flags_are_set_from_the_name_at_admission(self):
        book = Book()
        edge, mint, external, plain = book._admit_agents(["edge:wear", "edge:mint", "edge:external:far", "producer:flour@rome"])
        flags = book.agent_table
        self.assertEqual([(int(flags.is_edge[number]), int(flags.is_mint[number]), int(flags.is_external[number]))
                          for number in (edge, mint, external, plain)], [(1, 0, 0), (1, 1, 0), (1, 0, 1), (0, 0, 0)])

    def test_the_kind_is_the_text_before_the_first_colon(self):
        book = Book()
        edge, producer, founder = book._admit_agents(["edge:wear", "producer:flour@rome", "founder"])
        kinds = [book.kind_ids.name(int(book.agent_table.kind[number])) for number in (edge, producer, founder)]
        self.assertEqual(kinds, ["edge", "producer", ""])

    def test_growing_past_the_first_capacity_keeps_earlier_agents_flags(self):
        book = Book()
        book.agent_number("edge:first")
        book._admit_agents(["agent%03d" % number for number in range(300)])
        self.assertEqual(int(book.agent_table.is_edge[0]), 1)


class KnownTests(unittest.TestCase):
    def test_an_agent_named_only_in_a_refused_batch_is_not_known(self):
        book = Book()
        with self.assertRaises(InsufficientFunds):
            book.post([Transfer("broke", "stranger", "coin", 5.0, "x")], [])
        self.assertEqual((book.knows("broke"), book.knows("stranger"), book.agents()), (False, False, []))

    def test_a_posted_agent_is_known(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "amy", "coin", 5.0, "x"))
        self.assertEqual(book.agents(), ["amy", "edge:mint"])


class CurrencyGrowthTests(unittest.TestCase):
    def test_admitting_more_currencies_than_the_stride_keeps_every_balance(self):
        book = Book()
        for number in range(7):
            book.transfer(Transfer("edge:mint", "amy%d" % (number % 3), "money%d" % number, 10.0 + number, "x"))
        self.assertEqual([book.balance("amy%d" % (number % 3), "money%d" % number) for number in range(7)],
                         [10.0 + number for number in range(7)])

    def test_the_stride_doubles_when_the_currencies_outgrow_it(self):
        book = Book()
        first = book.stride
        book._admit_currencies(["c%d" % number for number in range(first + 1)])
        self.assertEqual(book.stride, 2 * first)


class NumberingTests(unittest.TestCase):
    def test_a_loaded_book_numbers_every_name_as_the_live_book_did(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "zed", "coin", 5.0, "sale of wheat"))
        book.move(GoodsMove("edge:production", "amy", "iron", "t9", 3.0, "output"))
        book.transfer(Transfer("zed", "amy", "coin", 1.0, "x"))
        loaded = Book.from_record(book.to_record())
        self.assertEqual(loaded.numbering_state(), book.numbering_state())

    def test_the_numbering_is_in_arrival_order_not_sorted_order_after_a_load(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "zed", "coin", 5.0, "x"))
        book.transfer(Transfer("edge:mint", "amy", "coin", 5.0, "x"))
        loaded = Book.from_record(book.to_record())
        self.assertEqual((book.agent_ids.state(), loaded.agent_ids.state()),
                         (["edge:mint", "zed", "amy"], ["edge:mint", "zed", "amy"]))

    def test_a_record_without_numbering_still_loads(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "amy", "coin", 5.0, "x"))
        record = book.to_record()
        del record["numbering"]
        self.assertEqual(Book.from_record(record).balance("amy", "coin"), 5.0)

    def test_a_filtered_record_leaves_the_numbering_out(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "amy", "coin", 5.0, "x"))
        self.assertNotIn("numbering", book.to_record(only=("coin",)))


if __name__ == "__main__":
    unittest.main()
