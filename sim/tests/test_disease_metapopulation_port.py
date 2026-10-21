"""The metapopulation wired to the engine's side (Complaint 490), with no game built (`disease_stand_in.StandInSim`): an
endemic start for a civilisation whose childhood diseases are already in its people, an arrival entering at the tile the
routes reach first, deaths by tile, the forecast the risk screens show, and the regional disease loss the cost readers use."""

QUICK_TOPIC = True

import unittest

from sim.disease import api as disease
from sim.engine import disease_port
from sim.tests.disease_stand_in import StandInSim, civilisation


def england():
    return StandInSim(civilisation("england_1300"), 1)


class EndemicStartTest(unittest.TestCase):
    def test_a_civilisation_whose_childhood_diseases_are_endemic_opens_with_the_immune_share_their_numbers_imply(self):
        sim = england()
        sim.disease_year(sim.food, sim.year)
        records = sim.state.disease.records
        self.assertEqual(sorted(records), ["measles", "smallpox"])
        for pathogen_id, tiles in records.items():
            children = sum(counts["recovered"] for bands in tiles.values() for counts in [bands["children"]])
            working_age = sum(counts["recovered"] for bands in tiles.values() for counts in [bands["working_age"]])
            children_total = sum(sum(bands["children"].values()) for bands in tiles.values())
            working_total = sum(sum(bands["working_age"].values()) for bands in tiles.values())
            self.assertLess(children / children_total, working_total and working_age / working_total, pathogen_id)
            self.assertGreater(working_age / working_total, 0.5, pathogen_id)
            self.assertTrue(disease.metapopulation.is_circulating(records, pathogen_id), pathogen_id)

    def test_a_civilisation_that_lists_no_endemic_pathogen_opens_with_every_pathogen_unmet(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        self.assertEqual(disease_port.DiseaseWorld(sim).endemic_pathogens(), ())

    def test_the_endemic_start_keeps_the_people_less_the_years_disease_deaths(self):
        sim = england()
        before = sim.population.total
        sim.disease_year(sim.food, sim.year)
        living = sum(sum(counts.values()) for tiles in sim.state.disease.records.values() for bands in tiles.values()
                     for counts in bands.values())
        self.assertAlmostEqual(living / 2, before, delta=before * 0.02)


class ArrivalTest(unittest.TestCase):
    def test_a_pathogen_enters_at_a_tile_held_and_the_deaths_are_listed_by_tile(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        world = disease_port.DiseaseWorld(sim)
        people = world.people_by_tile()
        entered = world.entry_tiles(["smallpox"], sim.year, people, world.contacts(people))
        self.assertTrue(entered["smallpox"])
        for tile in entered["smallpox"]:
            self.assertGreater(sum(people[tile].values()), 0.0)
        sim.disease_year(sim.food, sim.year)
        introduced_by = disease_port.DiseaseWorld.introductions
        try:
            disease_port.DiseaseWorld.introductions = lambda self, records, year: ["smallpox"] if not records else []
            deaths = {}
            for _ in range(3):
                deaths = sim.disease_year(sim.food, sim.year)
                sim.year += 1
        finally:
            disease_port.DiseaseWorld.introductions = introduced_by
        by_tile = sim.epidemic_deaths_by_tile()
        self.assertEqual(set(by_tile) <= set(people), True)
        self.assertAlmostEqual(sum(sum(bands.values()) for bands in by_tile.values()), sum(deaths.values()))

    def test_every_tile_of_the_nation_has_people_that_sum_to_the_nations(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        people = disease_port.DiseaseWorld(sim).people_by_tile()
        for band in disease_port.BANDS:
            self.assertAlmostEqual(sum(bands[band] for bands in people.values()), getattr(sim.population, band), delta=1.0)


class ForecastTest(unittest.TestCase):
    def test_with_nothing_under_way_the_forecast_expects_no_deaths_and_names_the_chances_of_arrival(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        forecast = sim.epidemic_forecast()
        self.assertEqual(forecast["expected_deaths"], 0)
        self.assertEqual(forecast["by_pathogen"], [])
        self.assertTrue(forecast["arrival_chances"])
        self.assertTrue(all(0.0 <= chance <= 1.0 for chance in forecast["arrival_chances"].values()))

    def test_with_a_pathogen_under_way_the_forecast_expects_deaths_from_it_and_the_next_year_draws_near_it(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        introduced_by = disease_port.DiseaseWorld.introductions
        try:
            disease_port.DiseaseWorld.introductions = lambda self, records, year: ["smallpox"] if not records else []
            sim.disease_year(sim.food, sim.year)
        finally:
            disease_port.DiseaseWorld.introductions = introduced_by
        sim.year += 1
        forecast = sim.epidemic_forecast()
        self.assertEqual([row["pathogen"] for row in forecast["by_pathogen"]], ["smallpox"])
        self.assertGreater(forecast["expected_deaths"], 0)
        self.assertGreater(forecast["expected_working_age_share"], 0.0)
        self.assertIs(sim.epidemic_forecast(), forecast)
        drawn = sum(sim.disease_year(sim.food, sim.year).values())
        self.assertGreater(drawn, 0.2 * forecast["expected_deaths"])
        self.assertLess(drawn, 5.0 * forecast["expected_deaths"])

    def test_no_forecast_text_names_a_dated_plague(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        self.assertNotIn("years", sim.epidemic_forecast())


class RegionalLossTest(unittest.TestCase):
    def test_a_tile_whose_epidemic_is_forecast_to_take_people_loses_more_than_its_endemic_rate_alone(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        tile = sorted(disease_port.DiseaseWorld(sim).people_by_tile())[0]
        quiet = sim.regional_disease_loss(tile)
        sim.__dict__["_epidemic_forecast"] = {
            "expected_deaths": 5000, "expected_working_age_share": 0.01, "by_pathogen": [],
            "expected_deaths_by_tile": {tile: {"working_age": 0.5 * disease_port.DiseaseWorld(sim).people_by_tile()[tile]["working_age"]}},
            "arrival_chances": {}}
        self.assertAlmostEqual(sim.regional_disease_loss(tile) - quiet, 0.5, places=6)

    def test_a_tile_that_is_not_held_takes_the_nations_forecast_share(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        sim.__dict__["_epidemic_forecast"] = {"expected_deaths": 1, "expected_working_age_share": 0.25, "by_pathogen": [],
                                              "expected_deaths_by_tile": {}, "arrival_chances": {}}
        held = set(disease_port.DiseaseWorld(sim).held_tiles())
        outside = next(tile for tile in sim.world_map.tiles if tile not in held)
        self.assertGreaterEqual(sim.regional_disease_loss(outside), 0.25)

    def test_the_frontier_loss_is_the_mean_over_the_tiles_that_border_a_tile_not_held(self):
        sim = StandInSim(civilisation("rome_100ad"), 1)
        sim.__dict__["_epidemic_forecast"] = {"expected_deaths": 0, "expected_working_age_share": 0.0, "by_pathogen": [],
                                              "expected_deaths_by_tile": {}, "arrival_chances": {}}
        self.assertGreaterEqual(sim.frontier_disease_loss(), 0.0)
        self.assertLess(sim.frontier_disease_loss(), 1.0)


if __name__ == "__main__":
    unittest.main()
