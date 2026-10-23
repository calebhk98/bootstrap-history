"""Complaints 607 and 558: the opening's income is a steady state, so what households own of the firms is not
demand the opening settles on. A household may spend wealth above what it wants to keep, but only until that
wealth is spent; counted in the opening's fixed point it lifts every year's demand, so the settled income rose to
the full-employment ceiling on Rome (and, with it, the opening wages of the thin skilled trades several-fold).

Re-measure on Rome: `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 6` (the labourer's wage and the
hired share of offered hours by year)."""
import dataclasses
import unittest

from sim.economy import opening
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = True

# plant dear enough that the firms are worth many years of the households' income
PLANT_METAL_FARM = 80.0
PLANT_METAL_MINE = 20.0


def heavy_plant_setup():
    base = fixture.small_setup()
    recipes = dict(base.recipes)
    for recipe_id, metal, trade, hours in ((fixture.FARM, PLANT_METAL_FARM, fixture.LABOURER, 4000.0),
                                           (fixture.MINE, PLANT_METAL_MINE, fixture.MINER, 2000.0)):
        recipes[recipe_id] = dataclasses.replace(
            recipes[recipe_id], plant_goods={fixture.METAL: metal}, plant_labour_hours={trade: hours},
            plant_life_years=20.0)
    return dataclasses.replace(base, recipes=recipes)


class OpeningIncomeTests(unittest.TestCase):
    def test_the_opening_income_does_not_rise_to_the_ceiling_on_what_households_own_of_the_firms(self):
        setup = heavy_plant_setup()
        record, _area_map, _carriage = opening.open_economy(setup)
        people = sum(cohort.people for cohort in record.cohorts.values())
        income = sum(cohort.last_year_income for cohort in record.cohorts.values()) / people
        self.assertLess(income, 0.5 * opening._full_employment_income_per_head(setup))


if __name__ == "__main__":
    unittest.main()
