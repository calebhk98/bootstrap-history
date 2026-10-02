"""Silver and gold come from the deposits worked (Complaints 291, 333, 334, 373):
a silver assay per lead deposit, no silver counted twice, one dressing rate for
every route, a jarosite route that eats lead, and gold priced from its deposits."""
import json
import unittest

from sim.engine.prices import _default_production_entries
from sim.world import deposits, ore_dressing
from sim.unit_conversions import KILOGRAMS_PER_TONNE

# Wood 2022 (Archaeometry): argentiferous galena is about 0.2 wt% silver.
WOOD_SILVER_FRACTION_OF_GALENA = 0.002
# PbS from molar masses (g/mol).
LEAD_FRACTION_OF_GALENA = 207.2 / 239.3
LEAD_SMELTING_RECOVERY = 0.87
ROAST_AND_BELLOWS_HOURS_PER_TONNE_LEAD = 18.0 + 46.0


def _lead_deposits():
    return deposits.load_deposits("lead")


def _silver_per_tonne_lead(deposit):
    joint = deposits.joint_output_quantities_kg(deposit)
    return joint.get("silver_kg", 0.0) / joint["lead_kg"] * KILOGRAMS_PER_TONNE


class SilverAssayPerDeposit(unittest.TestCase):

    def test_laurion_lead_carries_about_two_kilograms_of_silver_per_tonne(self):
        laurion = next(d for d in _lead_deposits() if d.name == "laurion_lead")
        self.assertGreaterEqual(_silver_per_tonne_lead(laurion), 2.0 - 1e-9)
        self.assertLessEqual(_silver_per_tonne_lead(laurion), 2.3)

    def test_galena_deposits_carry_woods_zero_point_two_percent(self):
        expected = WOOD_SILVER_FRACTION_OF_GALENA / LEAD_FRACTION_OF_GALENA * KILOGRAMS_PER_TONNE
        for name in ("hispania_lead", "britannia_lead", "italia_lead_generic"):
            deposit = next(d for d in _lead_deposits() if d.name == name)
            self.assertAlmostEqual(_silver_per_tonne_lead(deposit) / expected, 1.0, delta=0.03, msg=name)

    def test_each_lead_deposit_has_its_own_assay_not_a_district_silver_grade(self):
        assays = {d.name: _silver_per_tonne_lead(d) for d in _lead_deposits()}
        self.assertEqual(assays["gaul_germania_lead_generic"], 0.0)
        self.assertNotAlmostEqual(assays["laurion_lead"], assays["hispania_lead"], places=2)

    def test_recipe_silver_is_the_output_weighted_assay_times_recoveries(self):
        entry = _default_production_entries()["lead_kg"]
        lead_total = silver_total = 0.0
        for deposit in _lead_deposits():
            joint = deposits.joint_output_quantities_kg(deposit)
            lead_total += joint["lead_kg"]
            silver_total += joint.get("silver_kg", 0.0)
        recovered = silver_total / lead_total * 0.90 * 0.92
        recipe = entry["outputs"]["silver_kg"] / entry["outputs"]["lead_kg"]
        self.assertAlmostEqual(recipe / recovered, 1.0, delta=0.02)


class SilverSupplyCountedOnce(unittest.TestCase):

    def test_silver_only_deposits_and_lead_byproduct_sum_to_the_empire_total(self):
        with open(deposits.RESOURCES_FILE) as handle:
            empire_silver = json.load(handle)["empire_output_100ad"]["silver"]["t_per_yr"]
        silver_only = sum(d.quantity_tonnes_per_year for d in deposits.load_deposits("silver"))
        from_lead = sum(deposits.byproduct_quantities_tonnes_per_year(d).get("silver", 0.0)
                        for d in _lead_deposits())
        self.assertGreater(from_lead, 0.0)
        self.assertAlmostEqual((silver_only + from_lead) / empire_silver, 1.0, places=6)

    def test_demand_the_silver_only_deposits_must_meet_excludes_the_byproduct(self):
        net = deposits.empire_output_net_of_byproducts_tonnes_per_year("silver")
        silver_only = sum(d.quantity_tonnes_per_year for d in deposits.load_deposits("silver"))
        self.assertAlmostEqual(net, silver_only, places=6)


class DressingIsOneRate(unittest.TestCase):

    def test_the_rate_is_polybius_five_cycles_over_a_stated_throughput(self):
        self.assertEqual(ore_dressing.CRUSH_SIEVE_CYCLES, 5)
        self.assertAlmostEqual(
            ore_dressing.dressing_hours_per_tonne_rock(),
            5 / ore_dressing.TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE)

    def test_direct_silver_route_dresses_at_the_shared_rate(self):
        entry = _default_production_entries()["silver_kg"]
        rock = entry["inputs"]["silver_ore_kg"] / KILOGRAMS_PER_TONNE
        self.assertAlmostEqual(entry["labour_hours"]["labourer"] / rock,
                               ore_dressing.dressing_hours_per_tonne_rock(), delta=0.01)

    def test_lead_route_dresses_at_the_same_rate_per_tonne_of_rock(self):
        entry = _default_production_entries()["lead_kg"]
        pool = _lead_deposits()
        total = sum(d.quantity_tonnes_per_year for d in pool)
        rock = sum(d.quantity_tonnes_per_year / total * KILOGRAMS_PER_TONNE
                   / d.ore_grade_kg_per_tonne for d in pool) / LEAD_SMELTING_RECOVERY
        dressing = entry["labour_hours"]["labourer"] - ROAST_AND_BELLOWS_HOURS_PER_TONNE_LEAD
        self.assertAlmostEqual(dressing / rock, ore_dressing.dressing_hours_per_tonne_rock(),
                               delta=0.02 * ore_dressing.dressing_hours_per_tonne_rock())

    def test_jarosite_route_dresses_at_the_same_rate(self):
        entry = _default_production_entries()["silver_jarosite_kg"]
        rock = entry["inputs"]["jarosite_ore_kg"] / KILOGRAMS_PER_TONNE
        self.assertAlmostEqual(entry["labour_hours"]["labourer"] / rock,
                               ore_dressing.dressing_hours_per_tonne_rock(), delta=0.01)


class JarositeRoute(unittest.TestCase):

    def test_a_rio_tinto_jarosite_deposit_exists(self):
        names = [d.name for d in deposits.load_deposits("silver")]
        self.assertIn("rio_tinto_jarosite", names)

    def test_jarosite_smelting_consumes_lead_as_a_collector_flux(self):
        entry = _default_production_entries()["silver_jarosite_kg"]
        self.assertGreater(entry["inputs"].get("lead_kg", 0.0), 0.0)
        self.assertIn("silver_kg", entry["outputs"])
        self.assertEqual(entry["conf"], "D")

    def test_jarosite_ore_comes_from_its_deposit(self):
        entry = _default_production_entries()["jarosite_ore_kg"]
        deposit = next(d for d in deposits.load_deposits("silver") if d.name == "rio_tinto_jarosite")
        self.assertAlmostEqual(
            entry["labour_hours"]["miner"] / deposits.vein_hours_per_tonne_ore(deposit), 1.0, delta=0.05)

    def test_patio_silver_ore_excludes_the_jarosite_deposit(self):
        pool = [d for d in deposits.load_deposits("silver") if d.ore_type == "primary"]
        self.assertNotIn("rio_tinto_jarosite", [d.name for d in pool])
        self.assertTrue(pool)


class GoldFromDeposits(unittest.TestCase):

    def _gold(self, name):
        return next(d for d in deposits.load_deposits("gold") if d.name == name)

    def test_no_recipe_assumes_a_fixed_placer_grade(self):
        entries = _default_production_entries()
        for key in ("gold_kg", "gold_g", "gold_lode_kg"):
            self.assertTrue(any(ore in entries[key]["inputs"]
                                for ore in ("gold_gravel_kg", "gold_lode_ore_kg")), key)

    def test_hydraulic_gold_ore_per_kilogram_is_the_las_medulas_grade(self):
        entry = _default_production_entries()["gold_kg"]
        gravel_per_kilogram = entry["inputs"]["gold_gravel_kg"] / entry["outputs"]["gold_kg"]
        grade_kg_per_tonne = self._gold("las_medulas_alluvial").ore_grade_kg_per_tonne
        recovery = 1.0 / (gravel_per_kilogram * grade_kg_per_tonne / KILOGRAMS_PER_TONNE)
        self.assertGreater(recovery, 0.3)
        self.assertLessEqual(recovery, 1.0)

    def test_aqueduct_build_hours_are_charged_as_capital_of_the_hydraulic_route(self):
        entry = _default_production_entries()["gold_kg"]
        aqueduct = [c for c in entry["capital"] if "aqueduct" in c["good"]]
        self.assertEqual(len(aqueduct), 1)
        self.assertEqual(sum(aqueduct[0]["build_labour_hours"].values()),
                         deposits.AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC)

    def test_hydraulic_route_cost_follows_the_las_medulas_deposit(self):
        entries = _default_production_entries()
        entry = entries["gold_kg"]
        outputs = entry["outputs"]["gold_kg"]
        gravel_hours = (entry["inputs"]["gold_gravel_kg"] / KILOGRAMS_PER_TONNE
                        * sum(entries["gold_gravel_kg"]["labour_hours"].values()))
        capital = entry["capital"][0]
        capital_hours_per_kilogram = (sum(capital["build_labour_hours"].values())
                                      / capital["service_life_years"] / capital["annual_output_at_basis"])
        per_kilogram = ((gravel_hours + sum(entry["labour_hours"].values())) / outputs
                        + capital_hours_per_kilogram)
        # The deposit's own hours per kilogram of contained gold; the recipe also loses some gold.
        own = deposits.total_cost_labour_hours_per_kg(self._gold("las_medulas_alluvial"))
        self.assertGreater(per_kilogram, 0.9 * own)
        self.assertLess(per_kilogram, 3.0 * own)

    def test_lode_gold_labour_follows_the_dacia_deposit(self):
        ore = _default_production_entries()["gold_lode_ore_kg"]
        deposit = self._gold("dacia_vein_gold")
        self.assertAlmostEqual(
            ore["labour_hours"]["miner"] / deposits.vein_hours_per_tonne_ore(deposit), 1.0, delta=0.05)

    def test_gold_is_priced_by_the_marginal_gold_deposit(self):
        from sim.engine.prices import solved_prices
        import os
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with open(os.path.join(root, "data", "civilizations", "rome_100ad.json")) as handle:
            techs = json.load(handle)["starting_techs"]
        prices_json = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 1.0}},
                       "money_per_labour_hour": 1.0}
        prices = solved_prices(techs, prices_json, civilization_id="rome_100ad").prices_in_labour_hours
        pool = deposits.load_deposits("gold")
        demand = sum(d.quantity_tonnes_per_year for d in pool)
        margin = deposits.find_marginal_deposit(pool, demand).price_at_margin_labour_hours_per_kg
        self.assertGreater(prices["gold_kg"], 0.5 * margin)


if __name__ == "__main__":
    unittest.main()
