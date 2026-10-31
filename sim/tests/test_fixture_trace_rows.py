"""The fixture spin-up trace's row: the year's macro figures and the money each kind of holder keeps, read from the
economy's book with the edge accounts left out."""

QUICK_TOPIC = True

import types
import unittest

from sim.book import Book, Transfer
from sim.markets.port_trace_holders import HOLDER_COLUMNS, holder_kind, money_by_holder_columns
from sim.ui.spin_up_fixture_trace import fixture_row

COIN = "coin"
LABOURER, GRAIN = "labourer", "grain_kg"


def book_with_money():
    book = Book()
    book.transfer(Transfer("edge:mint", "household:town:0", COIN, 10.0, "mint"))
    book.transfer(Transfer("edge:mint", "producer:grow_grain@farms", COIN, 4.0, "mint"))
    book.transfer(Transfer("edge:mint", "merchant:0", COIN, 2.0, "mint"))
    book.transfer(Transfer("edge:mint", "state:fixture", COIN, 1.0, "mint"))
    book.transfer(Transfer("edge:mint", "bank:0", COIN, 0.5, "mint"))
    book.transfer(Transfer("household:town:0", "producer:grow_grain@farms", COIN, 3.0, "buy grain"))
    book.transfer(Transfer("edge:consumption", "household:town:0", COIN, 7.0, "gift"))
    return book


def fake_economy(book):
    return types.SimpleNamespace(record=types.SimpleNamespace(book=book), setup=types.SimpleNamespace(currency_id=COIN))


def fake_outcome(wage, grain_price):
    return types.SimpleNamespace(
        basket_price_level=1.25, wages={LABOURER: wage}, prices={GRAIN: grain_price}, hired_hours=800.0,
        idle_hours=200.0, rate=0.05, money_supply=24.5, hunger_by_tile={"town": 2.0, "farms": 0.5})


class HolderKindTests(unittest.TestCase):
    def test_the_prefix_before_the_colon_names_the_column(self):
        self.assertEqual(holder_kind("household:town:2"), "money_households")
        self.assertEqual(holder_kind("producer:dig_ore@hills"), "money_producers")
        self.assertEqual(holder_kind("merchant:0"), "money_merchants")
        self.assertEqual(holder_kind("state:fixture"), "money_state")
        self.assertEqual(holder_kind("bank:3"), "money_banks")

    def test_any_other_account_is_money_other(self):
        self.assertEqual(holder_kind("fund:7"), "money_other")


class MoneyByHolderTests(unittest.TestCase):
    def test_each_kind_holds_the_money_posted_to_its_accounts(self):
        columns = money_by_holder_columns(book_with_money(), COIN)
        self.assertEqual(tuple(columns), HOLDER_COLUMNS)
        self.assertAlmostEqual(columns["money_households"], 14.0)
        self.assertAlmostEqual(columns["money_producers"], 7.0)
        self.assertAlmostEqual(columns["money_merchants"], 2.0)
        self.assertAlmostEqual(columns["money_state"], 1.0)
        self.assertAlmostEqual(columns["money_banks"], 0.5)
        self.assertAlmostEqual(columns["money_other"], 0.0)

    def test_the_edge_accounts_are_left_out(self):
        columns = money_by_holder_columns(book_with_money(), COIN)
        self.assertAlmostEqual(sum(columns.values()), 24.5)


class FixtureRowTests(unittest.TestCase):
    def test_the_row_reads_prices_wages_and_hours_and_the_real_wage(self):
        row = fixture_row(fake_economy(book_with_money()), fake_outcome(wage=1.0, grain_price=0.25), 3, [(100.0, 100.0, 75.0)])
        self.assertEqual(row["year"], 3)
        self.assertEqual(row["basket_price_level"], 1.25)
        self.assertEqual(row["unskilled_wage"], 1.0)
        self.assertEqual(row["staple_price"], 0.25)
        self.assertAlmostEqual(row["real_wage"], 4.0)
        self.assertEqual(row["hired_hours"], 800.0)
        self.assertEqual(row["idle_hours"], 200.0)
        self.assertEqual(row["rate"], 0.05)
        self.assertEqual(row["money_supply"], 24.5)
        self.assertAlmostEqual(row["hunger"], 2.5)
        self.assertAlmostEqual(row["money_households"], 14.0)

    def test_a_missing_price_gives_no_real_wage_rather_than_zero(self):
        row = fixture_row(fake_economy(book_with_money()), fake_outcome(wage=1.0, grain_price=0.0), 0, [(100.0, 100.0, 75.0)])
        self.assertIsNone(row["real_wage"])


if __name__ == "__main__":
    unittest.main()
