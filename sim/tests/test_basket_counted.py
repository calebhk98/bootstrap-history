"""The quantity of each basket good the price level counts: its whole opening quantity under the search rules, what
its markets still usually trade under the clearing rules."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import basket_counted, rule_sets
from sim.economy.labour_record import LabourRecord
from sim.economy.market_memory import MarketMemory, market_key
from sim.economy.year_close import remember_basket_price_level


class QuantityCounted(unittest.TestCase):
    def test_whole_ignores_what_trades(self):
        self.assertEqual(basket_counted.whole(100.0, 3.0), 100.0)
        self.assertEqual(basket_counted.whole(100.0, 0.0), 100.0)

    def test_still_bought_is_the_usual_volume_up_to_the_opening_quantity(self):
        self.assertEqual(basket_counted.still_bought(100.0, 3.0), 3.0)
        self.assertEqual(basket_counted.still_bought(100.0, 250.0), 100.0)
        self.assertEqual(basket_counted.still_bought(100.0, -1.0), 0.0)


class UsualVolumeByGood(unittest.TestCase):
    def test_a_goods_markets_are_summed(self):
        volumes = {market_key("tin", "a"): 2.0, market_key("tin", "b"): 3.0, market_key("salt", "a"): 7.0}
        self.assertEqual(basket_counted.usual_volume_by_good(volumes), {"tin": 5.0, "salt": 7.0})


class Counted(unittest.TestCase):
    def test_each_good_by_the_rule_and_a_good_left_nothing_is_dropped(self):
        basket = {"tin": 100.0, "salt": 50.0, "games": 80.0}
        usual = {"tin": 400.0, "salt": 5.0}
        self.assertEqual(basket_counted.counted(basket, usual, basket_counted.still_bought), {"tin": 100.0, "salt": 5.0})
        self.assertEqual(basket_counted.counted(basket, usual, basket_counted.whole), basket)


def setup_on(rule_set, base):
    return types.SimpleNamespace(recipes={}, opening_prices=base, currency_id="coin", unskilled_trade="labour", opening_wages={"labour": 0.5},
                                 trades={"labour": types.SimpleNamespace(training_years=0.0)}, rule_set=rule_set)


def record_of(memory, basket, base):
    return types.SimpleNamespace(memory=memory, labour=LabourRecord(), goods=types.SimpleNamespace(volumes={}, opening_basket=basket, index_base_prices=base))


class PriceLevel(unittest.TestCase):
    """A basket of tin and games, bought a hundred each at one coin; games now trade a single hour at ten coins."""

    def level(self, rule_set):
        memory = MarketMemory(prices={market_key("tin", "a"): 1.0, market_key("games", "a"): 10.0})
        memory.note_trading({market_key("tin", "a"), market_key("games", "a")})
        memory.note_volume(market_key("tin", "a"), 100.0)
        memory.note_volume(market_key("games", "a"), 1.0)
        base = {"tin": 1.0, "games": 1.0}
        return remember_basket_price_level(setup_on(rule_set, base), record_of(memory, {"tin": 100.0, "games": 100.0}, base))

    def test_under_the_search_rules_the_sliver_counts_at_the_whole_opening_quantity(self):
        self.assertAlmostEqual(self.level("search"), (100.0 + 1000.0) / 200.0)

    def test_under_the_clearing_rules_it_counts_by_the_hour_that_trades(self):
        self.assertAlmostEqual(self.level("clearing"), (100.0 + 10.0) / 101.0)


class Rules(unittest.TestCase):
    def test_the_two_entries(self):
        self.assertIs(rule_sets.RULE_SETS["search"].basket_quantity_counted, basket_counted.whole)
        self.assertIs(rule_sets.RULE_SETS["clearing"].basket_quantity_counted, basket_counted.still_bought)


if __name__ == "__main__":
    unittest.main()
