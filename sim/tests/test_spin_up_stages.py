"""SCENARIO (Complaint 640): The spin-up's second stage, after the workforce is trimmed, runs a bounded number of years on the economy
the first stage left; it settles wages and entry and does not wait for a tolerance that thin labour markets
never meet."""
QUICK_TOPIC = True

import os
import types
import unittest
from unittest import mock

from sim.engine import economy_port_key, economy_port_year
from sim.engine.economy_port_year import spin_up_years as years_from_environment   # reads the environment; runs no years

FULL_GAME = {key: value for key, value in os.environ.items() if key != economy_port_year.SPIN_UP_YEARS_ENV}


class _CountingEconomy:
    def __init__(self):
        self.years = 0

    def step(self, inputs):
        self.years += 1
        return types.SimpleNamespace(basket_price_level=1.0, prices={})


class TrimmedStageTests(unittest.TestCase):
    def test_the_stage_runs_its_declared_number_of_years_on_the_economy_it_is_given(self):
        economy = _CountingEconomy()
        with mock.patch.dict(os.environ, FULL_GAME, clear=True), \
                mock.patch.object(economy_port_year.economy_api, "spin_up_state", lambda economy, outcome: {}), \
                mock.patch.object(economy_port_year.economy_api, "interest_rate", lambda economy: 0.05):
            states = economy_port_year.AgentEconomy._settle_trimmed(economy, object(), [])
        self.assertEqual(economy.years, int(economy_port_year.SPIN_UP_TRIMMED_YEARS))
        # the stage hands back the last years' states for the measurement, not every year's
        self.assertEqual(len(states), int(economy_port_year.SPIN_UP_MEASURED_YEARS))

    def test_the_stage_is_shorter_than_the_first_stage_can_be(self):
        self.assertLess(economy_port_year.SPIN_UP_TRIMMED_YEARS, economy_port_year.SPIN_UP_MAXIMUM_YEARS)



def _economy_whose_price_level_follows(levels):
    """An economy whose yearly price level is the next of `levels` (the last one repeats); nothing else moves."""
    economy = types.SimpleNamespace(setup=types.SimpleNamespace(currency_id="coin"),
                                    record=types.SimpleNamespace(memory=types.SimpleNamespace(rates={"coin": 0.05})),
                                    years=0)

    def step(inputs):
        level = levels[min(economy.years, len(levels) - 1)]
        economy.years += 1
        return types.SimpleNamespace(basket_price_level=level, prices={"wheat_kg": 1.0})
    economy.step = step
    return economy


class SettledReportTests(unittest.TestCase):
    """The first stage says whether it met its tolerance, so a game or `openings` can tell a settled opening from
    one that opened wherever the cycle stood."""

    def test_a_stage_that_meets_the_tolerance_reports_settled_with_the_years_it_took(self):
        economy = _economy_whose_price_level_follows([1.0, 1.5, 1.2, 1.2])
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            result = economy_port_year.AgentEconomy._settle(economy, object(), ["wheat_kg"])
        self.assertTrue(result["settled"])
        self.assertEqual(result["years"], 4)
        self.assertLess(result["gap"], economy_port_year.SPIN_UP_TOLERANCE)

    def test_a_stage_that_runs_out_of_years_first_reports_not_settled_and_how_far_it_was(self):
        economy = _economy_whose_price_level_follows([1.0 * 1.5 ** year for year in range(100)])
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            result = economy_port_year.AgentEconomy._settle(economy, object(), ["wheat_kg"])
        self.assertFalse(result["settled"])
        self.assertEqual(result["years"], int(economy_port_year.SPIN_UP_MAXIMUM_YEARS))
        self.assertAlmostEqual(result["gap"], 0.5)

    def test_the_result_is_kept_in_the_record_and_survives_a_save(self):
        from sim.economy import api
        from sim.economy.record import EconomyRecord
        economy = types.SimpleNamespace(record=types.SimpleNamespace(spin_up_result={}))
        api.note_spin_up_result(economy, {"settled": False, "years": 30, "gap": 0.3})
        self.assertEqual(economy.record.spin_up_result, {"settled": False, "years": 30, "gap": 0.3})
        self.assertIn("spin_up_result", EconomyRecord.__dataclass_fields__)


class OpeningsReportTests(unittest.TestCase):
    def test_openings_says_plainly_when_the_opening_did_not_settle(self):
        from sim.ui.cli_openings import spin_up_line as describe_result   # formats a result; builds nothing
        unsettled = describe_result({"settled": False, "years": 30, "gap": 0.3})
        settled = describe_result({"settled": True, "years": 12, "gap": 0.01})
        self.assertIn("NOT SETTLED", unsettled)
        self.assertNotIn("NOT SETTLED", settled)
        self.assertIn("no result", describe_result({}))


class ShortenedSpinUpTests(unittest.TestCase):
    """The test suite shortens the spin-up through an environment variable; a full game never does."""

    def test_a_game_without_the_variable_runs_the_declared_bounds(self):
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            self.assertEqual(years_from_environment(),
                             (int(economy_port_year.SPIN_UP_MAXIMUM_YEARS), int(economy_port_year.SPIN_UP_TRIMMED_YEARS)))

    def test_the_variable_names_both_stages(self):
        with mock.patch.dict(os.environ, {economy_port_year.SPIN_UP_YEARS_ENV: "4,1"}):
            self.assertEqual(years_from_environment(), (4, 1))

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
