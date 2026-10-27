"""The externality point: the answers of the providers add deaths and scale land yields, and with none nothing changes. The rules
are plain functions of the answers; the mod door records its provider as an answer to the demography module's point."""

QUICK_TOPIC = True

import unittest

from sim.agriculture import rules as agriculture_rules
from sim.engine import mod_code
from sim.demography import rules as demography_rules


class ExternalityRuleTests(unittest.TestCase):
    def test_with_no_answer_the_deaths_come_back_unchanged(self):
        deaths = {"children": 3.0}
        self.assertIs(demography_rules.deaths_with_externalities(deaths, []), deaths)

    def test_with_no_answer_there_is_no_yield_factor(self):
        self.assertEqual(agriculture_rules.yield_factors([]), {})

    def test_deaths_add_to_the_epidemic_deaths_by_band(self):
        answers = [{"deaths_by_band": {"children": 2.0, "elderly": 1.0}}, {"deaths_by_band": {"children": 0.5}}]
        total = demography_rules.deaths_with_externalities({"children": 3.0, "working_age": 4.0}, answers)
        self.assertEqual(total, {"children": 5.5, "working_age": 4.0, "elderly": 1.0})

    def test_a_negative_death_count_is_ignored(self):
        self.assertEqual(demography_rules.deaths_with_externalities({"children": 1.0}, [{"deaths_by_band": {"children": -9.0}}]),
                         {"children": 1.0})

    def test_yield_factors_multiply_and_stay_between_zero_and_one(self):
        answers = [{"yield_factor_by_tile": {"a": 0.5, "b": 2.0, "c": -1.0}}, {"yield_factor_by_tile": {"a": 0.5}}]
        self.assertEqual(agriculture_rules.yield_factors(answers), {"a": 0.25, "b": 1.0, "c": 0.0})

    def test_a_provider_that_answers_nothing_is_harmless(self):
        self.assertEqual(agriculture_rules.yield_factors([None]), {})
        self.assertEqual(demography_rules.deaths_with_externalities({}, [None]), {})


class ExternalityDoorTests(unittest.TestCase):
    def test_a_mod_provides_through_the_code_api_to_the_point(self):
        api = mod_code.ModCodeApi("test_acme_k3f9")
        provider = lambda sim, year: {}
        api.externality(provider)
        self.assertEqual(api.operations.provided["externality"], (provider,))

    def test_one_mods_providers_are_not_another_games(self):
        first, second = mod_code.ModCodeApi("test_acme_k3f9"), mod_code.ModCodeApi("test_acme_k3f9")
        first.externality(lambda sim, year: {})
        self.assertEqual(second.operations.provided, {})


if __name__ == "__main__":
    unittest.main()
