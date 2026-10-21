"""Complaint 649: the merchants' carried flows are kept by good and tile pair, valued at the price of each end, and a
country's trade book is read off them. The rules are called on built inputs."""

QUICK_TOPIC = True

import unittest

from sim.economy import carried_book, country_figures
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.types import CurrencySpec
from sim.economy.record import EconomyRecord
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_carriage_hours import trading_setup

COUNTRY_OF = {"a1": "home", "a2": "home", "b1": "north"}.get


class CarriedBookTests(unittest.TestCase):
    def test_a_flow_is_kept_by_good_and_pair_at_each_ends_price(self):
        carried = {}
        carried_book.note_carried(carried, "grain", "a1", "b1", units=10.0, tonnes=2.0, price_at_origin=3.0, price_at_destination=5.0)
        carried_book.note_carried(carried, "grain", "a1", "b1", units=5.0, tonnes=1.0, price_at_origin=3.0, price_at_destination=5.0)
        self.assertEqual(carried, {"grain": {"a1": {"b1": [3.0, 45.0, 75.0]}}})

    def test_an_end_without_a_price_takes_the_other_ends(self):
        carried = {}
        carried_book.note_carried(carried, "grain", "a1", "b1", 10.0, 2.0, None, 5.0)
        carried_book.note_carried(carried, "salt", "a1", "b1", 10.0, 2.0, None, None)
        self.assertEqual(carried["grain"]["a1"]["b1"], [2.0, 50.0, 50.0])
        self.assertEqual(carried["salt"]["a1"]["b1"], [2.0, 0.0, 0.0])

    def test_a_stay_or_an_empty_haul_is_not_kept(self):
        carried = {}
        carried_book.note_carried(carried, "grain", "a1", "a1", 10.0, 2.0, 3.0, 3.0)
        carried_book.note_carried(carried, "grain", "a1", "b1", 0.0, 0.0, 3.0, 3.0)
        self.assertEqual(carried, {})

    def test_imports_are_worth_the_landed_price_and_exports_the_price_at_the_door(self):
        carried = {"grain": {"a1": {"b1": [2.0, 30.0, 50.0], "a2": [9.0, 1.0, 1.0]}},
                   "iron": {"b1": {"a1": [1.0, 40.0, 70.0]}}}
        north = carried_book.trade_book(carried, COUNTRY_OF, "north")
        self.assertEqual(north, {"grain": {"in_tonnes": 2.0, "in_value": 50.0, "out_tonnes": 0.0, "out_value": 0.0},
                                 "iron": {"in_tonnes": 0.0, "in_value": 0.0, "out_tonnes": 1.0, "out_value": 40.0}})
        home = carried_book.trade_book(carried, COUNTRY_OF, "home")
        self.assertEqual(carried_book.trade_value(home, "in"), 70.0)
        self.assertEqual(carried_book.trade_value(home, "out"), 30.0)     # the haul between two home tiles crossed no border
        self.assertEqual(carried_book.trade_book(carried, COUNTRY_OF, "nowhere"), {})

    def test_the_record_saves_the_flows_by_good_and_they_add_up_to_the_tonnes(self):
        carried_goods = {}
        carried_book.note_carried(carried_goods, "grain", "a1", "b1", 10.0, 2.0, 3.0, 5.0)
        carried_book.note_carried(carried_goods, "salt", "a1", "b1", 4.0, 1.0, 2.0, 6.0)
        carried_book.note_carried(carried_goods, "grain", "b1", "a2", 5.0, 1.5, 4.0, 3.0)
        record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec("coin", "fiat", None, 0.0, None))
        record.carried_goods = carried_goods
        record.carried = {"a1": {"b1": 3.0}, "b1": {"a2": 1.5}}
        for origin, row in record.carried.items():
            for destination, tonnes in row.items():
                by_good = sum(by_origin.get(origin, {}).get(destination, [0.0])[0] for by_origin in record.carried_goods.values())
                self.assertAlmostEqual(by_good, tonnes, places=9)
        again = EconomyRecord.from_record(record.to_record())
        self.assertEqual(again.carried_goods, record.carried_goods)

    def test_no_country_means_no_border(self):
        economy = fixture.run(fixture.two_country_setup(), years=1)[0]
        self.assertEqual(country_figures.trade_book(economy, None), {})
        self.assertEqual(country_figures.trade_book(economy, "nowhere"), {})


if __name__ == "__main__":
    unittest.main()
