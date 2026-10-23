"""The granary (Complaints/44-no-granary-so-the-baseline-collapses.md), on inputs the test builds.

  1. `agriculture.stock_to_carry_forward_kg`: a caller that persists `Storage` across years must add `seed_retained_kg`
     back into `stock_after_kg`, or one season's seed is deducted twice a year and the granary starves the population.
  2. `farm_year.run_farm_year`: the stock carried forward is capped at `agriculture.granary_capacity_kg`, because a granary
     is a physical structure, not an unlimited ledger, and a debt in seed corn does not pass on as a negative stock.
  3. The farm workforce share does not respond to famine: it is computed from crop, soil and technique constants only.

The century measurement of the granary is in Complaints/473 (test migration, rule-tests-07)."""
import inspect
import unittest

from sim.world import agriculture, farming_technique, farm_year as farm_year_model

QUICK_TOPIC = True


class DoubleSeedDeductionTests(unittest.TestCase):
    """The bug this task's own probe caught: persisting `stock_after_kg`
    alone (without `seed_retained_kg` added back) manufactures a
    structural, weather-independent annual deficit of one season's seed
    requirement - see `agriculture.stock_to_carry_forward_kg`'s own
    docstring and `Storage.step`'s docstring section on carrying stock
    across years for the full mechanism.
    """

    # A population sized consistently with its own land/labour - matching
    # how sim/engine/core.py's `_demographic_recovery` actually builds
    # these three together, rather than an arbitrary land/population
    # mismatch that would swamp the effect being measured under its own
    # structural food surplus (agriculture.py's module docstring names
    # that surplus - roughly fourfold - as this module's own headline
    # finding, and a land/population pairing far outside what
    # `farmland_for_population` would choose can hide the double-seed bug
    # inside it instead of demonstrating it).
    _POPULATION = 500000.0

    def _consistent_land_and_workers(self):
        # Mirrors sim/engine/core.py's `_demographic_recovery` exactly -
        # see its own extensive comment on why `labour_hours` MUST be
        # built as `hectares_worked * REFERENCE_LABOUR_HOURS_PER_HECTARE`
        # rather than `workers_fte * ANNUAL_LABOUR_HOURS_PER_FARM_WORKER`
        # (the two conventions disagree by roughly 4.4x and using the
        # wrong one inflates the harvest enough to mask the very deficit
        # this test exists to demonstrate).
        land = agriculture.farmland_for_population(self._POPULATION)
        workers_fte = agriculture.farm_workers_fte_for_population(
            self._POPULATION)
        hectares_worked = min(
            land.hectares,
            workers_fte * agriculture.hectares_cropped_per_farm_worker())
        labour_hours = (hectares_worked
                        * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE)
        return land, workers_fte, labour_hours

    def test_carrying_stock_after_kg_alone_loses_a_whole_seasons_seed_every_year(self):
        land, workers_fte, labour_hours = self._consistent_land_and_workers()
        one_season_seed_kg = (agriculture.SEED_SOWING_RATE_KG_PER_HA
                              * land.hectares)
        stock = 0.0
        for _year in range(10):
            storage = agriculture.Storage(stock_kg=stock, seed=42)
            flows = storage.step(land, labour_hours, self._POPULATION,
                                 worker_count=workers_fte)
            stock = flows.stock_after_kg  # THE BUG: seed_retained_kg dropped
        # `stock_after_kg` has had `seed_retained_kg` (one whole season's
        # seed) removed from it without that amount ever being added back
        # anywhere - so at reference weather (this test's deterministic
        # seed lands close to it), the naive carry sits at roughly minus
        # one season's seed requirement, not at roughly zero the way a
        # correctly-closed cycle would.
        self.assertLess(stock, -0.5 * one_season_seed_kg, (stock,
                        one_season_seed_kg))

    def test_the_fixed_carry_rule_does_not_drift_structurally(self):
        land, workers_fte, labour_hours = self._consistent_land_and_workers()
        stock = 0.0
        stocks = []
        for _year in range(30):
            storage = agriculture.Storage(stock_kg=stock, seed=42)
            flows = storage.step(land, labour_hours, self._POPULATION,
                                 worker_count=workers_fte)
            stock = agriculture.stock_to_carry_forward_kg(flows)
            stocks.append(stock)
        # The corrected rule may still drift (this module's own headline
        # finding is a large structural food SURPLUS at reference
        # technique - see agriculture.py's module docstring), but it must
        # not drift toward the same catastrophic, ever-more-negative
        # trajectory the naive rule produces on the same inputs. A loose,
        # one-sided bound: never falls anywhere near the naive rule's
        # 30-year floor.
        self.assertGreater(min(stocks),
                           -5.0 * agriculture.SEED_SOWING_RATE_KG_PER_HA
                           * land.hectares)

    def test_stock_to_carry_forward_kg_is_exactly_stock_after_plus_seed_retained(self):
        land = agriculture.Land(50.0)
        storage = agriculture.Storage(stock_kg=1000.0, seed=7)
        flows = storage.step(land, labour_hours=50.0 * 150.0, population=20.0)
        self.assertAlmostEqual(
            agriculture.stock_to_carry_forward_kg(flows),
            flows.stock_after_kg + flows.seed_retained_kg, places=6)


class GranaryCapacityTests(unittest.TestCase):
    """The stock a farm year carries forward never exceeds what a granary of that year's demand can hold."""

    def _run_years(self, years, hectares, quality=1.3, weather=1.0):
        land = agriculture.Land(hectares, quality=quality)
        population = 20000.0
        workers = agriculture.farm_workers_fte_for_population(population)
        technique = farming_technique.DEFAULT_TECHNIQUE
        stock = 0.0
        rows = []
        for year in range(years):
            result = farm_year_model.run_farm_year(land, technique, stock, population, workers, 42 + year, weather)
            stock = result.stock_kg
            capacity = agriculture.granary_capacity_kg(result.farm_year.food_demand_kg)
            rows.append((stock, capacity))
        return rows

    def test_the_carried_stock_never_exceeds_capacity_over_many_good_years(self):
        land_hectares = agriculture.farmland_for_population(20000.0).hectares * 2.0
        rows = self._run_years(60, land_hectares)
        for stock, capacity in rows:
            self.assertLessEqual(stock, capacity + 1e-6, (stock, capacity))

    def test_the_cap_binds_given_a_structural_surplus(self):
        # otherwise the cap test above would pass even with capacity computed as zero
        land_hectares = agriculture.farmland_for_population(20000.0).hectares * 2.0
        rows = self._run_years(60, land_hectares)
        self.assertGreater(max(stock / capacity for stock, capacity in rows if capacity > 0), 0.5)

    def test_a_granary_never_holds_less_than_nothing(self):
        starved = self._run_years(20, agriculture.farmland_for_population(20000.0).hectares * 0.05, weather=0.5)
        for stock, _capacity in starved:
            self.assertGreaterEqual(stock, 0.0)


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
