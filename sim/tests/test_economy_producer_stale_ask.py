"""A seller left holding goods nobody bought at its ask lowers the ask and what it expects to get, and does
not stop planning runs for good because the sales it recorded were at an ask above every bid."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import producers
from sim.economy.types import GoodSpec, Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages, stock=0.0, rate=0.05):
        self.prices, self.wages, self.held, self.rate = prices, wages, stock, rate

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
        return 1000.0

    def stock(self, agent, good, tile):
        return self.held if good == "grain" else 0.0


def seller(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0,
                last_runs=1.0, expected_sales=1.0, expected_prices={"grain": 0.7})
    base.update(changes)
    return producers.Producer(**base)


def frozen_market(stock):
    """The market remembers the price the seller already expects: nothing cleared, nothing moved it."""
    return View({"grain": 0.7, "seed": 1.0}, {"hand": 1.0}, stock)


class UnsoldAskTests(unittest.TestCase):
    def test_unsold_stock_lowers_the_expected_price(self):
        expected = producers.next_expectations(seller(), FARM, frozen_market(stock=500.0))["grain"]
        self.assertLess(expected, 0.63)

    def test_no_stock_left_keeps_the_expectation(self):
        expected = producers.next_expectations(seller(), FARM, frozen_market(stock=0.0))["grain"]
        self.assertGreater(expected, 0.65)

    def test_the_reservation_follows_the_expectation_down_year_after_year(self):
        producer = seller()
        view = frozen_market(stock=500.0)
        reservations = []
        for _year in range(8):
            producer = producers.replace(producer, expected_prices=producers.next_expectations(producer, FARM, view))
            offer, = producers.offers(producer, FARM, view, {"grain": 500.0}, 0.0, 0.05, {"grain": GoodSpec("grain", 1.0, 0.0, 0.0, "food")})
            reservations.append(offer.reservation_price)
        self.assertTrue(all(later < earlier for earlier, later in zip(reservations, reservations[1:])))
        # the markdown compounds; the regressive pull toward cost slows it
        self.assertLess(reservations[-1], (1.0 - producers.UNSOLD_ASK_MARKDOWN_SHARE) ** 4 * reservations[0])

    def test_sales_recorded_at_too_high_an_ask_do_not_stop_runs_for_good(self):
        producer = seller(expected_sales=1e-6)
        held_in_runs = 0.1
        runs = producers.runs_for_stock(producer, FARM, View({}, {}, stock=held_in_runs * FARM.outputs["grain"]))
        self.assertGreater(runs, 0.0)
        self.assertTrue(math.isfinite(runs))

    def test_a_large_unsold_stock_still_holds_runs_back(self):
        producer = seller(expected_sales=1e-6)
        runs = producers.runs_for_stock(producer, FARM, View({}, {}, stock=50.0 * FARM.outputs["grain"]))
        self.assertEqual(runs, 0.0)


if __name__ == "__main__":
    unittest.main()
