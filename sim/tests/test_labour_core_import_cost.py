"""A labour market with far more hours bid than offered cannot quote above what bringing the trade's workers
in from a neighbouring area costs: that area's wage plus the move spread over a career. Without it the wage
climbs toward the top bid however few hours trade (Complaint 473). Plain records, no game."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing, trades
from sim.labour.market.records import Bid, MarketState, Route, YearInputs

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0}})
HOURS = 100.0
SUBSISTENCE = 100.0      # a reservation wage of one an hour
NEIGHBOUR_WAGE = 1.0
MOVING_COST = 100.0
GREAT_BID = 1000.0
YEARS = 12
ENOUGH_HANDS = 1.0e5      # their hours exceed the million the market bids
FEW_HANDS = 50.0


def inputs(bids, routes):
    return YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={"vale": SUBSISTENCE, "dale": SUBSISTENCE},
                      hours_per_worker_year=HOURS, discount_rate=0.03, career_years=30.0, routes=routes)


def state(neighbour_workers=ENOUGH_HANDS):
    held = MarketState(workers={"vale": {"digger": [10.0, 0.0, 0.0, 0.0, 0.0]},
                                "dale": {"digger": [neighbour_workers, 0.0, 0.0, 0.0, 0.0]}})
    held.wages = {"vale": {"digger": 1.0}, "dale": {"digger": NEIGHBOUR_WAGE}}
    return held


def swamped_bids():
    return [Bid("works", "digger", "vale", 1.0e6, GREAT_BID)]     # a thousand times the hours offered


def vale_wage(held, routes):
    found = None
    for _year in range(YEARS):
        found = [each for each in clearing.clear_all(held, inputs(swamped_bids(), routes)) if each.area == "vale"][0]
    return found.wage


class ImportCostTests(unittest.TestCase):

    def test_a_swamped_market_with_neighbours_who_have_enough_spare_hands_stays_near_their_wage_plus_the_move(self):
        wage = vale_wage(state(), {"vale": [Route("dale", MOVING_COST)]})
        self.assertLess(wage, 2.5 * NEIGHBOUR_WAGE)      # the thousandth of the hours the spot supplies is priced by the bid
        self.assertGreater(wage, NEIGHBOUR_WAGE)

    def test_a_dearer_move_allows_a_higher_wage(self):
        near = vale_wage(state(), {"vale": [Route("dale", MOVING_COST)]})
        far = vale_wage(state(), {"vale": [Route("dale", 20.0 * MOVING_COST)]})
        self.assertGreater(far, near)

    def test_with_no_route_out_the_wage_still_follows_the_bids(self):
        self.assertGreater(vale_wage(state(), {}), 100.0)

    def test_a_neighbour_without_the_trade_gives_nothing_to_import(self):
        self.assertGreater(vale_wage(state(neighbour_workers=0.0), {"vale": [Route("dale", MOVING_COST)]}), 100.0)

    def test_hands_beyond_an_empty_area_are_reached_through_it(self):
        routes = {"vale": [Route("glen", MOVING_COST)], "glen": [Route("dale", MOVING_COST)]}
        wage = vale_wage(state(), routes)
        self.assertLess(wage, 2.5 * NEIGHBOUR_WAGE)      # the thousandth of the hours the spot supplies is priced by the bid
        self.assertGreater(wage, vale_wage(state(), {"vale": [Route("dale", MOVING_COST)]}))

    def test_the_cap_never_undercuts_what_the_workers_ask(self):
        held = state()
        held.wages["dale"]["digger"] = 0.1       # a glut next door: the move is cheap, but the ask is one an hour
        self.assertGreaterEqual(vale_wage(held, {"vale": [Route("dale", MOVING_COST)]}), 1.0)

    def test_a_swamped_market_whose_neighbours_have_few_spare_hands_is_not_held_at_their_wage(self):
        wage = vale_wage(state(neighbour_workers=FEW_HANDS), {"vale": [Route("dale", MOVING_COST)]})
        self.assertGreater(wage, 100.0)

    def test_a_neighbour_whose_own_employers_want_all_its_hands_has_none_to_import(self):
        # both areas swamped: neither can fetch from the other, so the wage follows the bids in each
        bids = swamped_bids() + [Bid("works", "digger", "dale", 1.0e6, GREAT_BID)]
        routes = {"vale": [Route("dale", MOVING_COST)], "dale": [Route("vale", MOVING_COST)]}
        held = state(neighbour_workers=FEW_HANDS)
        for _year in range(YEARS):
            found = clearing.clear_all(held, inputs(bids, routes))
        self.assertGreater(min(each.wage for each in found), 100.0)


if __name__ == "__main__":
    unittest.main()
