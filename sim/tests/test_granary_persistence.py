"""The granary (Complaints/44-no-granary-so-the-baseline-collapses.md), on inputs the test builds.

  1. `agriculture.stock_to_carry_forward_kg`: a caller that persists `Storage` across years must add `seed_retained_kg`
     back into `stock_after_kg`, or one season's seed is deducted twice a year and the granary starves the population.
  2. `farm_year.carried_stock_kg`: the stock carried forward is capped at `agriculture.granary_capacity_kg`, because a granary
     is a physical structure, not an unlimited ledger, and a debt in seed corn does not pass on as a negative stock.
  3. The farm workforce share does not respond to famine: it is computed from crop, soil and technique constants only.

The century measurement of the granary is in Complaints/473 (test migration, rule-tests-07)."""
import inspect
import unittest

from sim.world import agriculture, agriculture_storage, farm_year as farm_year_model

QUICK_TOPIC = True


class CarryForwardTests(unittest.TestCase):
    """A caller that persists `Storage` across years must add `seed_retained_kg` back into `stock_after_kg`."""

    def test_stock_to_carry_forward_kg_is_exactly_stock_after_plus_seed_retained(self):
        flows = agriculture_storage.YearFlows(
            weather_multiplier=1.0, labour_hours_applied=0.0, seed_sown_kg=100.0, gross_harvest_kg=900.0,
            food_demand_kg=500.0, consumption_kg=500.0, food_shortfall_kg=0.0, spoilage_kg=20.0, seed_retained_kg=100.0,
            carryover_kg=180.0, stock_before_kg=100.0, stock_after_kg=180.0, food_available_kcal_per_day=0.0,
            marginal_product_last_hour_kg_per_hour=0.0)
        self.assertAlmostEqual(agriculture.stock_to_carry_forward_kg(flows), 280.0, places=6)


class GranaryCapacityTests(unittest.TestCase):
    """The stock a farm year carries forward never exceeds what a granary of that year's demand can hold."""

    def test_the_carried_stock_never_exceeds_capacity(self):
        self.assertEqual(farm_year_model.carried_stock_kg(900.0, 500.0), 500.0)

    def test_a_stock_within_capacity_is_carried_whole(self):
        self.assertEqual(farm_year_model.carried_stock_kg(300.0, 500.0), 300.0)

    def test_a_granary_never_holds_less_than_nothing(self):
        self.assertEqual(farm_year_model.carried_stock_kg(-40.0, 500.0), 0.0)


class FarmWorkforceShareIsFixedTests(unittest.TestCase):
    """Can a famine turn blacksmiths into farmers? Not yet: the share that farms is computed from crop, soil, rotation,
    toolkit and storage constants, and takes no nutrition, wage, price or other scarcity signal."""

    def test_the_farm_share_takes_only_technique_arguments(self):
        self.assertEqual(list(inspect.signature(agriculture.fraction_of_population_that_must_farm).parameters),
                         ["crop", "soil", "rotation", "toolkit", "storage_technique"])

    def test_the_workers_are_that_share_of_the_population(self):
        share = agriculture.fraction_of_population_that_must_farm()
        for population in (1000.0, 500000.0):
            self.assertAlmostEqual(agriculture.farm_workers_fte_for_population(population), share * population)


if __name__ == "__main__":
    unittest.main()
