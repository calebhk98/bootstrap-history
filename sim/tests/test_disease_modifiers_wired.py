"""The care-collapse and density modifiers reach the nation's yearly disease step (Complaint 471), on the stand-in sim
(`disease_stand_in.StandInSim`, no game). The rules inside the model are in test_disease_wiring (`CareCollapseAndDensityTest`);
these two check the port hands the tuned constants to them, and that the immunity a first wave leaves is still in the nation's records for a second. The sourced-band check is a measurement, not a test: Complaints/closed/386 gives the command."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.disease import api as disease
from sim.disease.module import Disease
from sim.tests.disease_stand_in import StandInSim, mexica_with_source

YEARS = 3
SECOND_ARRIVAL_AFTER_YEARS = 5
SEEDS_USED = (1,)


def deaths_with(seed, care_sensitivity):
    """Deaths from a smallpox arrival in the first year, over YEARS years, with the port's care-collapse sensitivity replaced."""
    sim = StandInSim(mexica_with_source(["sail"]), seed)
    first_year = sim.year
    with mock.patch.object(disease.nation_tuning, "DISEASE_CARE_COLLAPSE_SENSITIVITY", care_sensitivity), mock.patch.object(
            Disease, "introductions", lambda module, records, year: ["smallpox"] if year == first_year else []):
        rows = sim.run(YEARS)
    return sum(deaths for _year, _people, deaths in rows)


class ModifiersReachTheNationsYearTest(unittest.TestCase):
    def test_care_collapse_raises_the_deaths_of_the_same_arrival(self):
        for seed in SEEDS_USED:
            without = deaths_with(seed, 0.0)
            with_collapse = deaths_with(seed, disease.nation_tuning.DISEASE_CARE_COLLAPSE_SENSITIVITY)
            self.assertGreater(disease.nation_tuning.DISEASE_CARE_COLLAPSE_SENSITIVITY, 0.0)
            self.assertGreater(without, 0.0, "seed %d" % seed)
            self.assertGreater(with_collapse, without, "seed %d" % seed)

    def test_the_urban_density_ratio_raises_the_crowding_of_every_populated_tile(self):
        sim = StandInSim(mexica_with_source(["sail"]), 1)
        world = sim.module
        people = world.people_by_tile()
        with mock.patch.object(disease.nation_tuning, "DISEASE_URBAN_DENSITY_RATIO", 1.0):
            rural = world.crowding_by_tile(people)
        crowded = world.crowding_by_tile(people)
        self.assertGreater(sim.urban_fraction(), 0.0)
        self.assertTrue(rural)
        for tile, rural_crowding in rural.items():
            self.assertGreater(crowded[tile], rural_crowding, tile)


class ImmunityCarriesBetweenYearsTest(unittest.TestCase):
    def test_the_same_pathogen_arriving_again_kills_far_fewer_people_than_it_did_the_first_time(self):
        sim = StandInSim(mexica_with_source(["sail"]), 1)
        first_year = sim.year
        arrivals = (first_year, first_year + SECOND_ARRIVAL_AFTER_YEARS)
        with mock.patch.object(Disease, "introductions",
                               lambda module, records, year: ["smallpox"] if year in arrivals else []):
            rows = sim.run(SECOND_ARRIVAL_AFTER_YEARS + YEARS)
        deaths = [row[2] for row in rows]
        first_wave, second_wave = sum(deaths[:YEARS]), sum(deaths[SECOND_ARRIVAL_AFTER_YEARS:])
        self.assertEqual(sim.module.world.introduced["smallpox"], list(arrivals))
        self.assertGreater(first_wave, 0.0)
        self.assertLess(second_wave, 0.5 * first_wave)


if __name__ == "__main__":
    unittest.main()
