"""The engine's hours by trade (the society's working hours split between trades) have one owner: the
labour core's people when the agent economy runs, the recipe graph's need when it does not. There is no
separate workforce that moves hours between trades."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation, labour_market

FARM = labour_allocation.FARM_TRADE


def _non_farm_share(game, trade):
    hours = game.state.economy.society_labour_hours
    rest = sum(value for name, value in hours.items() if name != FARM)
    return hours.get(trade, 0.0) / rest


def _core_state(game):
    game.economy.open_agent()
    return game.economy.agent.economy().record.workforce


class HoursFollowTheCoreTests(unittest.TestCase):

    def test_with_the_agent_economy_on_a_trade_with_more_people_has_more_hours(self):
        game = sim(civ="rome_100ad", events=False)
        game._demographic_recovery(101)
        before = _non_farm_share(game, "smith")
        for by_trade in _core_state(game).workers.values():
            if "smith" in by_trade:
                by_trade["smith"] = [count * 50.0 for count in by_trade["smith"]]
        game._demographic_recovery(102)
        self.assertGreater(_non_farm_share(game, "smith"), 5.0 * before)

    def test_hours_add_up_to_the_hours_the_society_has(self):
        game = sim(civ="rome_100ad", events=False)
        game._demographic_recovery(101)
        total = sum(game.state.economy.society_labour_hours.values())
        # people change a little after the year's allocation, so the two totals agree to a percent
        self.assertAlmostEqual(total, game.labour._society_hours_available(), delta=0.01 * total)

    def test_with_the_agent_economy_off_hours_follow_the_need_the_recipes_put_on_each_trade(self):
        game = sim(civ="rome_100ad", events=False, agent_economy=False)
        game._demographic_recovery(101)
        shares = game.labour._non_farm_need_shares()
        for trade, share in shares.items():
            self.assertAlmostEqual(_non_farm_share(game, trade), share, places=9)

    def test_no_second_workforce_moves_hours_between_trades(self):
        self.assertFalse(hasattr(labour_market, "Workforce"))
        self.assertFalse(hasattr(labour_allocation, "reallocate"))


if __name__ == "__main__":
    unittest.main()
