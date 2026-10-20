"""Complaint 473: seeding a durable a cohort wants can move the cohort to a substitute (seeding raises the
wealth it spends from, so the first good drops out of its bids and another appears). The substitute is then
bid for as a whole stock the opening sizes its makers to build in year 0. Seeding follows the bids until
every durable a cohort wants is held."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import opening
from sim.economy.accounts import Book
from sim.economy.types import Bid

COHORT = types.SimpleNamespace(agent_id="household:a", tile="t")
FIRST, SUBSTITUTE = "stone", "brick"
STOCK = 800.0
WEAR = 10.0


def book_stock(book, good):
    return sum(book.holdings(COHORT.agent_id)["goods"].get(good, {}).values())


def bids_that_move_on(book):
    """Before the first good is held the cohort wants a stock of it; once it holds it, the wear of that and
    a whole stock of the substitute."""
    def bids(setup, record, view):
        held_first = book_stock(record.book, FIRST) > 0.0
        held_substitute = book_stock(record.book, SUBSTITUTE) > 0.0
        wanted = {}
        if not held_first:
            wanted[FIRST] = STOCK
        else:
            wanted[FIRST] = WEAR
            wanted[SUBSTITUTE] = WEAR if held_substitute else STOCK
        for good, quantity in wanted.items():
            yield COHORT, Bid(COHORT.agent_id, good, "area", COHORT.tile, quantity, 0.0, 1.0, 0.0, quantity), 1.0
    return bids


class SeedFollowsSubstitutesTests(unittest.TestCase):
    def test_a_durable_the_cohort_turns_to_after_the_first_seeding_is_seeded_too(self):
        book = Book()
        setup = types.SimpleNamespace(specs={FIRST: types.SimpleNamespace(service_life_years=80.0),
                                             SUBSTITUTE: types.SimpleNamespace(service_life_years=80.0)})
        record = types.SimpleNamespace(book=book)
        with mock.patch.object(opening, "_opening_bids", bids_that_move_on(book)):
            opening._seed_durable_stocks(setup, record, None)
            self.assertEqual(book_stock(book, SUBSTITUTE), STOCK)
            remaining = [bid for _cohort, bid, _price in opening._opening_bids(setup, record, None)]
        self.assertLessEqual(sum(bid.floor_quantity for bid in remaining), 2.0 * WEAR)

    def test_a_durable_already_held_is_not_seeded_again(self):
        book = Book()
        setup = types.SimpleNamespace(specs={FIRST: types.SimpleNamespace(service_life_years=80.0),
                                             SUBSTITUTE: types.SimpleNamespace(service_life_years=80.0)})
        record = types.SimpleNamespace(book=book)
        with mock.patch.object(opening, "_opening_bids", bids_that_move_on(book)):
            opening._seed_durable_stocks(setup, record, None)
        self.assertEqual(book_stock(book, FIRST), STOCK)


if __name__ == "__main__":
    unittest.main()
