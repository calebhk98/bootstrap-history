"""The spin-up's first stage: under the search rules it ends on its first quiet year, under the clearing rules it runs
to its bound, so the path a game runs is the one the stages trace replays."""

QUICK_TOPIC = True

import os
import types
import unittest
from unittest import mock

from sim.economy import rule_sets, spin_up_stop
from sim.markets import spin_up, spin_up_run

FULL_GAME = {key: value for key, value in os.environ.items() if key != spin_up.SPIN_UP_YEARS_ENV}


def economy_on(rule_set, levels):
    """An economy on `rule_set` whose yearly price level is the next of `levels` (the last one repeats)."""
    economy = types.SimpleNamespace(setup=types.SimpleNamespace(currency_id="coin", rule_set=rule_set),
                                    record=types.SimpleNamespace(memory=types.SimpleNamespace(rates={"coin": 0.05})), years=0)

    def step(inputs):
        level = levels[min(economy.years, len(levels) - 1)]
        economy.years += 1
        return types.SimpleNamespace(basket_price_level=level, prices={"wheat_kg": 1.0})
    economy.step = step
    return economy


def first_stage(economy):
    with mock.patch.dict(os.environ, FULL_GAME, clear=True), \
            mock.patch.object(spin_up_run.economy_api, "traded_volumes", lambda economy: {"wheat_kg": 1.0}):
        return spin_up_run.settle(economy, object(), ["wheat_kg"])


class FirstStage(unittest.TestCase):
    def test_the_search_rules_stop_on_the_first_quiet_year(self):
        result = first_stage(economy_on("search", [1.0, 1.5, 1.2, 1.2]))
        self.assertEqual(result["years"], 4)
        self.assertTrue(result["settled"])

    def test_the_clearing_rules_run_the_stage_to_their_own_longer_bound(self):
        result = first_stage(economy_on("clearing", [1.0, 1.5, 1.2, 1.2]))
        self.assertEqual(result["years"], int(spin_up_stop.FIRST_STAGE_YEARS_TO_REST))
        self.assertGreater(result["years"], int(spin_up_run.SPIN_UP_MAXIMUM_YEARS))
        self.assertTrue(result["settled"])

    def test_a_full_stage_that_ends_moving_reports_not_settled(self):
        result = first_stage(economy_on("clearing", [1.0 * 1.5 ** year for year in range(100)]))
        self.assertEqual(result["years"], int(spin_up_stop.FIRST_STAGE_YEARS_TO_REST))
        self.assertFalse(result["settled"])

    def test_years_named_in_the_environment_are_run_as_named_whatever_the_rule_set(self):
        economy = economy_on("clearing", [1.0 * 1.5 ** year for year in range(100)])
        with mock.patch.dict(os.environ, {**FULL_GAME, spin_up.SPIN_UP_YEARS_ENV: "3,1"}, clear=True), \
                mock.patch.object(spin_up_run.economy_api, "traded_volumes", lambda economy: {"wheat_kg": 1.0}):
            self.assertEqual(spin_up_run.settle(economy, object(), ["wheat_kg"])["years"], 3)


class StageYears(unittest.TestCase):
    def test_the_declared_bounds_with_the_rule_sets_first_stage(self):
        with mock.patch.dict(os.environ, FULL_GAME, clear=True):
            declared = (int(spin_up.SPIN_UP_MAXIMUM_YEARS), int(spin_up.SPIN_UP_TRIMMED_YEARS))
            self.assertEqual(spin_up.stage_years(lambda years: years), declared)
            self.assertEqual(spin_up.stage_years(lambda years: years + 25), (declared[0] + 25, declared[1]))

    def test_years_named_in_the_environment_stand_as_named(self):
        with mock.patch.dict(os.environ, {**FULL_GAME, spin_up.SPIN_UP_YEARS_ENV: "4,2"}, clear=True):
            self.assertEqual(spin_up.stage_years(lambda years: years + 25), (4, 2))


class FirstStageYears(unittest.TestCase):
    def test_the_declared_bound_stands_where_the_stage_may_stop_early(self):
        self.assertEqual(spin_up_stop.the_declared_bound(30), 30)

    def test_a_stage_that_runs_to_the_rest_is_never_shorter_than_the_years_the_rest_takes(self):
        years = int(spin_up_stop.FIRST_STAGE_YEARS_TO_REST)
        self.assertEqual(spin_up_stop.long_enough_to_rest(30), years)
        self.assertEqual(spin_up_stop.long_enough_to_rest(years + 20), years + 20)


class Rules(unittest.TestCase):
    def test_the_two_answers(self):
        self.assertTrue(spin_up_stop.on_a_quiet_year())
        self.assertFalse(spin_up_stop.at_its_bound())
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_stops_early, spin_up_stop.on_a_quiet_year)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_stops_early, spin_up_stop.at_its_bound)
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_first_stage_years, spin_up_stop.the_declared_bound)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_first_stage_years, spin_up_stop.long_enough_to_rest)


if __name__ == "__main__":
    unittest.main()
