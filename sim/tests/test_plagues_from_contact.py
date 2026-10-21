"""Plagues come from the disease model, not from a dated hazard table (Complaint 490).

No game is built (`disease_stand_in.StandInSim`). The rules here: a civilisation with no contact to a pathogen's source never
gets it, contact weight follows the routes a carrier mode opens and falls with distance, the deaths handed to the population
are the model's own count, and no civilisation file carries a dated plague. The ensemble gates (Rome's epidemics are drawn,
not dated; ships bring the pathogen in every run) are test_plagues_from_contact_validation; the founder's staff losing the
working-age share is test_plagues_from_contact_scenario.
"""

QUICK_TOPIC = True

import os
import unittest
from unittest import mock

from sim.engine import disease_port
from sim.tests.disease_stand_in import ROOT, SEEDS, StandInSim, civilisation, mexica_with_source, world_map

PLAGUE_HAZARD_NAMES = ("Antonine plague", "Plague of Cyprian", "The Justinianic plague", "Recurrent plague", "Black Death",
                       "Black Death in Scandinavia", "The Great Plague of London", "The matlazahuatl of 1736")


def source_of(carrier_modes):
    return mexica_with_source(carrier_modes)["disease_exposure"]["outside_contact"][0]


def weight(sim, source):
    return disease_port.DiseaseWorld(sim).contact_weight(
        dict(source, tiles=tuple(source["tiles"]), pathogens=tuple(source["pathogens"]),
             carrier_modes=tuple(source["carrier_modes"]), first_year=None, last_year=None))


class NoContactTest(unittest.TestCase):
    def test_a_source_no_route_joins_to_the_nation_never_gives_it_a_pathogen(self):
        for seed in SEEDS:
            sim = StandInSim(mexica_with_source([]), seed)
            sim.run(400)
            self.assertEqual(sim.state.disease.introduced, {}, "seed %d" % seed)
            self.assertEqual(sim.state.disease.deaths, {}, "seed %d" % seed)

    def test_the_same_source_has_no_weight_without_a_carrier_and_some_with_ships(self):
        sim = StandInSim(mexica_with_source([]), 1)
        self.assertEqual(weight(sim, source_of([])), 0.0)
        self.assertGreater(weight(sim, source_of(["sail"])), 0.0)

    def test_a_source_closer_by_route_gives_more_arrivals_than_a_far_one(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        near = {"tiles": ("iran_01",), "carrier_modes": (), "circulating": False, "first_year": None, "last_year": None,
                "pathogens": ("smallpox",)}
        far = dict(near, tiles=("china_60",))
        self.assertGreater(disease_port.DiseaseWorld(sim).contact_weight(near), disease_port.DiseaseWorld(sim).contact_weight(far))


class DeathsComeFromTheModelTest(unittest.TestCase):
    def test_the_deaths_handed_to_population_are_the_models_own_count(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        pathogen_id = sorted(civilisation("rome_100ad")["disease_exposure"]["outside_contact"][0]["pathogens"])[0]
        handed, sim_start = 0, sim.year
        # The epidemic arrives in the first year, so a few years show the hand-off without waiting for a draw.
        with mock.patch.object(disease_port.DiseaseWorld, "introductions",
                               lambda world, records, year: [pathogen_id] if year == sim_start else []):
            for _ in range(5):
                handed += sum(sim.disease_year(sim.food, sim.year).values())
                sim.year += 1
        self.assertGreater(handed, 0)
        self.assertEqual(handed, sum(sim.state.disease.deaths.values()))

    def test_no_civilisation_file_carries_a_dated_plague(self):
        directory = os.path.join(ROOT, "data", "civilizations")
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json") or name.startswith("_"):
                continue
            hazard_names = {hazard["name"] for hazard in civilisation(name[:-5]).get("hazards", [])}
            self.assertFalse(hazard_names & set(PLAGUE_HAZARD_NAMES), name)

    def test_every_civilisation_states_where_its_pathogens_live_not_when_they_come(self):
        for civ_id in ("rome_100ad", "england_1300", "norse_900ad", "han_china_100ad", "mexica_1500"):
            sources = civilisation(civ_id)["disease_exposure"]["outside_contact"]
            self.assertTrue(sources, civ_id)
            for source in sources:
                self.assertTrue(source["tiles"], civ_id)
                self.assertTrue(set(source["tiles"]) <= set(world_map().tiles), civ_id)


if __name__ == "__main__":
    unittest.main()
