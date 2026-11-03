"""Two labour rules over a registry: a trade that states no training years takes its family's median (the same figure
the wage schedule uses), and a founder with no work to sell sells his hours as a scholar."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.labour import trade_data
from sim.labour.labour_hands import Hands
from sim.labour.labour_training import Training


def world_with(registry):
    return SimpleNamespace(trades=SimpleNamespace(trade_registry=registry))


class FullYearsOfATrade(unittest.TestCase):
    def test_a_trade_that_states_no_years_takes_the_median_of_its_family(self):
        registry = {"smith": {"family": "craft", "training_years": 4.0},
                    "wright": {"family": "craft", "training_years": 2.0},
                    "wheelwright": {"family": "craft"}}
        training = SimpleNamespace(_world=world_with(registry))
        self.assertEqual(Training._full_years(training, "wheelwright"), 4.0)

    def test_a_trade_absent_from_the_registry_has_no_years(self):
        training = SimpleNamespace(_world=world_with({}))
        self.assertEqual(Training._full_years(training, "ghost"), 0.0)


class WageFallbackTrade(unittest.TestCase):
    def test_a_founder_with_no_scholars_sells_his_hours_as_a_scholar(self):
        hands = SimpleNamespace(effective_scholars=lambda: 0.0)
        self.assertEqual(Hands.wage_fallback_trade(hands), trade_data.scholar_trade())

    def test_a_founder_with_scholars_sells_his_hours_as_a_scholar(self):
        hands = SimpleNamespace(effective_scholars=lambda: 3.0)
        self.assertEqual(Hands.wage_fallback_trade(hands), trade_data.scholar_trade())
