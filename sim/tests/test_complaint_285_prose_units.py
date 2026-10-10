"""Complaint 285: quantities inside engine sentences, civilisation display units and units typed in commands.

No game is built: a stand-in with the two things the unit layer reads from a game (the civilisation's
currency words and what one labour hour is worth in coin) is enough for the sentence formatters.
"""

QUICK_TOPIC = True

import json
import re
import unittest
from types import SimpleNamespace

from sim.engine import units as U
from sim.engine import units_prose as P
from sim.ui.proto import quantity_units, typed

ROME_WORDS = {"long": "denarii", "short": "den"}
BLOBS = {
    "blob_area": {"name": "blob", "symbol": "blob", "dimension": "area", "factor": 0.15},
    "blob_mass": {"name": "blob", "symbol": "blob", "dimension": "mass", "factor": 7.0},
    "blob_money": {"name": "blob", "symbol": "blob", "dimension": "money", "factor": 3.0},
    "blob_degree": {"name": "blob", "symbol": "blob", "dimension": "temperature", "factor": 2.0, "offset": 10.0},
}
NATIVE_WORD = re.compile(r"\btonnes?\b|\bhectares?\b|\bdenarii\b|\bden\b|degrees? Celsius|square metres?|\bkg\b|\bha\b")


def fake_game(civ_id="rome_100ad"):
    """A stand-in game: two coin to the labour hour, so one coin is half an hour."""
    labour = SimpleNamespace(money_per_labour_hour=lambda: 0.5)
    return SimpleNamespace(civ={"id": civ_id, "currency_words": ROME_WORDS}, labour=labour)


class UnitSetup(unittest.TestCase):
    def setUp(self):
        self.original = (U.registry(), dict(U.PREFERENCES), dict(U.CIV_DEFAULTS))
        registry = json.loads(json.dumps(U.load_units(U.ROOT)))
        registry["units"].update(BLOBS)
        U.set_registry(registry)
        U.set_preferences({})
        U.set_civ_defaults(None)
        self.game = fake_game()

    def tearDown(self):
        U.set_registry(None)
        U.set_preferences(self.original[1])
        U.CIV_DEFAULTS.clear()
        U.CIV_DEFAULTS.update(self.original[2])


class DefaultText(UnitSetup):
    def test_default_sentences_read_as_the_game_always_wrote_them(self):
        self.assertEqual(P.money_text(1234.4, self.game, grouped=True), "1,234 denarii")
        self.assertEqual(P.money_text(1234.4, self.game, short=True), "1234 den")
        self.assertEqual(P.mass_text(12, self.game), "12 tonnes")
        self.assertEqual(P.mass_text(1, self.game), "1 tonne")
        self.assertEqual(P.mass_text(12, self.game, short=True), "12 t")
        self.assertEqual(P.mass_rate_text(12, self.game), "12 t/year")
        self.assertEqual(P.mass_rate_text(12, self.game, short=False), "12 tonnes a year")
        self.assertEqual(P.area_text(5, self.game), "5 hectares")
        self.assertEqual(P.area_text(40, self.game, unit="square_metre"), "40 square metres")
        self.assertEqual(P.temperature_text(100, self.game), "100 degrees Celsius")
        self.assertEqual(P.mass_per_area_text(0.0004, self.game, digits=4), "0.0004 tonnes per square metre")
        self.assertEqual(P.mass_per_area_text(0.5, self.game, digits=2, area="hectare"), "0.50 tonnes per hectare")

    def test_no_game_still_writes_the_native_text(self):
        self.assertEqual(P.mass_text(3), "3 tonnes")
        self.assertEqual(P.area_text(3), "3 hectares")


class ChosenText(UnitSetup):
    def test_every_dimension_follows_the_chosen_unit(self):
        U.set_preferences({"mass": "blob_mass", "area": "blob_area", "money": "blob_money", "temperature": "blob_degree"})
        cases = {
            "mass": (P.mass_text(14, self.game), "2000 blobs"),
            "mass rate": (P.mass_rate_text(14, self.game), "2000 blob/year"),
            "area": (P.area_text(3, self.game), "20 blobs"),
            "small area": (P.area_text(1500, self.game, unit="square_metre"), "1 blob"),
            "money": (P.money_text(100, self.game), "67 blobs"),
            "short money": (P.money_text(100, self.game, short=True), "67 blob"),
            "temperature": (P.temperature_text(100, self.game), "45 blobs"),
        }
        for name, (text, expected) in cases.items():
            self.assertEqual(text, expected, name)
            self.assertIsNone(NATIVE_WORD.search(text), (name, text))

    def test_a_yield_per_area_changes_both_parts(self):
        U.set_preferences({"mass": "blob_mass", "area": "blob_area"})
        text = P.mass_per_area_text(0.0004, self.game, digits=0)
        self.assertEqual(text, "86 blobs per blob")

    def test_the_players_unit_names_come_from_the_registry(self):
        U.set_preferences({"mass": "pound", "area": "acre", "temperature": "fahrenheit", "money": "labour_hour"})
        self.assertEqual(P.mass_text(1, self.game, digits=1), "2204.6 pounds")
        self.assertEqual(P.area_text(1, self.game, digits=2), "2.47 acres")
        self.assertEqual(P.temperature_text(100, self.game), "212 degrees Fahrenheit")
        self.assertEqual(P.money_text(100, self.game), "200 labour hours")


class TaggedFields(UnitSetup):
    def test_a_producer_can_tag_a_field_no_name_rule_covers(self):
        U.set_preferences({"mass": "blob_mass"})
        reply = U.tagged({"ok": True, "haul": 14.0, "plain": 14.0}, haul="mass:tonne")
        shown = U.add_display(reply, self.game)
        self.assertEqual(shown["haul_display"]["value"], 2000.0)
        self.assertEqual(shown["haul_display"]["unit"], "blob")
        self.assertNotIn("plain_display", shown)
        self.assertEqual(shown["haul"], 14.0)
        self.assertEqual(shown["field_units"], {"haul": "mass:tonne"})

    def test_a_tag_naming_the_wrong_dimension_is_ignored(self):
        U.set_preferences({"mass": "blob_mass"})
        shown = U.add_display(U.tagged({"haul": 14.0}, haul="area:tonne"), self.game)
        self.assertNotIn("haul_display", shown)

    def test_a_tagged_field_reaches_the_text_screen(self):
        from sim.ui.units_text import for_text
        U.set_preferences({"mass": "blob_mass"})
        text_reply = for_text(U.add_display(U.tagged({"ok": True, "haul": 14.0}, haul="mass:tonne"), self.game), False)
        self.assertEqual(text_reply["haul"], 2000.0)


class CivilisationUnits(UnitSetup):
    def test_a_civilisation_names_its_own_units_as_the_default(self):
        U.set_civ_defaults({"display_units": {"area": "iugerum", "mass": "libra"}})
        self.assertEqual(P.area_text(0.2518, self.game, digits=0), "1 iugerum")
        self.assertEqual(P.area_text(2.518, self.game, digits=0), "10 iugera")
        self.assertEqual(P.mass_text(0.0003272, self.game, digits=0), "1 libra")

    def test_the_player_choice_beats_the_civilisation(self):
        U.set_civ_defaults({"display_units": {"area": "iugerum"}})
        U.set_preferences({"area": "acre"})
        self.assertEqual(U.chosen_units()["area"], "acre")
        U.set_preferences({"area": "hectare"})
        self.assertEqual(P.area_text(5, self.game), "5 hectares")

    def test_no_civilisation_units_and_nothing_chosen_changes_nothing(self):
        U.set_civ_defaults({})
        reply = {"ok": True, "farm_hectares": 5.0}
        self.assertIs(U.add_display(reply, self.game), reply)

    def test_shipped_civilisations_name_only_units_the_registry_allows(self):
        from sim.engine.civ_start_check import load_civilisations
        registry = U.registry()
        civs = load_civilisations(U.ROOT)
        named = {civ_id for civ_id, civ in civs.items() if civ.get("display_units")}
        self.assertTrue(named, "at least one civilisation names its own units")
        for civ_id, civ in civs.items():
            self.assertEqual(U.check_civ_units(registry, civ_id, civ), [], civ_id)

    def test_a_civilisation_cannot_name_another_civilisations_unit(self):
        registry = U.registry()
        problems = U.check_civ_units(registry, "han_china_100ad", {"display_units": {"mass": "libra", "area": "acre"}})
        self.assertEqual(len(problems), 1)
        self.assertIn("libra", problems[0])
        problems = U.check_civ_units(registry, "rome_100ad", {"display_units": {"area": "kilogram"}})
        self.assertEqual(len(problems), 1)

    def test_every_civilisation_unit_is_offered_only_to_its_civilisation(self):
        registry = U.registry()
        self.assertIn("iugerum", U.available_units(registry, "area", "rome_100ad"))
        self.assertNotIn("iugerum", U.available_units(registry, "area", "han_china_100ad"))
        self.assertIn("mu", U.available_units(registry, "area", "han_china_100ad"))


class QuantitiesInCommands(UnitSetup):
    def read(self, cmd, target):
        return quantity_units.read_target_quantity(cmd, "n", 0, target, self.game)

    def test_without_a_unit_the_quantity_is_the_engines_own(self):
        U.set_preferences({"area": "acre"})
        self.assertEqual(self.read({"n": 10}, "farm"), (10.0, None))

    def test_a_unit_converts_through_the_registry(self):
        quantity, error = self.read({"n": 10, "unit": "acre"}, "farm")
        self.assertIsNone(error)
        self.assertAlmostEqual(quantity, 4.0468564224)
        quantity, _ = self.read({"n": "10 acres"}, "forest")
        self.assertAlmostEqual(quantity, 4.0468564224)
        quantity, _ = self.read({"n": 2, "unit": "tonnes"}, "material")
        self.assertEqual(quantity, 2.0)
        quantity, _ = self.read({"n": 2000, "unit": "kg"}, "mine")
        self.assertAlmostEqual(quantity, 2.0)
        quantity, _ = self.read({"n": 3, "unit": "ha"}, "nitre")
        self.assertAlmostEqual(quantity, 30000.0)

    def test_the_shown_unit_means_the_one_the_player_displays(self):
        U.set_preferences({"mass": "pound"})
        quantity, error = self.read({"n": 2204.62262185, "unit": "shown"}, "material")
        self.assertIsNone(error)
        self.assertAlmostEqual(quantity, 1.0, places=5)

    def test_a_money_amount_takes_a_unit_too(self):
        quantity, error = quantity_units.read_quantity({"amount": 200, "unit": "labour hours"}, "amount", None,
                                                       "money", "civ_coin", self.game)
        self.assertIsNone(error)
        self.assertAlmostEqual(quantity, 100.0)

    def test_a_unit_of_another_kind_is_refused_with_the_choices(self):
        quantity, error = self.read({"n": 3, "unit": "kg"}, "farm")
        self.assertIsNone(quantity)
        self.assertIn("hectare", error)
        quantity, error = self.read({"n": 3, "unit": "libra"}, "farm")
        self.assertIsNone(quantity)

    def test_a_civilisations_own_unit_is_accepted_only_there(self):
        quantity, error = self.read({"n": 10, "unit": "iugera"}, "farm")
        self.assertIsNone(error)
        self.assertAlmostEqual(quantity, 2.518)
        han = fake_game("han_china_100ad")
        quantity, error = quantity_units.read_target_quantity({"n": 10, "unit": "iugera"}, "n", 0, "farm", han)
        self.assertIsNone(quantity)

    def test_targets_with_no_dimension_take_no_unit(self):
        self.assertEqual(self.read({"n": 4}, "housing"), (4.0, None))

    def test_a_bad_number_is_still_named(self):
        quantity, error = self.read({"n": "banana", "unit": "acre"}, "farm")
        self.assertIsNone(quantity)
        self.assertIn("number", error)

    def test_typed_commands_carry_the_unit_word(self):
        parsed, error = typed._parse_buy_or_quote("buy", "farm 10 acre", ["farm", "acre"], [10.0], False)
        self.assertIsNone(error)
        self.assertEqual(parsed, {"cmd": "buy", "what": "farm", "n": 10.0, "unit": "acre"})
        parsed, _ = typed._parse_buy_or_quote("buy", "mine coal 500 t", ["mine", "coal", "t"], [500.0], False)
        self.assertEqual(parsed, {"cmd": "buy", "what": "mine", "material": "coal", "n": 500.0, "unit": "t"})
        parsed, _ = typed._parse_buy_or_quote("buy", "mine coal 500", ["mine", "coal"], [500.0], False)
        self.assertEqual(parsed, {"cmd": "buy", "what": "mine", "material": "coal", "n": 500.0})
        parsed, _ = typed._parse_sell("sell", "farm 40 acres", ["farm", "acres"], [40.0], False)
        self.assertEqual(parsed, {"cmd": "sell", "what": "farm", "n": 40.0, "unit": "acres"})
        parsed, _ = typed._parse_sell("sell", "iron 50 lb", ["iron", "lb"], [50.0], False)
        self.assertEqual(parsed, {"cmd": "sell", "material": "iron", "n": 50.0, "unit": "lb"})


if __name__ == "__main__":
    unittest.main()
