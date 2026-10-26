"""Complaint 616: vines and olives take years to bear, a press and jars are used up making wine and oil, and a
build bill is charged interest only from when it is spent."""
QUICK_TOPIC = True

import os
import unittest

from sim.prices import solve_prices
from sim.engine.catalog import load_production_catalog
from sim.world import capital_market

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)
_WAGES = {"vine_and_olive_tender": 1.0, "carpenter": 1.0, "mason": 1.0, "potter": 1.0, "farmer": 1.0}


class EstablishmentCarry(unittest.TestCase):

    def test_outlay_spread_over_the_wait_earns_interest_only_from_when_it_is_spent(self):
        rate, years = 0.1, 3.0
        # one third of the bill goes out at the start of each year; the share spent in year k grows for the
        # years that remain, counted from the middle of the year it is spent in
        spent_at_the_start = (1.0 + rate) ** years
        carried = capital_market.establishment_carry_factor(rate, years)
        self.assertLess(carried, spent_at_the_start)
        spent_at_year_starts = sum((1.0 + rate) ** (years - year) for year in range(int(years))) / years
        spent_at_year_ends = sum((1.0 + rate) ** (years - year - 1) for year in range(int(years))) / years
        self.assertLess(carried, spent_at_year_starts)
        self.assertGreater(carried, spent_at_year_ends)

    def test_no_wait_or_a_nil_rate_carries_nothing(self):
        self.assertEqual(capital_market.establishment_carry_factor(0.1, 0.0), 1.0)
        self.assertEqual(capital_market.establishment_carry_factor(0.0, 5.0), 1.0)

    def test_a_longer_wait_costs_more_per_unit_of_the_bill(self):
        self.assertGreater(capital_market.establishment_carry_factor(0.1, 7.0),
                           capital_market.establishment_carry_factor(0.1, 2.0))


class BarrenYears(unittest.TestCase):

    def test_a_stand_yields_only_after_the_years_before_it_bears(self):
        self.assertEqual(capital_market.bearing_years(30.0, 2.0), 28.0)
        self.assertEqual(capital_market.bearing_years(30.0, 0.0), 30.0)

    def test_a_stand_that_never_bears_is_refused(self):
        with self.assertRaises(ValueError):
            capital_market.bearing_years(2.0, 2.0)

    def test_at_a_nil_rate_the_bill_is_repaid_over_the_bearing_years_alone(self):
        self.assertAlmostEqual(capital_market.stand_yearly_share(0.0, 30.0, 2.0), 1.0 / 28.0)

    def test_no_wait_is_an_ordinary_plant(self):
        self.assertAlmostEqual(capital_market.stand_yearly_share(0.07, 25.0, 0.0),
                               capital_market.capital_recovery_factor(0.07, 25.0))

    def test_a_new_vineyard_costs_more_per_kilogram_than_the_same_plant_that_bears_at_once(self):
        entry = _PRODUCTION["grapes_kg"]
        stand = entry["capital"][0]
        prices = {"hectare_land": 1.0}
        cost = solve_prices.recipe_cost_and_allocation("grapes_kg", entry, prices, _WAGES, interest_rate=0.05)[0]
        at_once = dict(entry, capital=[dict(stand, establishment_years=0.0)])
        cost_at_once = solve_prices.recipe_cost_and_allocation(
            "grapes_kg", at_once, prices, _WAGES, interest_rate=0.05)[0]
        self.assertGreater(cost, cost_at_once)

    def test_the_vineyard_and_the_grove_declare_the_years_before_they_bear(self):
        self.assertGreater(_PRODUCTION["grapes_kg"]["capital"][0]["establishment_years"], 0.0)
        self.assertGreater(_PRODUCTION["olives_kg"]["capital"][0]["establishment_years"],
                           _PRODUCTION["grapes_kg"]["capital"][0]["establishment_years"])


class PressAndJars(unittest.TestCase):

    def cost(self, material, prices, wages=None):
        return solve_prices.recipe_cost_and_allocation(
            material, _PRODUCTION[material], prices, wages or _WAGES, interest_rate=0.05)[1][material]

    def base_prices(self):
        return {"grapes_kg": 1.0, "olives_kg": 1.0, "amphora_count": 10.0, "hectare_land": 1.0,
                "timber_m3": 1.0, "stone_kg": 1.0}

    def test_wine_and_oil_consume_their_crop_and_jars_and_stand_in_a_press(self):
        for material, crop in (("wine_common_kg", "grapes_kg"), ("olive_oil_kg", "olives_kg")):
            entry = _PRODUCTION[material]
            self.assertIn(crop, entry["inputs"])
            self.assertGreater(entry["inputs"]["amphora_count"], 0.0)
            self.assertTrue(any("press" in item["good"] for item in entry["capital"]))

    def test_a_dearer_jar_makes_wine_and_oil_dearer(self):
        for material in ("wine_common_kg", "olive_oil_kg"):
            cheap = self.cost(material, dict(self.base_prices(), amphora_count=1.0))
            dear = self.cost(material, dict(self.base_prices(), amphora_count=50.0))
            self.assertGreater(dear, cheap, material)

    def test_a_dearer_press_makes_wine_and_oil_dearer(self):
        for material in ("wine_common_kg", "olive_oil_kg"):
            cheap = self.cost(material, dict(self.base_prices(), timber_m3=1.0))
            dear = self.cost(material, dict(self.base_prices(), timber_m3=500.0))
            self.assertGreater(dear, cheap, material)

    def test_the_jar_is_made_by_potters_from_clay_through_the_ceramic_recipe(self):
        jar = _PRODUCTION["amphora_count"]
        self.assertIn("potter", jar["labour_hours"])
        self.assertIn("ceramic_kg", jar["inputs"])
        self.assertIn("clay_kg", _PRODUCTION["ceramic_kg"]["inputs"])
        self.assertGreater(jar["unit_mass_kg"], 0.0)

    def test_a_press_holds_the_land_one_press_served_in_cato(self):
        # 3 presses to 100 iugera of vines, 5 to 240 of olives, at 2,523 square metres to the iugerum
        wine = _PRODUCTION["wine_common_kg"]["capital"][0]["annual_output_at_basis"]
        oil = _PRODUCTION["olive_oil_kg"]["capital"][0]["annual_output_at_basis"]
        self.assertAlmostEqual(wine, 100.0 / 3.0 * 0.2523 * 2700.0, delta=1.0)
        self.assertAlmostEqual(oil, 48.0 * 0.2523 * 300.0, delta=1.0)


class CropLabourFromTheAgronomists(unittest.TestCase):

    def test_vineyard_hours_are_a_working_year_over_columellas_seven_iugera(self):
        from sim.unit_conversions import HOURS_PER_PERSON_YEAR
        hours = _PRODUCTION["grapes_kg"]["labour_hours"]["vine_and_olive_tender"]
        self.assertAlmostEqual(hours, HOURS_PER_PERSON_YEAR / (7.0 * 0.2523), delta=2.0)

    def test_grove_hours_are_catos_five_labourers_over_240_iugera(self):
        from sim.unit_conversions import HOURS_PER_PERSON_YEAR
        hours = _PRODUCTION["olives_kg"]["labour_hours"]["vine_and_olive_tender"]
        self.assertAlmostEqual(hours, 5.0 * HOURS_PER_PERSON_YEAR / (240.0 * 0.2523), delta=1.0)

    def test_oil_jars_hold_the_oil_at_its_density(self):
        jar_litres, oil_density = 26.0, 0.911
        entry = _PRODUCTION["olive_oil_kg"]
        self.assertAlmostEqual(entry["inputs"]["amphora_count"],
                               entry["outputs"]["olive_oil_kg"] / (jar_litres * oil_density), delta=0.01)


class HoldingInterestRule(unittest.TestCase):

    def test_stock_held_is_charged_on_the_inputs_laid_out_not_on_the_labour_after(self):
        entry = {"outputs": {"cured_kg": 1.0}, "inputs": {"raw_kg": 10.0}, "labour_hours": {"labourer": 100.0},
                 "holding_years": 2.0}
        held = solve_prices.recipe_cost_and_allocation(
            "cured_kg", entry, {"raw_kg": 1.0}, {"labourer": 1.0}, interest_rate=0.1)[0]
        free = solve_prices.recipe_cost_and_allocation(
            "cured_kg", dict(entry, holding_years=0.0), {"raw_kg": 1.0}, {"labourer": 1.0}, interest_rate=0.1)[0]
        self.assertAlmostEqual(held - free, 10.0 * 0.1 * 2.0)


if __name__ == "__main__":
    unittest.main()
