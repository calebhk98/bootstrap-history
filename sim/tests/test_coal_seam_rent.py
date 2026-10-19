"""Complaints/562: coal's seam rent comes from the land its working takes, and what remains of the gap to firewood.

Every extracted good drawn on a catalogue deposit that carries no Ricardian ore rent (coal) states the surface
land its working occupies, charged at the solved land rent; the ore goods get their rent from the deposits
(`rent_standin.rent_hours_per_kg_by_ore_material`). The comparison with firewood is per megajoule.
"""

QUICK_TOPIC = True

import os
import unittest

from sim.engine.catalog import load_production_catalog
from sim.engine.solve_prices_core import recipe_cost_and_allocation
from sim.geography.api import mine_demand_goods
from sim.world import deposits

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WAGES = {"labourer": 1.0, "miner": 1.0}
# Calorific values: bituminous coal as data/production/70_energy.json takes it; air-dried cordwood (about 20
# percent moisture) near the middle of the 14 to 16 MJ/kg usually cited (Engineering Toolbox, biomass heat values).
COAL_MEGAJOULES_PER_KILOGRAM = 29.0
FIREWOOD_MEGAJOULES_PER_KILOGRAM = 15.0


def hours_per_kilogram(production, material, land_rent):
    entry = {key: value for key, value in production[material].items() if key != "capital"}
    _total, prices = recipe_cost_and_allocation(material, entry, {"hectare_land": land_rent}, WAGES)
    return prices[material]


class CoalSeamRentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.production = load_production_catalog(ROOT)

    def test_every_deposit_good_without_an_ore_rent_works_land(self):
        ore_goods = set(deposits.rent_bearing_ore_materials())
        drawn = {good for goods in mine_demand_goods().values() for good in goods
                 if self.production.get(good, {}).get("extracted_from") and good not in ore_goods}
        self.assertIn("coal_kg", drawn)
        for good in drawn:
            self.assertGreater(self.production[good].get("land_hectare_years", 0.0), 0.0, good)

    def test_the_seam_rent_follows_the_land_rent(self):
        free = hours_per_kilogram(self.production, "coal_kg", 0.0)
        low = hours_per_kilogram(self.production, "coal_kg", 100.0)
        high = hours_per_kilogram(self.production, "coal_kg", 200.0)
        self.assertGreater(low, free)
        self.assertAlmostEqual(high - free, 2.0 * (low - free), places=12)
        land_hectare_years = self.production["coal_kg"]["land_hectare_years"]
        self.assertAlmostEqual(low - free, 100.0 * land_hectare_years / 1000.0, places=12)

    def test_the_seam_rent_is_small_beside_the_forest_land(self):
        # a worked seam is a small part of the surface it lies under, unlike a forest felled whole
        coal = self.production["coal_kg"]["land_hectare_years"]
        firewood = self.production["firewood_kg"]["land_hectare_years"]
        self.assertLess(coal, firewood / 100.0)

    def test_coal_stays_below_firewood_per_megajoule_without_any_forest_rent(self):
        # labour alone already puts coal under firewood per megajoule, so the gap the complaint saw is not
        # a missing seam rent: the seam rent that would close it dwarfs the land a working occupies.
        coal = hours_per_kilogram(self.production, "coal_kg", 0.0) / COAL_MEGAJOULES_PER_KILOGRAM
        wood = hours_per_kilogram(self.production, "firewood_kg", 0.0) / FIREWOOD_MEGAJOULES_PER_KILOGRAM
        self.assertLess(coal, wood)
        for land_rent in (50.0, 150.0, 400.0):
            coal_priced = hours_per_kilogram(self.production, "coal_kg", land_rent) / COAL_MEGAJOULES_PER_KILOGRAM
            wood_priced = hours_per_kilogram(self.production, "firewood_kg", land_rent) / FIREWOOD_MEGAJOULES_PER_KILOGRAM
            self.assertLess(coal_priced, wood_priced)
        land_hectare_years = self.production["coal_kg"]["land_hectare_years"]
        wood_per_megajoule = hours_per_kilogram(self.production, "firewood_kg", 0.0) / FIREWOOD_MEGAJOULES_PER_KILOGRAM
        coal_labour = hours_per_kilogram(self.production, "coal_kg", 0.0)
        break_even_seam_rent = wood_per_megajoule * COAL_MEGAJOULES_PER_KILOGRAM - coal_labour
        self.assertGreater(break_even_seam_rent, 0.0)
        # the land rent per hectare-year at which coal's land term alone would close the gap
        self.assertGreater(break_even_seam_rent * 1000.0 / land_hectare_years, 1.0e3)


if __name__ == "__main__":
    unittest.main()
