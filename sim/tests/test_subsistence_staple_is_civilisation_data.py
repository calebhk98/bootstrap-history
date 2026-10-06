"""Complaints/432: the grain behind the wage floor is the civilisation's own, not wheat for everyone."""
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

    def test_the_floor_follows_the_civilisations_own_staple(self):
        for civilization_id, staple in (("han_china_100ad", "millet_kg"), ("mexica_1500", "maize_kg")):
            civ = data.load_civ(civilization_id)
            normal = _schedule(civ)
            entries = _entries()
            _scaled_labour(entries, staple, 2.0)
            self.assertGreater(_schedule(civ, entries).subsistence_hours_per_hour,
                               normal.subsistence_hours_per_hour, civilization_id)

    def test_the_staple_moves_the_floor_more_than_wheat_does(self):
        civ = data.load_civ("han_china_100ad")
        normal = _schedule(civ).subsistence_hours_per_hour
        wheat_entries, millet_entries = _entries(), _entries()
        _scaled_labour(wheat_entries, "wheat_kg", 2.0)
        _scaled_labour(millet_entries, "millet_kg", 2.0)
        wheat_shift = abs(_schedule(civ, wheat_entries).subsistence_hours_per_hour - normal)
        millet_shift = abs(_schedule(civ, millet_entries).subsistence_hours_per_hour - normal)
        self.assertGreater(millet_shift, wheat_shift)


if __name__ == "__main__":
    unittest.main()
