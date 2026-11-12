"""Complaints 532 and 670: herd and service-life figures that were read from a source follow that source's numbers."""
QUICK_TOPIC = True

import json
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Wilson, FAO, Tswana goat in the traditional system: 284 g a day, 180 days
GOAT_MILK_GRAMS_PER_DAY = 284.0
GOAT_LACTATION_DAYS = 180.0
MILKED_SHARE_OF_HERD = 0.5
# Mummed and Webb 2019: warm dressing percentage of cattle of 241.41 kg mean live weight
CATTLE_WARM_DRESSING_PERCENT = 44.21
# FAO Animal Production and Health Paper 49 section 10.2, percent of live weight
DWARF_SKIN_PERCENT = (10.0, 12.0)
CATTLE_HIDE_PERCENT = (6.0, 8.0)
# FAO farm power study Annex 3 Table 5, hoe replacement years at ten sites (ranges at midpoint)
HOE_REPLACEMENT_YEARS = (1, 2, 3, 1.5, 3, 2, 1.5, 1, 2, 3)


def _load(*parts):
    with open(os.path.join(_ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def milk_per_head_year(grams_per_day, lactation_days, milked_share):
    return grams_per_day / 1000.0 * lactation_days * milked_share


def midpoint(low, high):
    return (low + high) / 2.0


class HerdRows(unittest.TestCase):

    def test_goat_milk_is_the_read_yield_over_the_lactation_for_the_milked_half(self):
        rows = _load("data", "world", "living_stock.json")["materials"]
        self.assertAlmostEqual(rows["goat_kg"]["milk_kg_per_head_year"],
                               milk_per_head_year(GOAT_MILK_GRAMS_PER_DAY, GOAT_LACTATION_DAYS, MILKED_SHARE_OF_HERD))

    def test_cattle_dressing_is_the_read_warm_percentage(self):
        rows = _load("data", "world", "living_stock.json")["materials"]
        self.assertAlmostEqual(rows["cattle_kg"]["dressing_fraction"], CATTLE_WARM_DRESSING_PERCENT / 100.0, places=3)

    def test_hide_shares_are_the_midpoints_of_the_fao_ranges(self):
        rows = _load("data", "world", "living_stock.json")["materials"]
        self.assertAlmostEqual(rows["cattle_kg"]["hide_share_of_live_weight"], midpoint(*CATTLE_HIDE_PERCENT) / 100.0)
        for species in ("sheep_kg", "goat_kg"):
            self.assertAlmostEqual(rows[species]["hide_share_of_live_weight"], midpoint(*DWARF_SKIN_PERCENT) / 100.0)

    def test_herd_recipe_outputs_follow_the_changed_rows(self):
        rows = _load("data", "world", "living_stock.json")["materials"]
        herds = _load("data", "production", "95_herds.json")["materials"]
        self.assertAlmostEqual(herds["milk_kg"]["outputs"]["milk_kg"], 100.0 * rows["goat_kg"]["milk_kg_per_head_year"], places=3)


class ServiceLives(unittest.TestCase):

    def test_iron_tool_life_is_the_mean_hoe_replacement_interval(self):
        years = _load("data", "world", "service_lives.json")["years"]
        self.assertAlmostEqual(years["iron_tools_kg"]["years"], sum(HOE_REPLACEMENT_YEARS) / len(HOE_REPLACEMENT_YEARS))
        self.assertEqual(years["iron_tools_kg"]["confidence"], "C")

    def test_wooden_tool_life_is_half_the_iron_tool_and_stays_a_heuristic(self):
        years = _load("data", "world", "service_lives.json")["years"]
        self.assertAlmostEqual(years["wooden_tools_kg"]["years"], years["iron_tools_kg"]["years"] / 2.0)
        self.assertEqual(years["wooden_tools_kg"]["confidence"], "D")

    def test_cart_life_is_the_oxen_cart_of_the_uganda_table(self):
        years = _load("data", "world", "service_lives.json")["years"]
        self.assertEqual(years["cart"]["years"], 15)


class Complaint670Pass8(unittest.TestCase):

    def test_sheep_and_goat_salt_follow_the_read_daily_salt_of_range_ewes(self):
        rows = _load("data", "world", "living_stock.json")["materials"]
        sheep_kg = midpoint(8.0, 11.0) / 1000.0 * 365.0
        self.assertAlmostEqual(rows["sheep_kg"]["salt_kg_per_head_year"], sheep_kg, delta=0.05)
        self.assertAlmostEqual(rows["goat_kg"]["salt_kg_per_head_year"], sheep_kg * 25.0 / 30.0, delta=0.05)
        self.assertAlmostEqual(rows["cattle_kg"]["salt_kg_per_head_year"], 30.0 / 1000.0 * 365.0, delta=0.1)

    def test_pack_saddle_life_is_the_geometric_mean_of_the_two_read_lives(self):
        years = _load("data", "world", "service_lives.json")["years"]
        self.assertAlmostEqual(years["pack_saddle"]["years"], (0.5 * 20.0) ** 0.5, delta=0.3)

    def test_mule_and_barge_lives_are_the_read_ranges(self):
        years = _load("data", "world", "service_lives.json")["years"]
        self.assertEqual(years["mule"]["years"], midpoint(10.0, 15.0))
        self.assertEqual(years["river_barge"]["years"], 15)

    def test_steel_edge_tool_life_is_the_mid_range_forged_axe_midpoint(self):
        years = _load("data", "world", "service_lives.json")["years"]
        for good in ("tool_steel_kg", "steel_noric_kg"):
            self.assertEqual(years[good]["years"], midpoint(20.0, 40.0))
        self.assertEqual(years["iron_bar_kg"]["years"], midpoint(5.0, 15.0))

    def test_perishable_rates_are_one_over_the_read_keeping_time(self):
        rates = _load("data", "world", "spoilage.json")["rates_per_year"]
        self.assertAlmostEqual(rates["bread_kg"]["rate"], 365.0 / midpoint(3.0, 7.0))
        self.assertAlmostEqual(rates["silk_cocoon_kg"]["rate"], 365.0 / midpoint(2.0, 3.0), delta=1.0)
        self.assertAlmostEqual(rates["hide_kg"]["rate"], 365.0 / midpoint(1.0, 2.0), delta=1.0)
        self.assertAlmostEqual(rates["garum_kg"]["rate"], 1.0 / midpoint(2.0, 3.0))


if __name__ == "__main__":
    unittest.main()
