"""A producer working far below its plant's capacity is short of cash only against the scale it works
at (plus the change one year allows), not against its whole plant, so it is not forced to dump stock at
any price. Its cash target, and so its dividends, are unchanged."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers, producers_close
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})
SPECS = {}                                      # no spoilage data: the good keeps


class View:
    year = 3

    def __init__(self, prices, wages, cash, rate=0.05):
        self.prices, self.wages, self.cash_held, self.rate = prices, wages, cash, rate

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return self.cash_held

    def stock(self, agent, good, tile):
        return 0.0


def view(cash):
    return View({"grain": 2.0, "seed": 1.0}, {"hand": 1.0}, cash)     # a run costs 2 + 5 = 7


def small_scale_producer(**changes):
    """Capacity 100 runs, works 4; the whole plant's working capital is 700, the scale it could reach
    next year (4 + a quarter of capacity = 29 runs) needs 203."""
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=100.0,
                last_runs=4.0, expected_sales=4.0, expected_prices={"grain": 2.0}, cash_target=700.0)
    base.update(changes)
    return producers.Producer(**base)


def offered(producer, cash, stock=50.0):
    shortfall = max(0.0, producer.cash_target - cash)
    return producers.offers(producer, FARM, view(cash), {"grain": stock}, shortfall, 0.05, SPECS)[0]


class DistressAgainstWorkingScaleTests(unittest.TestCase):
    def test_stock_is_held_for_a_better_price_when_cash_covers_the_scale_it_can_reach(self):
        self.assertGreater(offered(small_scale_producer(), cash=300.0).reservation_price, 0.0)

    def test_stock_is_still_dumped_when_cash_is_far_short_of_even_that_scale(self):
        self.assertEqual(offered(small_scale_producer(), cash=0.0).reservation_price, 0.0)

    def test_a_partly_short_producer_asks_less_than_a_flush_one(self):
        flush = offered(small_scale_producer(), cash=700.0).reservation_price
        short = offered(small_scale_producer(), cash=190.0).reservation_price
        self.assertGreater(flush, short)
        self.assertGreater(short, 0.0)

    def test_a_producer_with_no_history_is_short_against_its_whole_plant(self):
        new = small_scale_producer(last_runs=-1.0, expected_sales=0.0)
        self.assertEqual(offered(new, cash=300.0).reservation_price, 0.0)

    def test_the_cash_target_and_dividends_still_follow_the_whole_plant(self):
        closed = producers_close.close_year(small_scale_producer(), FARM, 300.0, 100.0, view(1e6)).producer
        whole_plant = producers_close.working_capital_target(FARM, closed.capacity_runs, {"seed": 1.0}, {"hand": 1.0})
        self.assertAlmostEqual(closed.cash_target, whole_plant)


if __name__ == "__main__":
    unittest.main()
