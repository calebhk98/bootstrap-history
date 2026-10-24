"""Complaint 512: a standing bid for a good no one makes (a fixed quantity, no price schedule, as a merchant's
replacement carriers or a project's draw are) is demand firm entry sees: a maker enters when the recipe pays at
the price the bid offers. The bid's demand and the founder's draws becoming bids: test_standing_bids_rule."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy.standing_demand import with_standing_bids
from sim.economy.types import Bid, GoodSpec, Recipe
from sim.tests import economy_fixture as fixture

GADGET, MAKE_GADGET = "gadget", "make_gadget"
UNITS_WANTED = 4.0


def gadget_setup(price=400.0):
    specs = dict(fixture.specs())
    specs[GADGET] = GoodSpec(GADGET, 20.0, 0.0, 0.0, "carrier")
    recipes = dict(fixture.recipes())
    recipes[MAKE_GADGET] = Recipe(MAKE_GADGET, {GADGET: 1.0}, {fixture.METAL: 1.0}, {fixture.SMITH: 40.0})
    base = fixture.small_setup()
    return dataclasses.replace(base, specs=specs, recipes=recipes,
                               opening_prices=dict(base.opening_prices, **{GADGET: price}))


class StandingBidsJoinTests(unittest.TestCase):
    """Demand settled outside the book (the founder's project draws) is read by entry as bids and clears nothing. That entry
    plans a maker for a bid's demand is test_economy_entry_trial; the bid's demand and the founder's draws becoming bids:
    test_standing_bids_rule."""

    def bid(self, area="area"):
        return Bid("standing:founder", GADGET, area, "tile", UNITS_WANTED, 0.0, 400.0, 0.0, UNITS_WANTED * 400.0)

    def test_a_standing_bid_joins_the_bids_of_its_market(self):
        household = Bid("household", GADGET, "area", "tile", 1.0, 0.0, 400.0, 0.0, 400.0)
        joined = with_standing_bids({(GADGET, "area"): [household]}, [self.bid()])
        self.assertEqual(joined[(GADGET, "area")], [household, self.bid()])

    def test_a_standing_bid_for_a_market_with_no_bids_opens_that_market(self):
        self.assertEqual(with_standing_bids({}, [self.bid("other")]), {(GADGET, "other"): [self.bid("other")]})

    def test_without_standing_bids_the_markets_bids_are_unchanged_and_a_copy(self):
        bids = {(GADGET, "area"): [self.bid()]}
        joined = with_standing_bids(bids, [])
        self.assertEqual(joined, bids)
        self.assertIsNot(joined[(GADGET, "area")], bids[(GADGET, "area")])


if __name__ == "__main__":
    unittest.main()
