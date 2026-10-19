"""Complaint 502: the state's bids for the goods of a need split the need's budget as a household's do: past the
reference price a dearer good draws less than a fixed sum (the basket's elasticity of substitution), so a seller
that raises its ask loses sales instead of keeping the same revenue on fewer units. The need's budget is unchanged."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import households_basket, state_budget
from sim.economy.goods_market import quantity_at
from sim.world import need_basket
from sim.world.need_basket import Basket, NeedSpec

CHEAP, DEAR, TILE, AREA = "cheap_kg", "dear_kg", "capital", "area"
PRICES = {CHEAP: 3.0, DEAR: 5.0}
EFFECT = {CHEAP: 1.0, DEAR: 0.9}
SUBSTITUTION = 2.0
BUDGET = 1000.0


class Holdings:
    def holdings(self, agent):
        return {"goods": {}}

    def move_many(self, moves):
        pass


def state_bids(**budget_fields):
    need = NeedSpec("implements", 0.0, 1.0, tuple(EFFECT.items()))
    basket = Basket((need,), SUBSTITUTION, {"implements": {}})
    setup = types.SimpleNamespace(capital_tile=TILE, state_agent="state", basket_for=lambda tile: basket)
    record = types.SimpleNamespace(state_budget=state_budget.StateBudget(goods_budget=BUDGET, **budget_fields), book=Holdings())
    view = types.SimpleNamespace(area_of=lambda good, tile: AREA)
    area_map = types.SimpleNamespace(goods=lambda: set(PRICES))
    order_book = {}
    priced = need_basket.need_prices(basket, PRICES.get)
    with mock.patch.object(households_basket, "need_prices", return_value=priced):
        state_budget.goods_bids(setup, record, view, area_map, order_book)
    return {good: order_book[(good, AREA)][0][0] for good in PRICES}


class StateNeedBidTests(unittest.TestCase):
    def test_the_need_budget_is_spent_in_full_at_the_reference_prices(self):
        bids = state_bids()
        self.assertAlmostEqual(sum(bid.budget for bid in bids.values()), BUDGET)
        self.assertAlmostEqual(sum(quantity_at(bid, bid.reference_price) * bid.reference_price
                                   for bid in bids.values()), BUDGET)

    def test_the_bid_carries_the_elasticity_of_substitution(self):
        for bid in state_bids().values():
            self.assertEqual(bid.elasticity, SUBSTITUTION)

    def test_a_dearer_good_draws_a_smaller_spend(self):
        for bid in state_bids().values():
            now = quantity_at(bid, bid.reference_price) * bid.reference_price
            dearer = quantity_at(bid, 2.0 * bid.reference_price) * 2.0 * bid.reference_price
            self.assertLess(dearer, 0.75 * now)


class StateProgrammeBidTests(unittest.TestCase):
    """A stated real spending programme buys quantities, not a sum: when the price level rises the state
    keeps spending its budget on them (up to the budget), so printed money reaches prices instead of
    sitting in the treasury while the bids shrink with the price."""

    def test_a_dearer_good_still_draws_the_whole_budget_share(self):
        for bid in state_bids(real_programme=True).values():
            dearer = quantity_at(bid, 5.0 * bid.reference_price) * 5.0 * bid.reference_price
            self.assertAlmostEqual(dearer, bid.budget)

    def test_the_quantity_wanted_at_the_reference_price_is_unchanged(self):
        plain, programme = state_bids(), state_bids(real_programme=True)
        for good in PRICES:
            self.assertAlmostEqual(quantity_at(programme[good], PRICES[good]), quantity_at(plain[good], PRICES[good]))


if __name__ == "__main__":
    unittest.main()
