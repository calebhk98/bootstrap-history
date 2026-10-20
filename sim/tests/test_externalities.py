"""The externality door: providers add deaths and scale land yields, and with none registered nothing changes."""

QUICK_TOPIC = True

import unittest

from sim.engine import externalities, mod_code


class ExternalityRegistryTests(unittest.TestCase):
    def setUp(self):
        externalities.clear()

    def tearDown(self):
        externalities.clear()

    def test_with_no_provider_the_inputs_come_back_unchanged(self):
        deaths = {"children": 3.0}
        self.assertIs(externalities.add_deaths(deaths, None, 1300), deaths)
        self.assertEqual(externalities.yield_factors(None, 1300), {})

    def test_deaths_add_to_the_epidemic_deaths_by_band(self):
        externalities.register(lambda sim, year: {"deaths_by_band": {"children": 2.0, "elderly": 1.0}})
        externalities.register(lambda sim, year: {"deaths_by_band": {"children": 0.5}})
        total = externalities.add_deaths({"children": 3.0, "working_age": 4.0}, None, 1300)
        self.assertEqual(total, {"children": 5.5, "working_age": 4.0, "elderly": 1.0})

    def test_a_negative_death_count_is_ignored(self):
        externalities.register(lambda sim, year: {"deaths_by_band": {"children": -9.0}})
        self.assertEqual(externalities.add_deaths({"children": 1.0}, None, 1300), {"children": 1.0})

    def test_yield_factors_multiply_and_stay_between_zero_and_one(self):
        externalities.register(lambda sim, year: {"yield_factor_by_tile": {"a": 0.5, "b": 2.0, "c": -1.0}})
        externalities.register(lambda sim, year: {"yield_factor_by_tile": {"a": 0.5}})
        self.assertEqual(externalities.yield_factors(None, 1300), {"a": 0.25, "b": 1.0, "c": 0.0})

    def test_a_provider_that_answers_nothing_is_harmless(self):
        externalities.register(lambda sim, year: None)
        self.assertEqual(externalities.yield_factors(None, 1300), {})
        self.assertEqual(externalities.add_deaths({}, None, 1300), {})

    def test_a_mod_registers_through_the_code_api_once(self):
        api = mod_code.ModCodeApi("test_acme_k3f9")
        provider = lambda sim, year: {}
        api.externality(provider)
        api.externality(provider)
        self.assertEqual(externalities.PROVIDERS, [provider])


if __name__ == "__main__":
    unittest.main()
