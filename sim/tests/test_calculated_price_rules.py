"""The plain rules behind the prices module's calculated-goods views and the markets' border terms."""

QUICK_TOPIC = True

import unittest

from sim.agents import relations
from sim.markets import trade_duty
from sim.prices import rules
from sim.tests.store_stand_in import base_book


class MoneyPrices(unittest.TestCase):

    def test_a_labour_hour_price_is_stated_in_the_coin_of_an_hour(self):
        self.assertEqual(rules.money_prices({"wheat": 2.0, "iron": 5.0}, 3.0), {"wheat": 6.0, "iron": 15.0})

    def test_an_empty_table_stays_empty(self):
        self.assertEqual(rules.money_prices({}, 3.0), {})


class SolvedMaterials(unittest.TestCase):

    def test_only_materials_made_with_the_held_techniques_are_solved(self):
        provenance = {"wheat": "solved", "steel": "gated", "wool": "solved"}
        self.assertEqual(rules.solved_materials(provenance), frozenset({"wheat", "wool"}))


class TermsInBook(unittest.TestCase):

    def test_a_country_with_no_record_charges_nothing_and_does_not_embargo(self):
        self.assertEqual(trade_duty.terms_in_book(base_book(), "rome", "partner"), (0.0, False))

    def test_a_set_tariff_and_embargo_are_read_back(self):
        book = base_book()
        relations.set_side(book, "rome", "partner", tariff=0.2, embargo=True)
        self.assertEqual(trade_duty.terms_in_book(book, "rome", "partner"), (0.2, True))
        self.assertEqual(trade_duty.terms_in_book(book, "partner", "rome"), (0.0, False))


if __name__ == "__main__":
    unittest.main()
