"""A mod declares a civilisation as a patch of another with `variant_of` (Complaint 636): the file names only what differs."""

QUICK_TOPIC = True

from unittest import mock
import unittest

from sim.engine import data
from sim.engine.mods import ModError
from sim.engine.mods_civ import check_all_civilizations
from sim.tests.test_mod_removal_and_civs import ModTestBase

ACME = "test_acme_k3f9"
VARIANT = ACME + ":rome_with_a_house"


class VariantTests(ModTestBase):
    def load(self, name):
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            return data.load_civ(name)

    def test_a_variant_is_its_base_with_only_the_named_fields_changed(self):
        base = self.load("rome_100ad")
        self.add_mod(ACME, civs={VARIANT: {"id": VARIANT, "variant_of": "rome_100ad", "name": "Rome with a house",
                                          "values": {"w_military": 0.9}}})
        civ = self.load(VARIANT)
        self.assertEqual(civ["id"], VARIANT)
        self.assertEqual(civ["name"], "Rome with a house")
        self.assertEqual(civ["variant_of"], "rome_100ad")
        self.assertEqual(civ["values"]["w_military"], 0.9)
        self.assertEqual(civ["values"]["w_commerce"], base["values"]["w_commerce"])
        self.assertEqual(civ["starting_techs"], base["starting_techs"])
        self.assertEqual(civ["home_tiles"], base["home_tiles"])

    def test_list_operators_edit_the_inherited_cast(self):
        base = self.load("rome_100ad")
        actor = {"actor_id": "house:one", "kind": "church", "name": "house", "money": 1.0}
        self.add_mod(ACME, civs={VARIANT: {"id": VARIANT, "variant_of": "rome_100ad", "append": {"cast.actors": [actor]}}})
        civ = self.load(VARIANT)
        self.assertEqual(civ["cast"]["actors"], list(base["cast"].get("actors") or []) + [actor])

    def test_a_variant_is_hidden_only_when_it_says_so(self):
        self.add_mod(ACME, civs={VARIANT: {"id": VARIANT, "variant_of": "rome_100ad"}})
        self.assertNotIn("hidden", self.load(VARIANT))
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            self.assertIn(VARIANT, data.civilization_ids())

    def test_a_variant_of_a_missing_civilisation_is_an_error_naming_it(self):
        self.add_mod(ACME, civs={VARIANT: {"id": VARIANT, "variant_of": "nowhere_1ad"}})
        with self.assertRaises(ModError) as caught:
            self.load(VARIANT)
        self.assertIn("nowhere_1ad", str(caught.exception))

    def test_the_start_check_skips_a_variant_whose_base_is_absent_and_still_checks_the_rest(self):
        # a base civilisation file is optional data; a variant of an absent one is unavailable, not a failed game start
        self.add_mod(ACME, civs={VARIANT: {"id": VARIANT, "variant_of": "nowhere_1ad"},
                                 ACME + ":ok": {"id": ACME + ":ok", "variant_of": "rome_100ad"}})
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            check_all_civilizations(data.CIVDIR, data.get_ordered_mods(data.MODDIR))
        self.test_a_variant_of_a_missing_civilisation_is_an_error_naming_it()

    def test_a_variant_of_a_variant_resolves_and_a_cycle_is_an_error(self):
        second = ACME + ":second"
        self.add_mod(ACME, civs={VARIANT: {"id": VARIANT, "variant_of": "rome_100ad", "population": 11},
                                 second: {"id": second, "variant_of": VARIANT, "name": "second"}})
        civ = self.load(second)
        self.assertEqual((civ["population"], civ["name"]), (11, "second"))
        loop_a, loop_b = ACME + ":loop_a", ACME + ":loop_b"
        self.add_mod("test_beta_k3f9", civs={"test_beta_k3f9:loop_a": {"variant_of": "test_beta_k3f9:loop_b"},
                                             "test_beta_k3f9:loop_b": {"variant_of": "test_beta_k3f9:loop_a"}})
        with self.assertRaises(ModError) as caught:
            self.load("test_beta_k3f9:loop_a")
        self.assertIn("loop", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
