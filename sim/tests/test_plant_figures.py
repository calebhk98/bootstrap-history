"""The plant kernel (sim/world/plant_figures.py): relationships between a plant's figures, from a hand-made entry.

Stage 2 of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md. No node dict, no engine and no money field is read.
"""

QUICK_TOPIC = True

import unittest

from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.world import plant_figures


class NoEnergy:
    def can_run(self, entry):
        return True

    def bought(self, carrier, entry):
        return 0.0

    def sold(self, carrier, entry):
        return 0.0


def entry(capacity=None, hours=10.0):
    capital = [{"good": "kiln", "annual_output_at_basis": capacity, "service_life_years": 10.0,
                "build_materials": {"brick": 100.0}, "build_labour_hours": {"mason": 50.0}}] if capacity else []
    return {"outputs": {"lime": 100.0}, "inputs": {"limestone": 150.0}, "labour_hours": {"burner": hours},
            "capital": capital}


GOODS = {"lime": 3.0, "limestone": 1.0, "brick": 2.0}
WAGES = {"burner": 1.0, "mason": 1.5}


def baskets(plant_entry, staff_people=0.0, declared_output_t=0.0):
    return plant_figures.yearly_baskets([plant_entry], GOODS, NoEnergy(), None, staff_people, declared_output_t)


class PlantFiguresTest(unittest.TestCase):
    def test_output_is_the_smaller_of_plant_capacity_and_what_the_crew_can_work(self):
        crew_hours = 2.0 * HOURS_PER_PERSON_YEAR
        by_crew = baskets(entry(capacity=1e9), staff_people=2.0)
        self.assertAlmostEqual(by_crew.outputs["lime"], crew_hours / 10.0 * 100.0)
        by_plant = baskets(entry(capacity=500.0), staff_people=2.0)
        self.assertAlmostEqual(by_plant.outputs["lime"], 500.0)

    def test_crew_hours_scale_with_output(self):
        small = baskets(entry(capacity=500.0))
        large = baskets(entry(capacity=1000.0))
        self.assertAlmostEqual(large.labour_hours["burner"], 2.0 * small.labour_hours["burner"])
        self.assertAlmostEqual(plant_figures.derived_crew_hours("output", large.labour_hours),
                               2.0 * plant_figures.derived_crew_hours("output", small.labour_hours))
        self.assertEqual(plant_figures.derived_crew_hours("authored", large.labour_hours), 0.0)

    def test_crew_is_hours_over_a_person_year_else_stated_else_fallback(self):
        self.assertAlmostEqual(plant_figures.crew_people(HOURS_PER_PERSON_YEAR * 3.0, HOURS_PER_PERSON_YEAR, 9.0, 7.0), 3.0)
        self.assertEqual(plant_figures.crew_people(0.0, HOURS_PER_PERSON_YEAR, 9.0, 7.0), 9.0)
        self.assertEqual(plant_figures.crew_people(0.0, HOURS_PER_PERSON_YEAR, None, 7.0), 7.0)
        self.assertTrue(plant_figures.crew_is_fallback(0.0, None))
        self.assertFalse(plant_figures.crew_is_fallback(0.0, 9.0))

    def test_upkeep_rises_with_plant_capital_and_is_consumables_alone_with_none(self):
        with_plant = plant_figures.upkeep_parts("ENGINEERING", baskets(entry(capacity=500.0)), GOODS, WAGES, 1.0)
        without = plant_figures.upkeep_parts("ENGINEERING", baskets(entry(capacity=None), staff_people=1.0),
                                             GOODS, WAGES, 1.0)
        self.assertGreater(with_plant["plant"], 0.0)
        self.assertEqual(without["plant"], 0.0)
        self.assertEqual(without["plant_build_hours"], 0.0)
        pricier = dict(GOODS, brick=4.0)
        dearer = plant_figures.upkeep_parts("ENGINEERING", baskets(entry(capacity=500.0)), pricier, WAGES, 1.0)
        self.assertGreater(dearer["plant_build_hours"], with_plant["plant_build_hours"])

    def test_maintenance_never_exceeds_the_wear(self):
        self.assertEqual(plant_figures.maintenance_hours("ENGINEERING", 1000.0, 1.0), 1.0)

    def test_takings_are_linear_in_the_price_of_what_it_sells(self):
        plant = baskets(entry(capacity=500.0))
        base = plant_figures.takings(plant, GOODS)
        raised = plant_figures.takings(plant, dict(GOODS, lime=GOODS["lime"] + 1.0))
        raised_twice = plant_figures.takings(plant, dict(GOODS, lime=GOODS["lime"] + 2.0))
        self.assertAlmostEqual(raised_twice - raised, raised - base)
        self.assertGreater(raised, base)
        self.assertEqual(plant_figures.takings(plant, dict(GOODS, lime=0.0)), 0.0)

    def test_non_labour_share_follows_the_stated_parts(self):
        self.assertAlmostEqual(plant_figures.non_labour_share({"staff": 3.0, "plant": 1.0}, "derived"), 0.25)
        self.assertEqual(plant_figures.non_labour_share(None, "staff"), 0.0)
        self.assertEqual(plant_figures.non_labour_share(None, "authored"), 1.0)

    def test_ramp_rises_with_age_and_shortens_with_depth(self):
        self.assertAlmostEqual(plant_figures.ramp(0, 4.0), 0.25)
        self.assertEqual(plant_figures.ramp(10, 4.0), 1.0)
        self.assertGreater(plant_figures.ramp(0, 4.0, 1.0, 0.5), plant_figures.ramp(0, 4.0, 0.0, 0.5))


if __name__ == "__main__":
    unittest.main()
