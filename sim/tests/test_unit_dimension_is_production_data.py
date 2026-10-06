"""Complaints/399: every production entry states what dimension its unit measures, and the validator checks it."""

QUICK_TOPIC = True

import copy
import unittest

from sim.economy import good_mass
from sim.engine import validate_production
from sim.world import demand, good_dimension


class UnitDimension(unittest.TestCase):

    def test_every_entry_states_a_known_dimension_agreeing_with_its_id(self):
        problems = []
        for name, entry in demand.production_data().items():
            problems.extend(validate_production.check_unit_dimension(name, entry))
        self.assertEqual(problems, [])

    def test_the_validator_rejects_missing_unknown_or_contradicting_dimensions(self):
        entry = copy.deepcopy(demand.production_data()["wheat_kg"])
        self.assertEqual(validate_production.check_unit_dimension("wheat_kg", entry), [])
        for bad in (None, "heavy", "volume", "count"):
            if bad is None:
                del entry["unit_dimension"]
            else:
                entry["unit_dimension"] = bad
            self.assertTrue(validate_production.check_unit_dimension("wheat_kg", entry), bad)

    def test_id_tokens_name_a_dimension(self):
        self.assertEqual(good_dimension.dimension_from_id("timber_m3"), "volume")
        self.assertEqual(good_dimension.dimension_from_id("thermal_mj"), "energy")
        self.assertEqual(good_dimension.dimension_from_id("hectare_land"), "area")
        self.assertEqual(good_dimension.dimension_from_id("iron_bar_kg"), "mass")
        self.assertIsNone(good_dimension.dimension_from_id("mule"))

    def test_counted_goods_have_a_stated_mass_not_a_guess(self):
        production = demand.production_data()
        for good in ("papyrus_sheet", "arsenic", "hops", "mat_sugar", "mat_animal_gut", "mat_potash"):
            self.assertEqual(good_mass.unit_mass_and_source(good, production)[1], good_mass.SOURCE_STATED, good)

    def test_energy_and_area_dimensions_cannot_be_carried(self):
        production = demand.production_data()
        for good in ("thermal_mj", "electrical_mj", "mechanical_mj", "hectare_land"):
            self.assertEqual(good_mass.unit_mass_and_source(good, production)[1], good_mass.SOURCE_IMMOBILE, good)


if __name__ == "__main__":
    unittest.main()
