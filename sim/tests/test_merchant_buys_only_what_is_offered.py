"""A merchant buys at a source only where something is on offer or it has its own expectation (Complaint 642); an area
whose only price is a bid ceiling, a cost quote or an old remembered price is still sold into."""

QUICK_TOPIC = True

import types
import unittest

import numpy as np

from sim.economy import merchants, merchants_book, merchants_search
from sim.tests.test_economy_merchants import SPECS, View, merchant, world


class OfferView:
    def __init__(self, offered):
        self.offered = offered

    def offered_price(self, good, area):
        return self.offered.get((good, area))


AREAS = [types.SimpleNamespace(area_id="a0"), types.SimpleNamespace(area_id="a1"), types.SimpleNamespace(area_id="a2")]


def rows_from(sources):
    count = len(sources)
    numbers = np.arange(count, dtype=np.float64)
    return merchants_book.MerchantRows(np.zeros(count, np.int64), np.array(sources, np.int64), np.zeros(count, np.int64),
                                       np.array(sources, np.int64), np.zeros(count, np.int64), numbers, numbers, numbers, numbers)


class UnofferedAreasTests(unittest.TestCase):
    def test_area_with_nothing_on_offer_and_no_expectation_is_closed(self):
        view = OfferView({("salt", "a0"): 2.0})
        self.assertEqual(merchants_search.unoffered_areas(view, "salt", AREAS, {}), {"a1", "a2"})

    def test_own_expectation_keeps_the_area_open(self):
        view = OfferView({("salt", "a0"): 2.0})
        self.assertEqual(merchants_search.unoffered_areas(view, "salt", AREAS, {"a1": 3.0}), {"a2"})


class BuyableSourcesTests(unittest.TestCase):
    def test_offered_or_expected_slots_are_buyable(self):
        offered = np.array([True, False, False])
        expected = np.array([np.nan, 5.0, np.nan])
        self.assertEqual(merchants_book.buyable_sources(offered, expected).tolist(), [True, True, False])

    def test_no_offered_array_means_every_slot(self):
        self.assertIsNone(merchants_book.buyable_sources(None, np.array([np.nan])))

    def test_rows_from_a_closed_source_are_dropped(self):
        rows = merchants_book.only_sources(rows_from([0, 1, 2, 1]), np.array([True, False, True]))
        self.assertEqual(rows.source_slot.tolist(), [0, 2])
        self.assertEqual(rows.rank.tolist(), [0.0, 2.0])

    def test_no_mask_keeps_the_rows(self):
        rows = rows_from([0, 1])
        self.assertIs(merchants_book.only_sources(rows, None), rows)


class NoOfferView(View):
    """Prices are shown, but nothing is on offer in the named areas."""
    def __init__(self, prices, closed):
        super().__init__(prices)
        self.closed = closed

    def offered_price(self, good, area):
        return None if area in self.closed else self.price(good, area)


class CandidateRoutesTests(unittest.TestCase):
    def routes(self, closed_in_a):
        carriage, area_map, area_a, area_b = world(("salt",))
        prices = {("salt", area_a["salt"]): 2.0, ("salt", area_b["salt"]): 4.0}
        view = NoOfferView(prices, {area_a["salt"]} if closed_in_a else set())
        return merchants.candidate_routes(merchant("m"), view, carriage, area_map, {}, SPECS, 0.05), area_a["salt"]

    def test_a_haul_from_an_area_with_only_a_shown_price_is_not_searched(self):
        rows, _area = self.routes(closed_in_a=True)
        self.assertEqual(rows, [])

    def test_the_same_prices_offered_give_the_haul(self):
        rows, area = self.routes(closed_in_a=False)
        self.assertEqual([row[2].area_id for row in rows], [area])


if __name__ == "__main__":
    unittest.main()
