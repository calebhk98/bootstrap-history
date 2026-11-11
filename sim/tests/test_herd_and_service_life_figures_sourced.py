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


if __name__ == "__main__":
    unittest.main()
