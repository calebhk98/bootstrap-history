"""Complaint 507, stage 7 of the one-price-owner plan: a seller left holding unsold stock lowers its ask inside
the year's clearing and the market clears again, until the stock sells or the ask reaches what a unit is worth
to the seller unsold (never below what it costs to make). Sellers that sold out are not revisited."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import goods_market, seller_offers, unsold_search
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE = "alloy", "area", "tile"
COST = 2.0 * 3.0 + 4.0 * 0.5      # two of metal at three, four hours at half


class View:
    def interest_rate(self, currency):
        return 0.0

    def currency_of(self, area):
        return "coin"

    year = 3

    def price(self, good, area):
        return {"metal": 3.0}.get(good)

    def wage(self, trade, area):
        return 0.5

    def area_of(self, good, tile):
        return AREA

    def stock(self, agent, good, tile):
        return 0.0


def game(*sellers, workshops=1):
    recipe = Recipe("melt", {GOOD: 1.0}, {"metal": 2.0}, {"labour": 4.0})
    producers = {name: Producer(name, "lord", "melt", TILE, 10.0, workshops=workshops) for name in sellers}
    basket = types.SimpleNamespace(substitution=1.0)
    setup = types.SimpleNamespace(specs={}, recipes={"melt": recipe}, basket_for=lambda tile: basket)
    return setup, types.SimpleNamespace(producers=producers, memory=types.SimpleNamespace(volume_weights={GOOD + "|" + AREA: 100.0}), unmet={})


def buyer(quantity, maximum_price):
    """Takes `quantity` at any price up to `maximum_price`."""
    return Bid("buyer", GOOD, AREA, TILE, quantity, 0.0, maximum_price, 0.0, 1e12, 0, maximum_price)


def offer(seller, quantity, ask):
    return Offer(seller, GOOD, AREA, TILE, quantity, ask)


def searched(bids, offers, last_price=None, workshops=1):
    setup, record = game(*{each.seller for each in offers}, workshops=workshops)
    chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, last_price)
    final, result = unsold_search.clear_with_search(setup, record, View(), bids, offers, chosen, GOOD, AREA, "coin", last_price)
    return {each.seller: each for each in final}, result


def sold(result, seller):
    return sum(fill.quantity for fill in result.fills if fill.side == "sell" and fill.agent == seller)


class UnsoldStockSearchTests(unittest.TestCase):
    def test_unsold_stock_sells_within_year(self):
        final, result = searched([buyer(100.0, 1.5 * COST)], [offer("a", 100.0, 5.0 * COST)])
        self.assertAlmostEqual(sold(result, "a"), 100.0)
        self.assertLessEqual(final["a"].reservation_price, 1.5 * COST)

    def test_a_good_opened_far_above_making_cost_reaches_buyers_in_one_year(self):
        final, result = searched([buyer(100.0, 1.2 * COST)], [offer("a", 100.0, 500.0 * COST)])
        self.assertGreater(sold(result, "a"), 99.0)
        self.assertGreaterEqual(final["a"].reservation_price, COST)

    def test_no_ask_ends_below_the_sellers_floor(self):
        final, result = searched([buyer(100.0, 0.5 * COST)], [offer("a", 100.0, 5.0 * COST)])
        self.assertAlmostEqual(final["a"].reservation_price, COST)
        self.assertEqual(sold(result, "a"), 0.0)

    def test_the_ask_stops_at_the_price_that_sells_not_at_the_floor(self):
        # three quarters of the cost is metal bought in, so the band above cost is 1.5 times it (ask_adjust.band_edge)
        final, _result = searched([buyer(100.0, 1.45 * COST)], [offer("a", 100.0, 5.0 * COST)])
        self.assertGreater(final["a"].reservation_price, 1.2 * COST)

    def test_a_seller_that_sold_out_keeps_its_ask(self):
        setup, record = game("a")
        bids = [buyer(100.0, 4.0 * COST)]
        offers = [offer("a", 100.0, 1.2 * COST)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, None)
        final, result = unsold_search.clear_with_search(setup, record, View(), bids, offers, chosen,
                                                        GOOD, AREA, "coin", None)
        self.assertEqual(final, chosen)
        self.assertAlmostEqual(sold(result, "a"), 100.0)

    def test_price_takers_with_more_stock_than_buyers_want_come_down_together_to_their_floor(self):
        final, result = searched([buyer(150.0, 4.0 * COST)],
                                 [offer("cheap", 100.0, 1.2 * COST), offer("dear", 100.0, 5.0 * COST)], workshops=2)
        self.assertAlmostEqual(result.quantity, 150.0)
        self.assertAlmostEqual(final["cheap"].reservation_price, COST)
        self.assertAlmostEqual(final["dear"].reservation_price, COST)

    def test_a_seller_that_moves_the_price_and_holds_units_back_on_purpose_is_not_searched(self):
        final, result = searched([buyer(150.0, 4.0 * COST)],
                                 [offer("cheap", 100.0, 1.2 * COST), offer("dear", 100.0, 5.0 * COST)])
        self.assertGreater(final["dear"].reservation_price, 1.2 * COST)
        self.assertLess(sold(result, "dear"), 100.0)

    def test_a_market_that_sells_out_with_no_excess_demand_is_left_as_chosen(self):
        setup, record = game("a")
        bids = [buyer(50.0, 4.0 * COST)]
        offers = [offer("a", 50.0, 1.2 * COST)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, None)
        final, _result = unsold_search.clear_with_search(setup, record, View(), bids, offers, chosen,
                                                         GOOD, AREA, "coin", None)
        self.assertEqual(final, chosen)

    def test_a_seller_that_sells_out_with_buyers_turned_away_asks_up_to_the_buyers_ceiling(self):
        setup, record = game("a")
        bids = [buyer(100.0, 1.45 * COST)]
        offers = [offer("a", 50.0, 1.2 * COST)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, None)
        final, _result = unsold_search.clear_with_search(setup, record, View(), bids, offers, chosen,
                                                         GOOD, AREA, "coin", None)
        self.assertAlmostEqual(final[0].reservation_price, 1.45 * COST, delta=0.01 * COST)

    def test_a_seller_turned_buyers_away_asks_no_more_than_the_band_above_its_cost(self):
        setup, record = game("a")
        bids = [buyer(100.0, 40.0 * COST)]
        offers = [offer("a", 50.0, 1.2 * COST)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, None)
        final, _result = unsold_search.clear_with_search(setup, record, View(), bids, offers, chosen,
                                                         GOOD, AREA, "coin", None)
        limit = unsold_search.ask_limits(setup, record, View(), offers, [0], {})[0]
        self.assertAlmostEqual(final[0].reservation_price, limit, delta=0.01 * limit)
        self.assertLess(limit, 40.0 * COST)

    def crossings_for(self, view, bids, asks):
        """How many market crossings one search makes for sellers asking `asks` under `view`."""
        offers = [offer("a", 100.0, ask) for ask in asks]
        setup, record = game("a")
        counted, original = [0], goods_market._crossing

        def counting(*arguments, **keywords):
            counted[0] += 1
            if counted[0] > 5000:
                raise RuntimeError("search did not converge")
            return original(*arguments, **keywords)

        goods_market._crossing = counting
        try:
            unsold_search.clear_with_search(setup, record, view, bids, offers, offers, GOOD, AREA, "coin", 100.0)
        finally:
            goods_market._crossing = original
        return counted[0]

    def test_the_search_is_bounded_by_its_precision_when_a_unit_costs_nothing_to_make(self):
        class Free(View):
            def price(self, good, area):
                return 0.0

            def wage(self, trade, area):
                return 0.0

        # the bracket is [0, ask] and halves each trial: about log2(1 / precision) trials plus the fixed few
        bound = math.ceil(math.log2(1.0 / unsold_search.SEARCH_PRECISION)) + 6
        self.assertLessEqual(self.crossings_for(Free(), [], [150.0]), bound)

    def test_the_search_is_bounded_when_the_floor_is_far_below_the_ask(self):
        class Nearly(View):
            def price(self, good, area):
                return 0.0

            def wage(self, trade, area):
                return 1e-274

        # the log of the ratio of ask to floor halves each trial, so the count grows with its log, not the ratio
        ratio = math.log(150.0 / 4e-274)
        bound = math.ceil(math.log2(ratio / unsold_search.SEARCH_PRECISION)) + 6
        self.assertLessEqual(self.crossings_for(Nearly(), [], [150.0]), bound)


if __name__ == "__main__":
    unittest.main()
