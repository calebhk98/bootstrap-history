"""A trade with few hands cannot quote above what training a substitute costs: the unskilled wage times the
trade's training premium (Complaint 434). Plain records, no game."""

QUICK_TOPIC = True

import unittest

from sim.labour import wages
from sim.labour.market import clearing, trades
from sim.labour.market.records import Bid, MarketState, YearInputs

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0},
                            "healer": {"family": "care", "training_years": 5},
                            "sage": {"family": "care", "training_years": 12}})
HOURS = 100.0
DISCOUNT = 0.03
CAREER = 30.0


def inputs(bids):
    return YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={"vale": 100.0},
                      hours_per_worker_year=HOURS, discount_rate=DISCOUNT, career_years=CAREER)


def state(healers, digger_wage=1.0):
    held = MarketState(workers={"vale": {"digger": [50.0, 0.0, 0.0, 0.0, 0.0],
                                         "healer": [healers, 0.0, 0.0, 0.0, 0.0]}})
    held.wages = {"vale": {"digger": digger_wage, "healer": 1.0}}
    return held


def hungry_bid(trade="healer", maximum=500.0):
    return Bid("clinic", trade, "vale", 5000.0, maximum)


def settle(held, bids, years=40):
    last = None
    for _year in range(years):
        last = [each for each in clearing.clear_all(held, inputs(bids)) if each.trade == bids[0].trade][0]
    return last


class SubstituteWageTests(unittest.TestCase):

    def test_a_trade_with_one_pair_of_hands_quotes_at_most_the_trained_substitute(self):
        ceiling = 1.0 * wages.training_premium(5.0, DISCOUNT, CAREER)
        result = settle(state(healers=1.0), [hungry_bid()])
        self.assertLessEqual(result.wage, ceiling + 1e-9)
        self.assertGreater(result.wage, 1.0)

    def test_a_longer_training_commands_a_dearer_substitute(self):
        healer = settle(state(healers=1.0), [hungry_bid("healer")]).wage
        held = state(healers=1.0)
        held.workers["vale"]["sage"] = [1.0, 0.0, 0.0, 0.0, 0.0]
        held.wages["vale"]["sage"] = 1.0
        sage = settle(held, [hungry_bid("sage")]).wage
        self.assertGreater(sage, healer)

    def test_the_ceiling_follows_the_unskilled_wage(self):
        def holding(wage):    # farms keep bidding, so the unskilled wage stays where it is
            return [hungry_bid(), Bid("farm", "digger", "vale", 99999.0, wage)]
        low = settle(state(healers=1.0, digger_wage=1.0), holding(1.0)).wage
        high = settle(state(healers=1.0, digger_wage=3.0), holding(3.0)).wage
        self.assertAlmostEqual(high / low, 3.0, places=6)

    def test_the_unskilled_trade_itself_is_not_capped(self):
        result = settle(state(healers=1.0), [Bid("farm", "digger", "vale", 99999.0, 50.0)])
        self.assertGreater(result.wage, 10.0)

    def test_a_trade_with_a_lower_maximum_bid_still_quotes_below_the_ceiling(self):
        result = settle(state(healers=1.0), [hungry_bid(maximum=1.2)])
        self.assertLessEqual(result.wage, 1.2 + 1e-9)

    def test_a_skilled_trade_in_surplus_never_quotes_below_the_unskilled_wage(self):
        held = state(healers=500.0, digger_wage=3.0)
        bids = [Bid("clinic", "healer", "vale", 10.0, 500.0), Bid("farm", "digger", "vale", 99999.0, 3.0)]
        result = settle(held, bids)
        self.assertGreaterEqual(result.wage, held.wages["vale"]["digger"] - 1e-9)


if __name__ == "__main__":
    unittest.main()
