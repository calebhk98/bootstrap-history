"""The labour core clears a market whose hours sold rise with the wage (Complaints 473, 608): a small excess of hours
moves the wage a little, where hours all offered at the ask move it all the way to the ask."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.labour.market import clearing, trades
from sim.labour.market.records import Bid, MarketState, YearInputs

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0}})
HOURS, PEOPLE = 100.0, 10.0       # a thousand hours a year; reservation wage one an hour (subsistence 100 over 100 hours)
ELASTICITY = 2.0


def bids(hours, maximum=2.0):
    return [Bid("a", "digger", "vale", hours, maximum, 0.0)]


def inputs(hours, supply=None):
    base = YearInputs(trades=SPECS, bids=bids(hours), subsistence_per_worker_year={"vale": 100.0},
                      hours_per_worker_year=HOURS, discount_rate=0.03, career_years=30.0)
    return dataclasses.replace(base, hours_share_at={("digger", "vale"): supply} if supply else {})


def supply_through(wage, share):
    """A share of hours sold that is `share` at `wage` and rises with the wage to the elasticity."""
    return lambda wage_now: min(1.0, share * (wage_now / wage) ** ELASTICITY)


def cleared(demand_hours, supply=None, last=1.5):
    state = MarketState(workers={"vale": {"digger": [PEOPLE, 0.0, 0.0, 0.0, 0.0]}}, wages={"vale": {"digger": last}})
    return clearing.clear_all(state, inputs(demand_hours, supply))[0]


class SupplyTargetTests(unittest.TestCase):
    def test_the_target_is_the_wage_the_supply_meets_the_demand_at(self):
        supply = lambda wage: 1000.0 * min(1.0, 0.5 * wage ** 2)      # 500 hours at wage one, rising
        bid = Bid("a", "digger", "vale", 800.0, 2.0, 0.0)
        target = clearing.supply_target(1.0, supply, [bid])
        self.assertAlmostEqual(supply(target), 800.0, places=3)

    def test_where_supply_covers_demand_at_the_reservation_wage_the_target_is_the_reservation_wage(self):
        bid = Bid("a", "digger", "vale", 400.0, 2.0, 0.0)
        self.assertEqual(clearing.supply_target(1.0, lambda wage: 500.0, [bid]), 1.0)

    def test_a_demand_the_supply_never_meets_ends_at_the_highest_maximum_wage(self):
        bid = Bid("a", "digger", "vale", 5000.0, 2.0, 0.0)
        self.assertEqual(clearing.supply_target(1.0, lambda wage: 500.0, [bid]), 2.0)

    def test_the_target_never_falls_as_demand_grows(self):
        supply = lambda wage: 1000.0 * min(1.0, 0.5 * wage ** 2)
        targets = [clearing.supply_target(1.0, supply, [Bid("a", "digger", "vale", hours, 3.0, 0.0)])
                   for hours in (100.0, 300.0, 500.0, 700.0, 900.0)]
        self.assertEqual(targets, sorted(targets))


class ClearingWithSupplyTests(unittest.TestCase):
    def test_a_few_per_cent_of_excess_hours_moves_the_wage_a_few_per_cent_where_flat_supply_drops_it_to_the_ask(self):
        sold_at_the_wage = 1000.0 * 0.5
        demand = sold_at_the_wage / 1.03       # three per cent more hours offered at wage 1.5 than the employers want
        flat = cleared(demand, lambda wage_now: 0.5)       # the same hours at any wage
        schedule = cleared(demand, supply_through(1.5, 0.5))
        self.assertAlmostEqual(flat.target_wage, 1.5 + (1.0 - 1.5) * 0.03 / 1.03, places=2)   # the pull toward the reservation wage, by the imbalance
        self.assertAlmostEqual(clearing.supply_target(1.0, lambda wage_now: 500.0, bids(demand)), 1.0)   # and its target is the ask itself
        self.assertGreater(clearing.supply_target(1.0, lambda wage_now: 1000.0 * supply_through(1.5, 0.5)(wage_now), bids(demand)), 1.5 * 0.97)   # a rising supply: a few per cent
        self.assertLess(clearing.supply_target(1.0, lambda wage_now: 1000.0 * supply_through(1.5, 0.5)(wage_now), bids(demand)), 1.5)
        self.assertGreater(schedule.target_wage, 1.5 * 0.97)

    def test_the_hours_offered_are_those_sold_at_the_wage_the_market_cleared_at(self):
        supply = supply_through(1.5, 0.5)
        result = cleared(450.0, supply)
        self.assertAlmostEqual(result.hours_offered, 1000.0 * supply(result.wage))

    def test_without_a_schedule_the_clearing_is_as_it_was(self):
        self.assertEqual(cleared(400.0).hours_offered, 1000.0)


if __name__ == "__main__":
    unittest.main()
