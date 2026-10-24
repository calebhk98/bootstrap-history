"""The actors' purses and the economy's agents keep their money in one book: adopting the economy's book moves the
purses over, and each owner saves only its own currency. Each rule is called on a book and purses built here; the
economy's year with the actors' accounts in it is not tested through a year (the book's own rules are in test_book)."""

QUICK_TOPIC = True

import unittest

from sim.agents.purses import COIN, POOL, Purses
from sim.book import Book, Transfer

ECONOMY_UNIT = "economy_unit"


def economy_book():
    """A book holding only what the economy keeps: one household's money in the economy's own unit."""
    book = Book()
    book.transfer(Transfer("edge:mint", "household:one", ECONOMY_UNIT, 55.0, "opening"))
    return book


def purses_with_money():
    """Purses where one firm holds 130 and another owes 30 on its facility."""
    purses = Purses()
    purses.book.transfer(Transfer("edge:mint", "firm:b", COIN, 130.0, "opening"))
    purses.contracts.draw("firm:a", POOL, COIN, 30.0)
    return purses


class SharedBook(unittest.TestCase):
    def test_adopting_the_economys_book_moves_the_accounts_over(self):
        purses = purses_with_money()
        book = economy_book()
        purses.adopt_book(book)
        self.assertIs(purses.book, book)
        self.assertEqual(book.balance("firm:b", COIN), 130.0)
        self.assertEqual(book.balance("household:one", ECONOMY_UNIT), 55.0)
        self.assertEqual(purses.debt("firm:a"), 30.0)

    def test_the_purses_save_only_the_actors_currency(self):
        purses = purses_with_money()
        purses.adopt_book(economy_book())
        saved = purses.to_canon_dict()["book"]["money"]
        self.assertTrue(all(set(held) == {COIN} for held in saved.values()))
        self.assertIn("firm:b", saved)
        self.assertNotIn("household:one", saved)

    def test_a_book_record_leaves_a_skipped_currency_out(self):
        purses = purses_with_money()
        purses.adopt_book(economy_book())
        saved = purses.book.to_record(skip=(COIN,))["money"]
        self.assertTrue(all(COIN not in held for held in saved.values()))
        self.assertIn("household:one", saved)
        self.assertNotIn("firm:b", saved)

    def test_a_loaded_purses_record_joins_the_economys_book_again(self):
        record = {"book": {"money": {"edge:mint": {COIN: -130.0}, "firm:b": {COIN: 130.0}}, "goods": {},
                           "gross_money": {COIN: 130.0}, "gross_goods": {}, "money_by_purpose": {}, "goods_by_purpose": {},
                           "edge_money_volume": {}, "edge_money_net": {}, "edge_goods_volume": {}, "edge_goods_net": {},
                           "supply_at_start": {}},
                  "facilities": [{"contract_id": "facility:firm:a:pool:credit", "lender": POOL, "borrower": "firm:a",
                                  "currency": COIN, "principal": 30.0, "rate": 0.0, "years_left": 0.0,
                                  "collateral_value": 0.0, "arrears": 0.0, "issued_year": 0, "arrears_interest": 0.0,
                                  "kind": "facility", "collateral_tile": "", "collateral_share": 0.0}]}
        again = Purses.from_record(record)
        again.adopt_book(economy_book())
        self.assertEqual(again.purse("firm:b"), 130.0)
        self.assertEqual(again.debt("firm:a"), 30.0)


if __name__ == "__main__":
    unittest.main()
