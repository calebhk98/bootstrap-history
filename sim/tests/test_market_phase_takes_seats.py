"""The year's market phase is called the way every world phase is, with the seats still in play: a hook that took no seats
made every year fail with a TypeError."""

QUICK_TOPIC = True

import types
import unittest

from sim.markets.clearing import MarketClearing


class MarketPhaseTakesTheSeats(unittest.TestCase):
    def test_the_market_phase_runs_the_year_given_the_seats(self):
        sent = []
        clearing = MarketClearing.__new__(MarketClearing)
        year = types.SimpleNamespace(run_year=lambda: types.SimpleNamespace(accounts=None))
        economy = types.SimpleNamespace(open_agent=lambda: None, parts=types.SimpleNamespace(year=year))
        clearing.parts = types.SimpleNamespace(market_objects=types.SimpleNamespace(economy=economy))
        clearing.needs = types.SimpleNamespace(send=sent.append)
        clearing.step_market(["first", "second"])
        self.assertEqual([type(command).__name__ for command in sent],
                         ["FinishWays", "RecordFoodEaten", "ResetActorTradeTallies", "CloseRealOutput"])


if __name__ == "__main__":
    unittest.main()
