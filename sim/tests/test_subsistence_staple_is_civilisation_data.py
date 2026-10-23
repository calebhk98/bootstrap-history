"""Complaints/432: the grain behind the wage floor is the civilisation's own, not wheat for everyone."""

QUICK_TOPIC = True

import copy
import unittest

from sim.default_civilisation import REPOSITORY_ROOT
from sim.engine import catalog, data, wage_schedule
from sim.engine.validate_production import load_production
from sim.labour import wage_provider


def _schedule(civ, entries=None):
    return wage_schedule.build_schedule(
        catalog.load_trade_registry(REPOSITORY_ROOT), civ, production_entries=entries)


def _entries():
    entries, _duplicates = load_production()
    return copy.deepcopy(entries)


def _scaled_labour(entries, material, factor):
    entries[material]["labour_hours"] = {
        trade: hours * factor for trade, hours in entries[material]["labour_hours"].items()}


class StapleIsData(unittest.TestCase):

    def test_staple_is_read_from_the_civilisation_and_defaults_to_wheat(self):
        self.assertEqual(wage_provider.staple_material(data.load_civ("rome_100ad")), "wheat_kg")
        self.assertEqual(wage_provider.staple_material(data.load_civ("han_china_100ad")), "millet_kg")
        self.assertEqual(wage_provider.staple_material(data.load_civ("mexica_1500")), "maize_kg")
        self.assertEqual(wage_provider.staple_material({"id": "mod"}), "wheat_kg")

    def test_a_staple_that_is_not_a_good_is_rejected(self):
        with self.assertRaises(ValueError):
            wage_provider.staple_material({"id": "mod", "staple": ""})

    def test_the_floor_follows_a_non_wheat_civilisations_staple(self):
        civ = data.load_civ("mexica_1500")
        normal = _schedule(civ)
        entries = _entries()
        _scaled_labour(entries, "maize_kg", 2.0)
        self.assertGreater(_schedule(civ, entries).subsistence_hours_per_hour, normal.subsistence_hours_per_hour)

    def test_the_floor_reads_the_named_staple_and_not_another_grain(self):
        # Land rent is stated in wheat (the solver's rent unit), so every grain's cost moves with wheat's labour; the
        # floor of a wheat-staple civilisation must move with wheat's labour by more than a millet-staple one's does,
        # and a grain that is not the staple (millet, for a wheat civilisation) must not move it at all.
        def floor_shift(staple, grain):
            civ = dict(data.load_civ("han_china_100ad"), staple=staple)
            normal = _schedule(civ).subsistence_hours_per_hour
            entries = _entries()
            _scaled_labour(entries, grain, 2.0)
            return _schedule(civ, entries).subsistence_hours_per_hour - normal
        self.assertGreater(floor_shift("millet_kg", "millet_kg"), 0.0)
        self.assertAlmostEqual(floor_shift("wheat_kg", "millet_kg"), 0.0, places=9)
        self.assertGreater(floor_shift("wheat_kg", "wheat_kg"), floor_shift("millet_kg", "wheat_kg"))


if __name__ == "__main__":
    unittest.main()
