"""The scenario module: the rules of its setup facts, its commands on its world state, and the text it writes in the player's units.
Each test calls one function or one command handler on values written out here; no game is built."""
QUICK_TOPIC = True

import unittest

from sim.scenario import quantity_text, rules
from sim.scenario.api import (AdvanceYear, OpenScenario, RecordOpeningLiteracy, ScenarioSources, SetEndYear, SetFog,
                              SetFuzzyEstimates, SetYear, money_short, money_word, scenario_slot_of, to_base)
from sim.scenario.module import Scenario
from sim.scenario.state import ScenarioWorld
from sim.tests import module_harness

CONFIGURATION = {"start_year": 100, "horizon_years": 500, "eminence_danger": 40.0, "suspicion_danger": 70.0, "immortal": False,
                 "founder_life_mean": 55.0, "founder_life_sd": 9.0}
REGISTRY = {"units": {"tonne": {"dimension": "mass", "name": "tonne", "symbol": "t", "factor": 1000.0},
                      "pound": {"dimension": "mass", "name": "pound", "plural": "pounds", "symbol": "lb", "factor": 0.45359237},
                      "hour": {"dimension": "money", "name": "hour", "symbol": "h", "factor_from": "hours_per_coin",
                               "label_from": "civ_currency"}}}
ROME = {"id": "rome", "name": "Rome", "year": 100, "currency_words": {"long": "denarii", "short": "den"}}


def display(chosen=None, civilisation=ROME, context=lambda: {"hours_per_coin": 2.0}):
    return quantity_text.Display(civilisation, REGISTRY, chosen or {}, context)


class Rules(unittest.TestCase):
    def test_a_civilisation_brings_its_own_start_year(self):
        self.assertEqual(rules.opening_start_year({"year": 900}, CONFIGURATION), 900)
        self.assertEqual(rules.opening_start_year({}, CONFIGURATION), 100)

    def test_the_horizon_ends_where_the_player_set_it_else_after_the_configured_years(self):
        self.assertEqual(rules.horizon_end_year(350, CONFIGURATION), 350)
        self.assertEqual(rules.horizon_end_year(None, CONFIGURATION), 600)

    def test_a_society_with_no_name_is_this_society(self):
        self.assertEqual(rules.society_name({}), "this society")
        self.assertEqual(rules.society_name(ROME), "Rome")

    def test_the_danger_lines_and_the_founder_life_terms_come_from_the_configuration(self):
        self.assertEqual(rules.danger_lines(CONFIGURATION), {"eminence": 40.0, "suspicion": 70.0})
        self.assertEqual(rules.founder_life_terms(CONFIGURATION, 5),
                         {"immortal": False, "minimum": 5, "mean": 55.0, "spread": 9.0})

    def test_the_scenario_slot_of_a_save_is_empty_when_the_save_lacks_it(self):
        self.assertEqual(scenario_slot_of({"modules": {"scenario": {"year": 7}}}), {"year": 7})
        self.assertEqual(scenario_slot_of({"modules": {}}), {})
        self.assertEqual(scenario_slot_of([]), {})


class Commands(unittest.TestCase):
    def build(self, **world):
        return module_harness.build(Scenario, world=ScenarioWorld(**world), module_id="scenario")

    def opened(self):
        module = self.build()
        module.open_scenario(OpenScenario(
            civilisation=dict(ROME, year=900, literacy_general=0.3, literacy_elite=0.9), configuration=dict(CONFIGURATION),
            manual=True, events=False, bounty_set={"a"}, sources=ScenarioSources(
                load_civilisation=lambda civilisation_id: {"id": civilisation_id}, kit_capital=lambda kit, civ: 7.0 * len(kit),
                display_units=lambda: (REGISTRY, {}, lambda: {}))))
        return module

    def test_advancing_the_year_moves_the_clock_by_one_and_answers_the_new_year(self):
        module = self.build(year=100)
        self.assertEqual(module.advance_year(AdvanceYear()), 101)
        self.assertEqual(module.year(), 101)

    def test_setting_the_year_replaces_it(self):
        module = self.build(year=100)
        module.set_year(SetYear(1301))
        self.assertEqual(module.year(), 1301)

    def test_the_fog_and_the_fuzzy_estimates_are_set_and_a_salt_is_kept_unless_replaced(self):
        module = self.build()
        module.set_fog(SetFog(True))
        module.set_fuzzy_estimates(SetFuzzyEstimates(True, 55))
        module.set_fuzzy_estimates(SetFuzzyEstimates(False))
        self.assertEqual((module.fog(), module.fuzzy_estimates(), module.fuzzy_salt()), (True, False, 55))

    def test_opening_the_scenario_takes_the_civilisations_date_and_keeps_its_opening_values(self):
        module = self.opened()
        self.assertEqual((module.start_year(), module.society_name(), module.events_enabled()), (900, "Rome", False))
        self.assertEqual(module.automation(), {"manual": True, "bounty_set": {"a"}})
        self.assertEqual(module.civilisation_record("han"), {"id": "han"})
        self.assertEqual(module.kit_capital("poor_scholar"), 7.0 * len("poor_scholar"))

    def test_the_end_year_is_unset_until_it_is_sent(self):
        module = self.opened()
        self.assertEqual(module.horizon_end_year(), 1400)
        module.set_end_year(SetEndYear(1000))
        self.assertEqual(module.horizon_end_year(), 1000)

    def test_recording_the_opening_literacy_moves_it_from_the_civilisation_to_the_opening_values(self):
        module = self.opened()
        module.record_opening_literacy(RecordOpeningLiteracy(0.25, 0.85))
        self.assertNotIn("literacy_general", module.civilisation)
        self.assertNotIn("literacy_elite", module.civilisation)
        self.assertEqual((module.start_civilisation["literacy_general"], module.start_civilisation["literacy_elite"]), (0.25, 0.85))


class Text(unittest.TestCase):
    # presentation: these test the wording the player reads
    def test_money_and_mass_read_as_the_game_always_wrote_them_with_no_unit_chosen(self):
        self.assertEqual(quantity_text.money_text(1234.4, display(), grouped=True), "1,234 denarii")
        self.assertEqual(quantity_text.money_text(1234.4, display(), short=True), "1234 den")
        self.assertEqual(quantity_text.mass_text(1, display()), "1 tonne")
        self.assertEqual(quantity_text.mass_rate_text(12, display()), "12 t/year")
        self.assertEqual(quantity_text.mass_rate_text(12, display(), short=False), "12 tonnes a year")

    def test_a_chosen_unit_converts_the_number_and_names_the_unit(self):
        self.assertEqual(quantity_text.mass_text(1, display({"mass": "pound"}), digits=0), "2205 pounds")

    def test_the_value_of_an_hour_is_asked_only_when_a_unit_needs_it(self):
        asked = []
        plain = display(context=lambda: asked.append(1) or {})
        quantity_text.mass_text(3, plain)
        self.assertEqual(asked, [])
        quantity_text.mass_text(3, display({"mass": "pound"}, context=lambda: asked.append(1) or {}))
        self.assertEqual(len(asked), 1)

    def test_a_number_with_separators_has_no_unit(self):
        self.assertEqual(quantity_text.plain_number(1234567.4), "1,234,567")

    def test_the_coin_words_fall_back_to_the_currency_then_to_denarii(self):
        self.assertEqual((money_word({"currency": "silver penny"}), money_short({"currency": "silver penny"})),
                         ("silver penny", "silver penny"))
        self.assertEqual((money_word(None), money_short(None)), ("denarii", "den"))

    def test_a_unit_converts_to_base_by_its_factor(self):
        self.assertEqual(to_base(REGISTRY, "tonne", 2.0, {}), 2000.0)


if __name__ == "__main__":
    unittest.main()
