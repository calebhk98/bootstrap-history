"""The labour core's demand for hours is continuous in the wage (each tranche's hours spread over the wage interval below
its maximum), so a small excess of demand over supply moves the wage a small way, in the plain rule and in the kernel."""

QUICK_TOPIC = True

import unittest

from sim.economy import labour_bids, labour_state
from sim.labour.market import clearing, trades
from sim.labour.market.import_cost import ImportCosts
from sim.labour.market.market_state import MarketState
from sim.labour.market.records import EmployerHoursBid, YearInputs

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0}})
RESERVATION = 1.0
SUPPLY_AT_RESERVATION = 1000.0


def nearly_vertical_supply(wage):
    """Hours sold rise by two per cent of the reservation's hours for each unit of wage."""
    return SUPPLY_AT_RESERVATION * (1.0 + 0.02 * (wage - RESERVATION))


def tranches(total_hours):
    return labour_bids.sloped_bids([EmployerHoursBid("farm", "digger", "vale", total_hours, 2.0)])


class ContinuousSupplyTargetTests(unittest.TestCase):
    def test_wanting_one_per_cent_more_than_supply_gives_a_wage_near_the_reservation_not_the_lowest_cap(self):
        target = clearing.supply_target(RESERVATION, nearly_vertical_supply, tranches(1.01 * SUPPLY_AT_RESERVATION))
        self.assertGreater(target, RESERVATION)
        self.assertLess(target, RESERVATION * 1.05)

    def test_wanting_one_per_cent_less_than_supply_gives_the_reservation(self):
        self.assertEqual(clearing.supply_target(RESERVATION, nearly_vertical_supply, tranches(0.99 * SUPPLY_AT_RESERVATION)),
                         RESERVATION)

    def test_the_wage_across_balance_differs_by_a_small_amount(self):
        below = clearing.supply_target(RESERVATION, nearly_vertical_supply, tranches(0.984 * SUPPLY_AT_RESERVATION))
        above = clearing.supply_target(RESERVATION, nearly_vertical_supply, tranches(1.009 * SUPPLY_AT_RESERVATION))
        self.assertLess(above - below, 0.05 * RESERVATION)


class OpeningWageSeedTests(unittest.TestCase):
    def test_each_market_of_the_workforce_gets_its_trades_opening_wage_and_a_trade_without_one_gets_none(self):
        workforce = MarketState(workers={"vale": {"digger": [10.0], "smith": [5.0]}})
        count_without = labour_state.seed_opening_wages(workforce, {"digger": 1.5})
        self.assertEqual(workforce.wages["vale"]["digger"], 1.5)
        self.assertNotIn("smith", workforce.wages.get("vale", {}))
        self.assertEqual(count_without, 1)


class SeededFirstYearTests(unittest.TestCase):
    def test_a_market_with_a_last_wage_moves_the_declared_share_of_the_way_to_the_wage_a_market_with_none_jumps_to(self):
        workers = {"vale": {"digger": [10.0, 0.0, 0.0, 0.0, 0.0]}}

        def cleared(wages):
            inputs = YearInputs(trades=SPECS, bids=tranches(5000.0), subsistence_per_worker_year={"vale": 100.0},
                                hours_per_worker_year=100.0, discount_rate=0.03, career_years=30.0,
                                hours_sold_at={("digger", "vale"): lambda wage: 500.0})
            state = MarketState(workers=workers, wages=wages)
            return clearing._plain_head(state, inputs, "digger", "vale", inputs.bids, ImportCosts(state, inputs))[0]

        jumped = cleared(None)
        seeded = cleared({"vale": {"digger": 1.0}})
        self.assertAlmostEqual(seeded, 1.0 + clearing.WAGE_SHARE_CLOSED_PER_YEAR * (jumped - 1.0), places=9)
