"""In a whole game the labour core holds carters and plumbers, sized from the need the recipe graph puts on
them (Complaint 434). Builds a game, so it is a slow topic; the pure checks are in test_need_shares_trade_demand."""
import unittest

from .harness import *  # noqa: F401,F403


class CartersAndPlumbersInAGameTests(unittest.TestCase):

    def test_rome_has_carters_and_plumbers_the_household_can_reach(self):
        report = sim(civ="rome_100ad", events=False).labour.population_report()
        by_trade = {row["trade"]: row for row in report["trades"]}
        for trade in ("carter", "plumber"):
            self.assertTrue(by_trade[trade]["exists_here"], trade)
            self.assertGreater(by_trade[trade]["estimated_in_the_country"], 0.0, trade)
            self.assertGreater(by_trade[trade]["within_your_reach"], 0.0, trade)


if __name__ == "__main__":
    unittest.main()
