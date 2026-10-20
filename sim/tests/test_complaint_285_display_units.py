"""Complaint 285: the player's chosen display units reach every quantity of a reply.

A fake unit is registered per dimension (the stakeholder's `blob` for area), selected, and `add_display` is called on
replies built here: every quantity of the dimension carries the fake unit, the number is the base value converted (so
not equal to it), and the base field is never changed. The same run is repeated with a mod supplying the fake units.
The default (nothing selected) leaves every reply untouched. (The covered screens of a played game:
test_scenario_display_units.)"""
QUICK_TOPIC = True

import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from sim.engine import units as U
from sim.tests.harness import ROOT
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.util import _coin_hoard_line
from sim.ui.units_text import for_text

FAKE = {"area": "blob_area", "mass": "blob_mass", "money": "blob_money", "temperature": "blob_degree"}
FAKE_UNITS = {
    "blob_area": {"name": "blob", "symbol": "blob", "dimension": "area", "factor": 0.15},
    "blob_mass": {"name": "blob", "symbol": "blob", "dimension": "mass", "factor": 7.0},
    "blob_money": {"name": "blob", "symbol": "blob", "dimension": "money", "factor": 3.0},
    "blob_degree": {"name": "blob", "symbol": "blob", "dimension": "temperature", "factor": 2.0, "offset": 10.0},
}
# a field of each dimension, its value in the field's native unit, and what the native unit is worth in base units
FIELDS = {"area": ("hectares", 5.0, "hectare"), "mass": ("needed_tonnes", 14.0, "tonne"),
          "money": ("capital", 1200.0, "civ_coin"), "temperature": ("furnace_celsius", 100.0, "celsius")}
HOURS_PER_COIN = 2.0
GAME = SimpleNamespace(civ={"id": "rome_100ad"}, labour=SimpleNamespace(money_per_labour_hour=lambda: 1.0 / HOURS_PER_COIN))
# Mass quantities in tonnes: 14 t is 2 blob (7 kg each); the number printed is the converted one.
HAND_REPLIES = [
    ("why", {"ok": True, "id": "x", "name": "x", "material_rows": [
        {"material": "iron", "needed_tonnes": 14.0, "held_tonnes": 7.0,
         "missing_tonnes": 7.0, "cost_of_missing": 1.0}]}, "need 2,000"),
]


def registry_with(fake_units):
    registry = json.loads(json.dumps(U.load_units(ROOT)))
    registry["units"].update(fake_units)
    return registry


def reply_of(dimension):
    field, value, _native = FIELDS[dimension]
    return {"ok": True, field: value, "nested": {"rows": [{field: value}]}}


def expected_shown(registry, dimension, fake_id, fake_units):
    field, value, native = FIELDS[dimension]
    spec = fake_units[fake_id]
    base = value * U.native_factor(registry, {"native": native}, GAME)
    if dimension == "temperature":
        base = value
    return (base - spec.get("offset", 0.0)) / spec["factor"]


class DisplayRegistry(unittest.TestCase):
    """Runs each test with the shipped registry plus fake units, and puts the globals back after."""
    fake_ids, fake_units = FAKE, FAKE_UNITS

    def setUp(self):
        self.registry = registry_with(self.fake_units)
        U.set_registry(self.registry)
        U.set_preferences({})
        self.addCleanup(U.set_registry, None)
        self.addCleanup(U.set_preferences, {})

    def shown(self, dimension):
        U.set_preferences({dimension: self.fake_ids[dimension]})
        return U.add_display(reply_of(dimension), GAME)


class ConversionTests(DisplayRegistry):
    def test_a_quantity_of_each_dimension_carries_the_chosen_unit(self):
        for dimension in FIELDS:
            field = FIELDS[dimension][0]
            display = self.shown(dimension)[field + "_display"]
            self.assertEqual((display["unit"], display["symbol"]), ("blob", "blob"), dimension)

    def test_the_number_is_the_base_value_converted_not_the_native_value(self):
        for dimension in FIELDS:
            field, value, _native = FIELDS[dimension]
            display = self.shown(dimension)[field + "_display"]
            expected = expected_shown(self.registry, dimension, self.fake_ids[dimension], self.fake_units)
            self.assertAlmostEqual(display["value"], expected, delta=0.011 * max(1.0, abs(expected)), msg=dimension)
            self.assertNotEqual(display["value"], value, dimension)

    def test_the_base_field_itself_is_never_changed(self):
        for dimension in FIELDS:
            field, value, _native = FIELDS[dimension]
            self.assertEqual(self.shown(dimension)[field], value, dimension)

    def test_a_quantity_inside_a_nested_row_is_converted_too(self):
        for dimension in FIELDS:
            field = FIELDS[dimension][0]
            self.assertIn(field + "_display", self.shown(dimension)["nested"]["rows"][0], dimension)

    def test_a_dimension_with_no_chosen_unit_is_left_as_written(self):
        U.set_preferences({"area": FAKE["area"]})
        reply = U.add_display(reply_of("mass"), GAME)
        self.assertNotIn("_display", json.dumps(reply))

    def test_a_number_that_is_not_a_quantity_gets_no_display(self):
        U.set_preferences(FAKE)
        reply = U.add_display({"ok": True, "year": 100, "count": 4}, GAME)
        self.assertEqual(reply, {"ok": True, "year": 100, "count": 4})

    def test_temperature_converts_with_its_offset(self):
        U.set_preferences({"temperature": FAKE["temperature"]})
        shown = U.add_display({"ok": True, "furnace_celsius": 100.0}, None)["furnace_celsius_display"]
        self.assertEqual(shown["unit"], "blob")
        self.assertAlmostEqual(shown["value"], 45.0, places=2)

    def test_the_default_preference_leaves_every_reply_untouched(self):
        for dimension in FIELDS:
            reply = reply_of(dimension)
            self.assertEqual(U.add_display(reply, GAME), reply)
            self.assertNotIn("_display", json.dumps(U.add_display(reply, GAME)))


class TextTests(DisplayRegistry):
    def test_a_hand_written_reply_prints_its_mass_in_the_chosen_unit_and_converts_the_number(self):
        # presentation: the screen prints blob, not tonnes
        U.set_preferences({"mass": FAKE["mass"]})
        for name, reply, expect in HAND_REPLIES:
            text = render_pretty(name, U.add_display(json.loads(json.dumps(reply)), None))
            self.assertIn("blob", text)
            self.assertIn(expect, text)
            self.assertNotRegex(text, r"\btonnes?\b")

    def test_the_coin_hoard_line_is_labelled_in_the_chosen_unit(self):
        # presentation: the line's unit
        U.set_preferences({"mass": FAKE["mass"]})
        hoard = U.add_display({"coin_hoard": {"metal": "silver_kg", "tonnes": 14.0, "keeping_cost_per_year": 1.0}}, None)
        text = "\n".join(_coin_hoard_line(for_text(hoard, False)))
        self.assertTrue("2000 blob of silver" in text or "2,000 blob of silver" in text, text)


class ModUnitsTests(unittest.TestCase):
    """The same conversions with a real mod directory supplying the fake units."""

    def setUp(self):
        self.addCleanup(U.set_registry, None)
        self.addCleanup(U.set_preferences, {})
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.mod = os.path.join(self.directory.name, "mods", "test_blobs_k3f9")
        os.makedirs(os.path.join(self.mod, "data", "world"))
        with open(os.path.join(self.mod, "mod.json"), "w") as handle:
            json.dump({"id": "test_blobs_k3f9", "name": "Blobs", "version": "1", "dependencies": [], "conflicts": []}, handle)

    def write_units(self, units):
        with open(os.path.join(self.mod, "data", "world", "units.json"), "w") as handle:
            json.dump({"units": units}, handle)

    @property
    def mods_directory(self):
        return os.path.join(self.directory.name, "mods")

    def test_a_mod_supplies_units_the_display_uses(self):
        ids = {dimension: "test_blobs_k3f9:" + name[len("blob_"):] for dimension, name in FAKE.items()}
        specs = {"test_blobs_k3f9:" + name[len("blob_"):]: dict(spec) for name, spec in FAKE_UNITS.items()}
        self.write_units(specs)
        registry = U.load_units(ROOT, self.mods_directory)
        U.set_registry(registry)
        for dimension in FIELDS:
            field, _value, _native = FIELDS[dimension]
            U.set_preferences({dimension: ids[dimension]})
            display = U.add_display(reply_of(dimension), GAME)[field + "_display"]
            expected = expected_shown(registry, dimension, ids[dimension], specs)
            self.assertEqual(display["unit"], "blob", dimension)
            self.assertAlmostEqual(display["value"], expected, delta=0.011 * max(1.0, abs(expected)), msg=dimension)

    def test_a_mod_unit_not_namespaced_to_the_mod_is_refused(self):
        self.write_units({"stray": dict(FAKE_UNITS["blob_area"])})
        with self.assertRaises(Exception) as caught:
            U.load_units(ROOT, self.mods_directory)
        self.assertIn("stray", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
