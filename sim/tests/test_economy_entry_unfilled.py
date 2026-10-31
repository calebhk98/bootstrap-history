"""Complaint 559: a market starved by makers too small to supply it trades little, so the year's unfilled demand a newcomer's
full cost would meet is counted with the trade. `entry_backed.unfilled_at_cost` hands entry sizing, per recipe and market,
the bids a recipe's full cost per unit would still meet beyond what the market traded. The recipe's full cost is a recorder;
how entry sizes a newcomer from that figure is test_economy_entrant_sizing. No game."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import entry_backed
from sim.economy.types import Bid

COST = 1.0


def bid(floor, maximum_price):
    return Bid("buyer", "salt", "area", "tile", floor, 0.0, 1.0, 1.0, 1e9, maximum_price=maximum_price)


def unfilled(bids_by_market, traded_volume=200.0, costed=(("pan", COST),)):
    """The unfilled-at-cost function for a market whose bids are given, asked for the recipe "pan" at the market's tile."""
    view = types.SimpleNamespace(area_of=lambda good, tile: "area")
    with mock.patch.object(entry_backed, "recipes_by_cost", return_value=list(costed)) as by_cost:
        found = entry_backed.unfilled_at_cost(object(), object(), view, object(), bids_by_market,
                                              lambda good, tile: traded_volume)
        quantity = found("pan", "salt", "tile", 7.0) if found is not None else None
    return quantity, by_cost


class UnfilledAtCostTests(unittest.TestCase):
    BIDS = {("salt", "area"): [bid(500.0, 3.0), bid(400.0, 0.5)]}

    def test_with_no_bids_at_all_there_is_no_function(self):
        self.assertIsNone(entry_backed.unfilled_at_cost(None, None, None, None, {}, None))

    def test_the_bids_that_meet_the_recipes_cost_less_what_traded_are_unfilled(self):
        quantity, _by_cost = unfilled(self.BIDS)
        self.assertAlmostEqual(quantity, 300.0)

    def test_the_recipe_is_costed_at_the_markets_tile_for_that_good(self):
        _quantity, by_cost = unfilled(self.BIDS)
        self.assertEqual(by_cost.call_args.args[3:], ("salt", "tile", ["pan"], 7.0))

    def test_a_market_with_no_bids_has_none_unfilled(self):
        quantity, _by_cost = unfilled({("salt", "elsewhere"): [bid(500.0, 3.0)]})
        self.assertEqual(quantity, 0.0)

    def test_a_recipe_that_cannot_be_costed_backs_nothing(self):
        quantity, _by_cost = unfilled(self.BIDS, costed=())
        self.assertEqual(quantity, 0.0)

    def test_a_market_that_traded_nothing_is_unfilled_by_every_bid_at_the_cost(self):
        quantity, _by_cost = unfilled(self.BIDS, traded_volume=0.0)
        self.assertAlmostEqual(quantity, 500.0)


if __name__ == "__main__":
    unittest.main()
