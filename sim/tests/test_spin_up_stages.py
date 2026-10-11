"""The spin-up's second stage, after the workforce is trimmed, runs a bounded number of years on the economy
the first stage left; it settles wages and entry and does not wait for a tolerance that thin labour markets
never meet."""
QUICK_TOPIC = True

import os
import unittest
from unittest import mock

from sim.engine import economy_port_key, economy_port_year

FULL_GAME = {key: value for key, value in os.environ.items() if key != economy_port_year.SPIN_UP_YEARS_ENV}


class _CountingEconomy:
    def __init__(self):
        self.years = 0

    def step(self, inputs):
        self.years += 1


class TrimmedStageTests(unittest.TestCase):
    def test_the_stage_runs_its_declared_number_of_years_on_the_economy_it_is_given(self):
        economy = _CountingEconomy()
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            economy_port_year.AgentEconomy._settle_trimmed(economy, object())
        self.assertEqual(economy.years, int(economy_port_year.SPIN_UP_TRIMMED_YEARS))

    def test_the_stage_is_shorter_than_the_first_stage_can_be(self):
        self.assertLess(economy_port_year.SPIN_UP_TRIMMED_YEARS, economy_port_year.SPIN_UP_MAXIMUM_YEARS)



class ShortenedSpinUpTests(unittest.TestCase):
    """The test suite shortens the spin-up through an environment variable; a full game never does."""

    def test_a_game_without_the_variable_runs_the_declared_bounds(self):
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            self.assertEqual(economy_port_year.spin_up_years(),
                             (int(economy_port_year.SPIN_UP_MAXIMUM_YEARS), int(economy_port_year.SPIN_UP_TRIMMED_YEARS)))

    def test_the_variable_names_both_stages(self):
        with mock.patch.dict(os.environ, {economy_port_year.SPIN_UP_YEARS_ENV: "4,1"}):
            self.assertEqual(economy_port_year.spin_up_years(), (4, 1))

    def test_a_shortened_spin_up_is_cached_apart_from_a_full_one(self):
        setup = {"civ_id": "rome_100ad"}
        with mock.patch.object(economy_port_key, "setup_digest", lambda value: "digest"):
            with mock.patch.dict(os.environ, FULL_GAME, clear=True):
                full = economy_port_year._spin_up_cache_key(setup)
            with mock.patch.dict(os.environ, {economy_port_year.SPIN_UP_YEARS_ENV: "4,1"}):
                short = economy_port_year._spin_up_cache_key(setup)
            plain = economy_port_key.spin_up_key(setup)
        self.assertEqual(full, plain)
        self.assertNotEqual(full, short)


if __name__ == "__main__":
    unittest.main()
