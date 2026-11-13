"""Complaint 550: the workshops a producer stands for follow from its runs and the recipe's plant, and the pricing reads the count."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import seller_offers, workshop_count
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.economy.types import Offer, PlantBuild, PlantPart, Recipe

BUILD = (PlantBuild({}, {}, 20.0),)


def part(runs_per_year):
    return PlantPart(runs_per_year, BUILD)


class WorkshopsForRunsTests(unittest.TestCase):
    def test_runs_of_forty_plants_count_forty_workshops(self):
        self.assertEqual(workshop_count.workshops_for_runs(1600.0, (part(40.0),)), 40)

    def test_the_smallest_part_bounds_a_workshop(self):
        self.assertEqual(workshop_count.workshops_for_runs(300.0, (part(100.0), part(30.0))), 10)

    def test_rounds_to_whole_workshops_and_keeps_at_least_one(self):
        self.assertEqual(workshop_count.workshops_for_runs(1.0, (part(40.0),)), 1)
        self.assertEqual(workshop_count.workshops_for_runs(100.0, (part(40.0),)), 3)
        self.assertEqual(workshop_count.workshops_for_runs(0.0, (part(40.0),)), 1)

    def test_no_plant_counts_one_workshop(self):
        self.assertEqual(workshop_count.workshops_for_runs(5000.0, ()), 1)


class LandRunsPerWorkshopTests(unittest.TestCase):
    def test_a_farm_workshop_is_one_household_holding(self):
        # holding 4 ha, a run takes 0.5 hectare-years: 8 runs fill a holding
        self.assertEqual(workshop_count.land_runs_per_workshop("arable land", 100.0, 0.5, 4.0, 2000.0), 8.0)

    def test_a_herd_workshop_is_one_herders_working_year(self):
        # a run takes 500 herder hours of a 2000 hour year: four runs are one herder's charge
        self.assertEqual(workshop_count.land_runs_per_workshop("pasture", 500.0, 66.0, 4.0, 2000.0), 4.0)

    def test_other_ground_and_deposits_have_no_unit(self):
        self.assertIsNone(workshop_count.land_runs_per_workshop("forest", 500.0, 66.0, 4.0, 2000.0))
        self.assertIsNone(workshop_count.land_runs_per_workshop("", 500.0, 0.0, 4.0, 2000.0))

    def test_no_land_or_no_hours_gives_no_unit(self):
        self.assertIsNone(workshop_count.land_runs_per_workshop("arable land", 100.0, 0.0, 4.0, 2000.0))
        self.assertIsNone(workshop_count.land_runs_per_workshop("pasture", 0.0, 66.0, 4.0, 2000.0))

    def test_the_table_takes_plant_recipes_by_plant_and_plantless_land_recipes_by_land(self):
        recipes = {"oven": Recipe("oven", {"x": 1.0}, {}, {}, plant_parts=(part(40.0),)),
                   "field": Recipe("field", {"x": 1.0}, {}, {"farmer": 100.0}, ground="arable land"),
                   "mine": Recipe("mine", {"x": 1.0}, {}, {"miner": 100.0}, site_bound=True, deposit_bound=True)}
        table = workshop_count.runs_per_workshop_by_recipe(recipes, {"field": 0.5, "oven": 0.5}, 4.0, 2000.0)
        self.assertEqual(table, {"oven": 40.0, "field": 8.0})


class RefreshWorkshopsTests(unittest.TestCase):
    def test_a_shrunk_producer_counts_fewer_workshops_and_a_plantless_one_keeps_its_count(self):
        planted = Producer("a", "owner", "oven", "t", capacity_runs=400.0, workshops=3)
        plantless = Producer("b", "owner", "farm", "t", capacity_runs=400.0, workshops=7)
        store = ProducerStore({"a": planted, "b": plantless})
        workshop_count.refresh_workshops(store, {"oven": 40.0})
        self.assertEqual(store.get("a").workshops, 10)
        self.assertEqual(store.get("b").workshops, 7)
        store.table.capacity_runs[store.row_of["a"]] = 90.0
        workshop_count.refresh_workshops(store, {"oven": 40.0})
        self.assertEqual(store.get("a").workshops, 2)


class PricingReadsTheCountTests(unittest.TestCase):
    def test_a_producer_of_many_workshops_stands_for_many(self):
        record = types.SimpleNamespace(producers={"crowd": Producer("crowd", "o", "oven", "t", 1.0, workshops=40),
                                                  "lone": Producer("lone", "o", "oven", "t", 1.0, workshops=1)})
        self.assertTrue(seller_offers.stands_for_many(record, Offer("crowd", "bread", "area", "t", 1.0, 1.0)))
        self.assertFalse(seller_offers.stands_for_many(record, Offer("lone", "bread", "area", "t", 1.0, 1.0)))


if __name__ == "__main__":
    unittest.main()
