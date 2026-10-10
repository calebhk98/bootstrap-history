"""Labour hours per kilogram of silver, measured from the recipe data without
building a game (Complaints/349): the direct silver route is its ore's mining
hours plus dressing, divided by the silver the ore holds, so hours vary as one
over the grade; the figure is a relationship to the data, not a target."""

QUICK_TOPIC = True

import unittest

from sim.engine.prices import _default_production_entries
from sim.world import deposits, ore_dressing
from sim.unit_conversions import KILOGRAMS_PER_TONNE


def direct_route_hours_per_kilogram_of_silver():
    """Labourer-hours (every trade counted as an hour) per kilogram of silver
    on the amalgamation route: the ore's mining, then dressing and furnace
    hours, read from the recipe entries."""
    entries = _default_production_entries()
    silver = entries["silver_kg"]
    ore = entries["silver_ore_kg"]
    ore_tonnes = silver["inputs"]["silver_ore_kg"] / KILOGRAMS_PER_TONNE
    mining = ore_tonnes * sum(ore["labour_hours"].values())
    own = sum(silver["labour_hours"].values())
    return (mining + own) / silver["outputs"]["silver_kg"]


def chain_hours_per_kilogram_at_grade(deposit, grade_kg_per_tonne):
    """Mining plus dressing hours per kilogram of silver in the ore of a
    deposit at a stated grade."""
    per_tonne = (deposits.vein_hours_per_tonne_ore(deposit)
                 + ore_dressing.dressing_hours_per_tonne_rock())
    return per_tonne / grade_kg_per_tonne


class SilverHoursPerKilogram(unittest.TestCase):

    def test_hours_vary_as_one_over_the_grade(self):
        for deposit in deposits.load_deposits("silver"):
            if deposit.depth_class in ("alluvial", "alluvial_hydraulic"):
                continue
            grade = deposit.ore_grade_kg_per_tonne
            self.assertAlmostEqual(
                chain_hours_per_kilogram_at_grade(deposit, grade)
                / chain_hours_per_kilogram_at_grade(deposit, 2.0 * grade), 2.0,
                places=9, msg=deposit.name)
            self.assertAlmostEqual(
                deposits.extraction_cost_labour_hours_per_kg(deposit)
                * grade, deposits.vein_hours_per_tonne_ore(deposit), places=6)

    def test_recipe_hours_are_the_deposits_mining_plus_dressing_over_the_ore_grade(self):
        pool = [d for d in deposits.load_deposits("silver") if d.ore_type == "primary"]
        total = sum(d.quantity_tonnes_per_year for d in pool)
        entries = _default_production_entries()
        ore_tonnes_per_kilogram = (
            entries["silver_kg"]["inputs"]["silver_ore_kg"]
            / entries["silver_kg"]["outputs"]["silver_kg"] / KILOGRAMS_PER_TONNE)
        mining_per_tonne = sum(
            d.quantity_tonnes_per_year / total * deposits.vein_hours_per_tonne_ore(d)
            for d in pool)
        expected = ((mining_per_tonne + ore_dressing.dressing_hours_per_tonne_rock())
                    * ore_tonnes_per_kilogram)
        self.assertAlmostEqual(
            direct_route_hours_per_kilogram_of_silver() / expected, 1.0, delta=0.03)

    def test_a_poorer_ore_costs_more_hours_per_kilogram_on_the_jarosite_route(self):
        entry = _default_production_entries()["silver_jarosite_kg"]
        deposit = next(d for d in deposits.load_deposits("silver")
                       if d.name == "rio_tinto_jarosite")
        ore_tonnes_per_kilogram = (entry["inputs"]["jarosite_ore_kg"]
                                   / entry["outputs"]["silver_kg"] / KILOGRAMS_PER_TONNE)
        # The route's ore per kilogram of silver is one over grade times the
        # collector's silver recovery (0.80) and the cupellation recovery (0.92).
        self.assertAlmostEqual(
            ore_tonnes_per_kilogram * deposit.ore_grade_kg_per_tonne * 0.80 * 0.92, 1.0, delta=0.01)
        self.assertAlmostEqual(
            entry["labour_hours"]["labourer"] / (entry["inputs"]["jarosite_ore_kg"] / 1000.0),
            ore_dressing.dressing_hours_per_tonne_rock(), delta=0.5)

    def test_dressing_hours_follow_the_attested_processing_staff(self):
        # Fewer processing workers for the same ore means fewer hours per tonne.
        base = ore_dressing.processing_worker_days_per_tonne_ore()
        self.assertAlmostEqual(
            base, ore_dressing.MELLE_PROCESSING_WORKERS
            * ore_dressing.MELLE_WORKING_DAYS_PER_YEAR
            / ore_dressing.MELLE_ORE_TONNES_PER_YEAR)
        self.assertGreater(ore_dressing.dressing_hours_per_tonne_rock(), 0.0)


if __name__ == "__main__":
    unittest.main()
