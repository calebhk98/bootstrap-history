"""Weather through running games (the rules are test_regional_weather_wiring): weather is a pure function of
(civ, region, year, salt), so two games match year for year and a save and reload mid-run loses no draw."""
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403

from sim.tests.weather_test_helpers import assert_matching_century, assert_save_reload_trajectory

# Long enough for weather to shape population and stock, short enough to stay cheap; the engine's own yearly market
# keeps each year fast and weather does not depend on the market.
DETERMINISM_YEARS = 20


def _market_free_rome():
    """A game whose steps leave out the year's market close: weather, farming and people do not read it."""
    game = sim(civ="rome_100ad", events=False)
    game._step_market = lambda: None
    return game


class DeterminismAcrossSaveAndReloadTests(unittest.TestCase):

    def test_two_games_stay_identical_year_for_year(self):
        assert_matching_century(self, _market_free_rome, years=DETERMINISM_YEARS)

    def test_a_mid_run_save_and_reload_follows_the_same_trajectory(self):
        with tempfile.TemporaryDirectory() as folder:
            assert_save_reload_trajectory(
                self, _market_free_rome, os.path.join(folder, "weather_trajectory.json"),
                years=DETERMINISM_YEARS)


if __name__ == "__main__":
    unittest.main()
