"""A seller that cannot sell lowers its ask year after year until it sells, and a seller that sells out
raises it until it no longer does. Hours of labour are sold like goods: the subsistence floor is where a
worker's ask starts, not a bound under it (Complaint 398)."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers
from sim.labour.market import asks, clearing, trades
from sim.labour.market.records import Bid, MarketState, YearInputs
from sim.tests.test_economy_producer_stale_ask import FARM, View, seller

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0}})
HOURS = 100.0
SUBSISTENCE = 100.0     # a reservation wage of one an hour


def inputs(bids, ask_floor=0.0):
    return YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={"vale": SUBSISTENCE},
                      hours_per_worker_year=HOURS, discount_rate=0.03, career_years=30.0,
                      ask_floor_per_worker_year={"vale": ask_floor})


def market(people):
    return MarketState(workers={"vale": {"digger": [people, 0.0, 0.0, 0.0, 0.0]}})


def years_of(state, bids, years):
    return [clearing.clear_all(state, inputs(bids))[0] for _ in range(years)]


class WorkersAskFollowSales(unittest.TestCase):
    def test_hours_nobody_buys_at_the_ask_are_offered_cheaper_each_year_until_hired(self):
        # employers value an hour at 0.4; the family's floor is 1.0 an hour, ten workers offer 1000 hours
        results = years_of(market(10.0), [Bid("farm", "digger", "vale", 500.0, 0.4)], 30)
        self.assertEqual(results[0].hours_hired, 0.0)
        self.assertGreater(results[-1].hours_hired, 0.0)
        self.assertLessEqual(results[-1].wage, 0.4 + 1e-9)

    def test_the_ask_keeps_falling_while_hours_stay_unsold(self):
        state = market(10.0)
        scales = []
        for _ in range(5):
            clearing.clear_all(state, inputs([]))
            scales.append(asks.scale_of(state, "vale", "digger"))
        self.assertTrue(all(later < earlier for earlier, later in zip(scales, scales[1:])), scales)

    def test_a_trade_that_sells_out_raises_its_ask(self):
        state = market(2.0)
        scales = []
        for _ in range(5):
            clearing.clear_all(state, inputs([Bid("farm", "digger", "vale", 1000.0, 1.1)]))
            scales.append(asks.scale_of(state, "vale", "digger"))
        # demand outruns supply and buyers pay little over the ask: the ask rises to what they pay, no further
        self.assertTrue(all(later >= earlier for earlier, later in zip(scales, scales[1:])), scales)
        self.assertGreater(scales[0], 1.0)
        self.assertLessEqual(scales[-1], 1.1 + 1e-9)

    def test_a_wage_well_above_the_ask_does_not_drag_the_ask_up_after_it(self):
        state = market(2.0)
        for _ in range(8):
            clearing.clear_all(state, inputs([Bid("farm", "digger", "vale", 1000.0, 50.0)]))
        self.assertEqual(asks.scale_of(state, "vale", "digger"), 1.0)

    def test_a_thin_trade_whose_employers_can_pay_less_is_hired_again_at_once(self):
        state = market(3.0)
        for _ in range(12):
            clearing.clear_all(state, inputs([Bid("farm", "digger", "vale", 500.0, 50.0)]))
        after = clearing.clear_all(state, inputs([Bid("farm", "digger", "vale", 500.0, 10.0)]))[0]
        self.assertLessEqual(after.wage, 10.0)
        self.assertGreater(after.hours_hired, 0.0)

    def test_a_thin_trade_with_swinging_demand_is_hired_every_year(self):
        state = market(3.0)
        hired = []
        for year in range(30):
            cap = 50.0 if year % 2 else 12.0
            hired.append(clearing.clear_all(state, inputs([Bid("farm", "digger", "vale", 500.0, cap)]))[0].hours_hired)
        self.assertTrue(all(hours > 0.0 for hours in hired[2:]), hired)

    def test_a_glutted_common_trade_settles_at_the_plot_floor_without_undershooting(self):
        # ten workers, employers want a fifth of their hours at any wage up to 5; the plot is worth 30 of 100
        state = market(10.0)
        wages = []
        for _ in range(60):
            result = clearing.clear_all(state, inputs([Bid("farm", "digger", "vale", 200.0, 5.0)], ask_floor=30.0))[0]
            wages.append(result.wage)
        self.assertTrue(all(later <= earlier + 1e-9 for earlier, later in zip(wages, wages[1:])), wages)
        self.assertGreaterEqual(min(wages), 0.3 - 1e-9)
        self.assertAlmostEqual(wages[-1], 0.3, places=2)

    def test_an_ask_stops_at_what_the_family_has_without_selling(self):
        # the family's own plot is worth half the subsistence floor to a worker
        state = market(10.0)
        for _ in range(40):
            clearing.clear_all(state, YearInputs(
                trades=SPECS, bids=[], subsistence_per_worker_year={"vale": SUBSISTENCE}, hours_per_worker_year=HOURS,
                discount_rate=0.03, career_years=30.0, ask_floor_per_worker_year={"vale": 50.0}))
        self.assertAlmostEqual(asks.scale_of(state, "vale", "digger"), 0.5, places=6)

    def test_a_market_nobody_has_cleared_asks_the_floor(self):
        self.assertEqual(asks.scale_of(MarketState(), "vale", "digger"), 1.0)


class SellersOfGoodsAskFollowSales(unittest.TestCase):
    def test_a_seller_that_sold_out_expects_more_than_the_price_it_saw(self):
        view = View({"grain": 0.7, "seed": 1.0}, {"hand": 1.0}, stock=0.0)
        expected = producers.next_expectations(seller(), FARM, view)["grain"]
        self.assertGreater(expected, 0.7)

    def test_a_seller_that_keeps_selling_out_raises_its_ask_year_after_year(self):
        producer = seller()
        view = View({"grain": 0.7, "seed": 1.0}, {"hand": 1.0}, stock=0.0)
        path = []
        for _ in range(4):
            producer = producers.replace(producer, expected_prices=producers.next_expectations(producer, FARM, view))
            path.append(producer.expected_prices["grain"])
        self.assertTrue(all(later > earlier for earlier, later in zip(path, path[1:])), path)

    def test_a_producer_that_did_not_run_has_not_sold_out(self):
        view = View({"grain": 0.7, "seed": 1.0}, {"hand": 1.0}, stock=0.0)
        expected = producers.next_expectations(seller(last_runs=0.0), FARM, view)["grain"]
        self.assertLessEqual(expected, 0.7 + 1e-9)


if __name__ == "__main__":
    unittest.main()
