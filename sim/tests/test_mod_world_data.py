"""Mods change small world data: foreign economies, starting kits, labels, strategies and civ lists."""

QUICK_TOPIC = True

import json
import unittest
import unittest.mock

from sim.engine.data import ROOT, STARTING_KITS, WIN_CONDITION_LABELS
from sim.engine.mod_world_data import load_starting_kits, load_win_condition_labels
from sim.engine.mods import ModError
from sim.engine.mods_civ import apply_mod_civilization
from sim.engine.mods_strategies import mod_strategy_names, mod_strategy_path
from sim.engine.mods_constants import apply_override, constant_overrides
from sim.engine.mods_world import merge_mod_list, merge_mod_map
from sim.tests.test_mod_removal_and_civs import ModTestBase

ACME = "test_acme_k3f9"
BETA = "test_beta_k3f9"


class WorldDataTests(ModTestBase):
    def write(self, mod_id, relative, document):
        path = self.mods_dir / mod_id / "data" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))

    def economies(self):
        base = [{"civilization": "han", "enabled": True}, {"civilization": "persia", "enabled": False}]
        return merge_mod_list(base, self.manifests(), "world/foreign_economies.json", "economies",
                              "civilization", "foreign economy")

    def test_mod_adds_a_partner_economy(self):
        self.add_mod(ACME)
        self.write(ACME, "world/foreign_economies.json",
                   {"economies": [{"civilization": ACME + ":realm", "enabled": True}]})
        self.assertIn(ACME + ":realm", [record["civilization"] for record in self.economies()])

    def test_mod_enables_a_listed_partner_and_keeps_other_fields(self):
        self.add_mod(ACME)
        self.write(ACME, "world/foreign_economies.json",
                   {"economies": [{"civilization": "persia", "override": True, "enabled": True}]})
        persia = [record for record in self.economies() if record["civilization"] == "persia"][0]
        self.assertTrue(persia["enabled"])

    def test_mod_removes_a_partner(self):
        self.add_mod(ACME)
        self.write(ACME, "world/foreign_economies.json",
                   {"economies": [{"civilization": "han", "remove": True}]})
        self.assertNotIn("han", [record["civilization"] for record in self.economies()])

    def test_duplicate_partner_is_an_error(self):
        self.add_mod(ACME)
        self.write(ACME, "world/foreign_economies.json", {"economies": [{"civilization": "han"}]})
        with self.assertRaises(ModError):
            self.economies()

    def test_unrelated_mods_enabling_the_same_field_name_both(self):
        self.add_mod(ACME)
        self.add_mod(BETA)
        for mod_id in (ACME, BETA):
            self.write(mod_id, "world/foreign_economies.json",
                       {"economies": [{"civilization": "persia", "override": True, "enabled": True}]})
        with self.assertRaises(ModError) as caught:
            self.economies()
        self.assertIn(ACME, str(caught.exception))
        self.assertIn(BETA, str(caught.exception))

    def kits(self):
        return merge_mod_map({"poor": {"labourer_years": 4.0, "desc": "x"}}, self.manifests(),
                             "world/starting_kits.json", "kits", "starting kit")

    def test_mod_adds_a_namespaced_kit(self):
        self.add_mod(ACME)
        self.write(ACME, "world/starting_kits.json",
                   {"kits": {ACME + ":noble": {"labourer_years": 9.0, "desc": "y"}}})
        self.assertEqual(self.kits()[ACME + ":noble"]["labourer_years"], 9.0)

    def test_kit_outside_namespace_is_refused(self):
        self.add_mod(ACME)
        self.write(ACME, "world/starting_kits.json", {"kits": {"noble": {"labourer_years": 9.0, "desc": "y"}}})
        with self.assertRaises(ModError):
            self.kits()

    def test_mod_retunes_and_removes_kits(self):
        self.add_mod(ACME)
        self.write(ACME, "world/starting_kits.json", {"kits": {"poor": {"override": True, "labourer_years": 1.0}}})
        self.assertEqual(self.kits()["poor"], {"labourer_years": 1.0, "desc": "x"})
        self.write(ACME, "world/starting_kits.json", {"kits": {"poor": {"remove": True}}})
        self.assertNotIn("poor", self.kits())

    def test_mod_labels_a_new_metric_and_rewords_one(self):
        self.add_mod(ACME)
        self.write(ACME, "ui/win_condition_labels.json",
                   {"labels": {"literacy_general": {"override": True, "text": "everyone reads (%s)"},
                               "mana_share": {"text": "mana reaches %s"}}})
        labels = load_win_condition_labels(ROOT, str(self.mods_dir))
        self.assertEqual(labels["literacy_general"], "everyone reads (%s)")
        self.assertEqual(labels["mana_share"], "mana reaches %s")

    def test_base_data_files_carry_the_shipped_entries(self):
        self.assertIn("poor_scholar", STARTING_KITS)
        self.assertIn("literacy_general", WIN_CONDITION_LABELS)
        self.assertIn("poor_scholar", load_starting_kits(ROOT, str(self.mods_dir)))

    def test_mod_strategy_resolves_only_in_its_own_namespace(self):
        self.add_mod(ACME)
        self.write(ACME, "strategies/" + ACME + "+rush.json", {"order": ["a"]})
        manifests = self.manifests()
        self.assertTrue(mod_strategy_path(ACME + ":rush", manifests).endswith(ACME + "+rush.json"))
        self.assertIsNone(mod_strategy_path("rush", manifests))
        self.assertEqual(mod_strategy_names(manifests), [ACME + ":rush"])

    def test_mod_adds_patches_and_removes_tech_effects(self):
        self.add_mod(ACME)
        self.write(ACME, "civilizations/_TECH_EFFECTS.json",
                   {"_doc": "notes are ignored", ACME + ":spell": {"literacy_general": 0.1},
                    "paper": {"override": True, "literacy_elite": 0.9}, "press": {"remove": True}})
        base = {"paper": {"literacy_general": 0.02, "literacy_elite": 0.05}, "press": {"w_novelty": 0.1}}
        merged = merge_mod_map(base, self.manifests(), "civilizations/_TECH_EFFECTS.json", None, "tech effect")
        self.assertEqual(merged["paper"], {"literacy_general": 0.02, "literacy_elite": 0.9})
        self.assertEqual(merged[ACME + ":spell"], {"literacy_general": 0.1})
        self.assertNotIn("press", merged)

    def test_mod_overrides_a_declared_number_with_a_reason(self):
        self.add_mod(ACME)
        self.write(ACME, "constants.json", {"constants": {"SOME_RATE": {"value": 0.5, "why": "magic world"}}})
        found = constant_overrides(str(self.mods_dir))["SOME_RATE"]
        self.assertEqual((found.mod_id, found.value), (ACME, 0.5))
        self.assertEqual(apply_override("SOME_RATE", 2.0, str(self.mods_dir)).value, 0.5)
        self.assertIsNone(apply_override("OTHER", 2.0, str(self.mods_dir)))

    def test_override_without_a_reason_or_of_another_type_is_refused(self):
        self.add_mod(ACME)
        self.write(ACME, "constants.json", {"constants": {"SOME_RATE": {"value": 0.5}}})
        with self.assertRaises(ModError):
            constant_overrides(str(self.mods_dir))
        self.write(ACME, "constants.json", {"constants": {"SOME_RATE": {"value": "high", "why": "x"}}})
        constant_overrides.cache_clear()
        with self.assertRaises(ModError):
            apply_override("SOME_RATE", 2.0, str(self.mods_dir))

    def test_unrelated_mods_overriding_one_number_name_both(self):
        for mod_id in (ACME, BETA):
            self.add_mod(mod_id)
            self.write(mod_id, "constants.json", {"constants": {"SOME_RATE": {"value": 1.0, "why": "x"}}})
        with self.assertRaises(ModError) as caught:
            constant_overrides(str(self.mods_dir))
        self.assertIn(ACME, str(caught.exception))
        self.assertIn(BETA, str(caught.exception))

    def test_declare_returns_the_override_and_records_who(self):
        from sim import constants
        constant_overrides.cache_clear()
        with unittest.mock.patch("sim.constants._mod_override",
                                 return_value=constant_overrides.__wrapped__(str(self._mod_with_rate()))["RATE_X"]):
            value = constants.declare("TEST_ONLY_RATE_X", 2.0, kind="temporary_heuristic", unit="1",
                                      why="test")
        self.addCleanup(constants.REGISTRY.pop, "TEST_ONLY_RATE_X", None)
        self.assertEqual(value, 0.25)
        self.assertEqual(constants.REGISTRY["TEST_ONLY_RATE_X"]["overridden_by"], ACME)

    def _mod_with_rate(self):
        self.add_mod(ACME)
        self.write(ACME, "constants.json", {"constants": {"RATE_X": {"value": 0.25, "why": "x"}}})
        return self.mods_dir

    def civ_patch(self, mod_id, patch):
        self.add_mod(mod_id, civs={"rome": dict(patch, override=True)})

    def apply(self, base):
        return apply_mod_civilization("rome", base, self.manifests())

    def test_mod_appends_a_hazard_to_a_base_civ(self):
        self.civ_patch(ACME, {"append": {"hazards": [{"name": "Mana storm", "staff_loss": 0.1, "years": [5, 9]}]}})
        civ = self.apply({"id": "rome", "hazards": [{"name": "Plague", "years": [1, 2]}]})
        self.assertEqual([hazard["name"] for hazard in civ["hazards"]], ["Plague", "Mana storm"])
        self.assertNotIn("append", civ)

    def test_mod_removes_a_hazard_by_name(self):
        self.civ_patch(ACME, {"remove_items": {"hazards": ["Plague"]}})
        civ = self.apply({"id": "rome", "hazards": [{"name": "Plague"}, {"name": "Flood"}]})
        self.assertEqual([hazard["name"] for hazard in civ["hazards"]], ["Flood"])

    def test_removing_a_missing_hazard_is_an_error(self):
        self.civ_patch(ACME, {"remove_items": {"hazards": ["Nope"]}})
        with self.assertRaises(ModError):
            self.apply({"id": "rome", "hazards": []})

    def test_mod_adds_and_removes_a_seat_in_the_cast(self):
        self.civ_patch(ACME, {"append": {"cast.seats": [{"id": "guild"}]}, "remove_items": {"cast.actors": ["old"]}})
        civ = self.apply({"id": "rome", "cast": {"seats": [{"id": "founder"}], "actors": [{"actor_id": "old"}]}})
        self.assertEqual([seat["id"] for seat in civ["cast"]["seats"]], ["founder", "guild"])
        self.assertEqual(civ["cast"]["actors"], [])

    def test_two_unrelated_mods_may_both_append(self):
        self.civ_patch(ACME, {"append": {"hazards": [{"name": "A"}]}})
        self.civ_patch(BETA, {"append": {"hazards": [{"name": "B"}]}})
        civ = self.apply({"id": "rome", "hazards": []})
        self.assertEqual([hazard["name"] for hazard in civ["hazards"]], ["A", "B"])

    def test_append_after_an_unrelated_whole_replacement_names_both(self):
        self.civ_patch(ACME, {"hazards": []})
        self.civ_patch(BETA, {"append": {"hazards": [{"name": "B"}]}})
        with self.assertRaises(ModError) as caught:
            self.apply({"id": "rome", "hazards": [{"name": "X"}]})
        self.assertIn(ACME, str(caught.exception))
        self.assertIn(BETA, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
