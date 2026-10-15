"""Complaints 473 and 507 (stage 2): the opening is internally consistent.

One final demand sizes the producers' plant, the hands they hire and the income households receive, so the
money households are paid is the money the demand they were sized to spends; the metal the money loses a year
is a demand the opening sizes the coin metal's producers to; a recipe a deposit cannot feed does not carry
the demand, the next cheapest does. Hand-built fixtures (economy_fixture.py), nothing read from data/.
"""
import dataclasses
import unittest

from sim.economy import opening, opening_income, opening_metal, opening_runs
from sim.economy.economy import Economy
from sim.economy.types import Recipe, SiteLimit
from sim.tests import economy_fixture as fixture
from sim.tests import harness


def national_value(record, prices):
    return sum(quantity * prices.get(good, 0.0) for good, quantity in record.opening_basket.items())


class OpeningIncomeTests(unittest.TestCase):
    def test_income_per_head_is_the_fixed_point_of_income_and_the_demand_it_pays_for(self):
        # demand saturates: it never exceeds 5 a head, and is what income buys below that
        per_head = opening_income.settled_income_per_head(100.0, 10.0, lambda income: 10.0 * min(income, 5.0))
        self.assertAlmostEqual(per_head, 5.0, places=6)
        per_head = opening_income.settled_income_per_head(100.0, 10.0, lambda income: 10.0 * (0.5 * income + 1.0))
        self.assertAlmostEqual(per_head, 2.0, places=6)

    def test_income_never_exceeds_the_full_employment_ceiling(self):
        per_head = opening_income.settled_income_per_head(3.0, 10.0, lambda income: 10.0 * (income + 5.0))
        self.assertEqual(per_head, 3.0)

    def test_the_opening_pays_households_the_value_of_the_demand_producers_are_sized_to(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        paid = sum(cohort.last_year_income for cohort in record.cohorts.values())
        self.assertAlmostEqual(paid / national_value(record, setup.opening_prices), 1.0, places=2)

    def test_that_income_is_below_what_every_worker_employed_all_year_would_earn(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        paid = sum(cohort.last_year_income for cohort in record.cohorts.values())
        ceiling = (setup.opening_wages[setup.unskilled_trade] * setup.working_hours_per_year * setup.working_share
                   * sum(setup.opening_population_by_tile.values()))
        self.assertLess(paid, ceiling)


class OpeningStaffingTests(unittest.TestCase):
    def test_the_workforce_is_placed_for_the_runs_producers_expect_to_sell(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        wanted = {}
        for producer in record.producers.values():
            for trade, hours in setup.recipes[producer.recipe_id].labour_hours.items():
                wanted[trade] = wanted.get(trade, 0.0) + producer.expected_sales * hours
        for trade in (fixture.MINER, fixture.SMITH):
            held = sum(sum(bands.get(trade, [])) for bands in record.workforce.workers.values()) * setup.working_hours_per_year
            self.assertGreaterEqual(held, 0.99 * wanted.get(trade, 0.0), trade)

    def test_plant_is_larger_than_the_runs_to_work_by_the_share_of_it_that_does_not_work(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        for producer in record.producers.values():
            recipe = setup.recipes[producer.recipe_id]
            share = opening_income.working_share(recipe, setup.opening_prices, setup.opening_wages)
            self.assertGreater(share, 0.0)
            self.assertLessEqual(share, 1.0)
            self.assertAlmostEqual(producer.capacity_runs * share / producer.expected_sales,
                                   1.0 + opening.OPENING_SPARE_CAPACITY_SHARE, places=6)


class OpeningMetalTests(unittest.TestCase):
    def test_the_producers_of_the_coin_metal_are_sized_to_replace_what_the_money_loses(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        lost = opening_metal.yearly_replacement(setup, record)
        self.assertGreater(lost, 0.0)
        made = sum(producer.capacity_runs * setup.recipes[producer.recipe_id].outputs.get(fixture.METAL, 0.0)
                   for producer in record.producers.values())
        self.assertGreaterEqual(made, lost)

    def test_fiat_money_loses_no_metal(self):
        setup = fixture.small_setup(currency=dataclasses.replace(fixture.small_setup().currency, regime="fiat",
                                                                 backing_good=None, backing_per_unit=0.0))
        record, _areas, _carriage = opening.open_economy(setup)
        self.assertEqual(opening_metal.yearly_replacement(setup, record), 0.0)


def two_ways_to_make_alloy(cheap_limit=None):
    """Two recipes for one alloy: a cheap one on an ore only a site supplies, a dear one on a bought input."""
    recipes = {
        "dig": Recipe("dig", {"ore_kg": 1000.0}, {}, {"miner": 10.0}, site_bound=True),
        "cheap": Recipe("cheap", {"alloy_kg": 100.0}, {"ore_kg": 500.0}, {"smith": 10.0}),
        "dear": Recipe("dear", {"alloy_kg": 100.0}, {"grain_kg": 100.0}, {"smith": 80.0}),
        "farm": Recipe("farm", {"grain_kg": 1000.0}, {}, {"labourer": 10.0}),
    }
    limits = {"dig": {"hills": SiteLimit("dig", "hills", cheap_limit)}} if cheap_limit else {}
    return recipes, limits


class RecipeChoiceTests(unittest.TestCase):
    prices = {"ore_kg": 0.1, "alloy_kg": 1.0, "grain_kg": 0.1}
    wages = {"miner": 1.0, "smith": 1.0, "labourer": 1.0}

    def test_the_cheapest_recipe_for_a_good_comes_first(self):
        recipes, _limits = two_ways_to_make_alloy()
        ranked = opening_runs.ranked_recipes(recipes, self.prices, self.wages, 0.05)
        self.assertEqual(ranked["alloy_kg"], ["cheap", "dear"])

    def test_a_deposit_that_cannot_feed_the_cheap_recipe_leaves_the_rest_to_the_next(self):
        recipes, limits = two_ways_to_make_alloy(cheap_limit=2.0)       # two runs of ore: four of the cheap recipe
        ranked = opening_runs.ranked_recipes(recipes, self.prices, self.wages, 0.05)
        ceilings = opening_runs.run_ceilings(recipes, limits)
        self.assertAlmostEqual(ceilings["cheap"], 4.0)
        runs = opening_runs.required_runs({"town": {"alloy_kg": 1000.0}}, ranked, recipes, ceilings)
        self.assertAlmostEqual(runs["cheap"], 4.0)
        self.assertAlmostEqual(runs["dear"], 6.0)                       # the other six hundred kilograms
        self.assertAlmostEqual(runs["cheap"] * 100.0 + runs["dear"] * 100.0, 1000.0)

    def test_with_no_limit_the_cheap_recipe_carries_it_all(self):
        recipes, limits = two_ways_to_make_alloy()
        ranked = opening_runs.ranked_recipes(recipes, self.prices, self.wages, 0.05)
        runs = opening_runs.required_runs({"town": {"alloy_kg": 1000.0}}, ranked, recipes,
                                          opening_runs.run_ceilings(recipes, limits))
        self.assertAlmostEqual(runs["cheap"], 10.0)
        self.assertNotIn("dear", runs)

    def test_a_co_product_nobody_wants_does_not_pay_for_a_run(self):
        recipes = {
            "smelt": Recipe("smelt", {"lead_kg": 1000.0, "silver_kg": 1.0}, {}, {"smith": 15.0}),
            "refine": Recipe("refine", {"silver_kg": 1.0}, {}, {"smith": 8.0}),
        }
        prices = {"lead_kg": 1.0, "silver_kg": 800.0}
        wages = {"smith": 1.0}
        shared = opening_runs.ranked_recipes(recipes, prices, wages, 0.05)
        self.assertEqual(shared["silver_kg"][0], "smelt")
        wanted = opening_runs.ranked_recipes(recipes, prices, wages, 0.05, {"silver_kg": 10.0, "lead_kg": 5.0})
        self.assertEqual(wanted["silver_kg"][0], "refine")


class OpeningSeedsAreCostsTests(unittest.TestCase):
    """The Rome opening's prices (Complaint 507 stage 2): the cost of making each good at the opening wages,
    rate and rent, and nothing of demand or of the player's money."""

    @classmethod
    def setUpClass(cls):
        from sim.engine import economy_port_costs, economy_port_setup
        from sim.labour.api import wage_provider
        cls.game = harness.unopened_sim()
        cls.opening = economy_port_setup.opening_values(cls.game)
        cls.costs = economy_port_costs
        cls.wage_provider = wage_provider

    def _cost_of_one_step(self, good):
        from sim.engine import long_run_costs, making_cost
        from sim.engine.prices import default_production_entries
        game, prices = self.game, self.opening["prices"]
        production = default_production_entries()
        techniques = frozenset(game.state.projects.granted) | frozenset(game.techniques_in_use())
        wage_of = self.costs.wage_function(game, production)
        rent_of = long_run_costs.opening_rent_of(techniques, wage_of, game.civ, production)
        made = making_cost.cost_of_making(good, techniques, prices.get, wage_of, self.opening["rate"], rent_of,
                                          production=production, civilization=game.civ)
        return made.unit_cost

    def test_the_staple_costs_what_its_recipe_bill_comes_to_at_the_opening_wages(self):
        staple = self.wage_provider.staple_material(self.game.civ)
        self.assertAlmostEqual(self.opening["prices"][staple] / self._cost_of_one_step(staple), 1.0, delta=0.25)

    def test_the_coin_metal_is_priced_at_its_cost_of_making(self):
        metal = self.wage_provider.coin_standard(self.game.civ)["material"]
        self.assertAlmostEqual(self.opening["prices"][metal] / self._cost_of_one_step(metal), 1.0, delta=0.25)

    def test_the_prices_in_hours_of_work_do_not_depend_on_what_the_player_holds(self):
        from sim.engine import economy_port_setup
        richer = economy_port_setup.opening_values(harness.unopened_sim(capital=1.0e9))
        unskilled = self.opening["unskilled_trade"]
        for good, price in sorted(self.opening["prices"].items())[:60]:
            self.assertAlmostEqual(richer["prices"][good] / richer["wages"][unskilled],
                                   price / self.opening["wages"][unskilled], places=9, msg=good)

    def test_a_good_the_economy_has_not_priced_is_seeded_at_a_cost_of_making_at_live_prices(self):
        from sim.engine import economy_port_late
        from sim.engine.prices import default_production_entries
        known = dict(self.opening["prices"])
        staple = self.wage_provider.staple_material(self.game.civ)
        gone = known.pop(staple)
        found = economy_port_late.late_goods_costs(self.game, known, [staple], frozenset(self.game.state.projects.granted),
                                                   default_production_entries())
        self.assertAlmostEqual(found[staple] / gone, 1.0, delta=0.25)


class OpeningWageAnchorTests(unittest.TestCase):
    def test_a_coin_metal_costs_the_same_hours_wherever_it_is_made_so_an_hour_is_paid_alike_in_metal(self):
        from sim.engine import data
        from sim.labour.api import wage_provider
        grams = {}
        for civ_id in ("rome_100ad", "england_1300", "norse_900ad"):
            civ = data.load_civ(civ_id)
            standard = wage_provider.coin_standard(civ)
            grams[civ_id] = data.starting_schedule(civ_id).money_per_labour_hour * standard["kg_per_unit"] * 1000.0
        self.assertLess(max(grams.values()) / min(grams.values()), 1.15, grams)


if __name__ == "__main__":
    unittest.main()
