"""A producer whose runs do not pay needs no working capital, so it is not pressed to dump stock at zero."""
import unittest

from sim.economy import producers
from sim.economy.types import Recipe

SMELT = Recipe("smelt", {"metal": 10.0}, {"ore": 4.0}, {"smith": 1.0})


class View:
    year = 3

    def __init__(self, prices, wages=None):
        self.prices, self.wages = prices, wages if wages is not None else {"smith": 1.0}

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def stock(self, agent, good, tile):
        return 0.0


def smelter(**changes):
    base = dict(agent_id="s1", owner="lord", recipe_id="smelt", tile="t", capacity_runs=10.0, last_runs=10.0,
                expected_sales=10.0, cash_target=200.0, expected_prices={"metal": 1.0, "ore": 1.0})
    base.update(changes)
    return producers.Producer(**base)


def reservation(view, shortfall=150.0, **changes):
    rows = producers.offers(smelter(**changes), SMELT, view, {"metal": 5.0}, shortfall, 0.05, {})
    return rows[0].reservation_price


class IdleProducerTests(unittest.TestCase):
    def test_a_run_that_does_not_pay_leaves_the_stock_at_its_holding_reservation(self):
        # revenue per run 10 at the expected price; the ore alone costs 400 a run at the market
        dear_ore = View({"metal": 1.0, "ore": 100.0}, {"smith": 1.0})
        held = reservation(dear_ore, expected_prices={"metal": 1.0, "ore": 100.0})
        self.assertAlmostEqual(held, 1.0 / 1.05)

    def test_a_run_that_pays_still_presses_a_cash_short_producer(self):
        cheap_ore = View({"metal": 1.0, "ore": 0.01}, {"smith": 0.1})
        pressed = reservation(cheap_ore, shortfall=150.0, expected_prices={"metal": 1.0, "ore": 0.01})
        self.assertLess(pressed, 1.0 / 1.05)

    def test_a_run_that_cannot_be_priced_does_not_press_the_producer(self):
        no_wage = View({"metal": 1.0, "ore": 0.01}, {})
        self.assertAlmostEqual(reservation(no_wage, expected_prices={"metal": 1.0, "ore": 0.01}), 1.0 / 1.05)


if __name__ == "__main__":
    unittest.main()
