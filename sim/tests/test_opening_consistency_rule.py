"""Complaints 473 and 507 (stage 2): the opening is internally consistent. One final demand sizes the producers' plant, the
hands they hire and the income households receive, so the money households are paid is the money the demand they were
sized to spends; the metal the money loses a year is a demand the coin metal's producers are sized to; a recipe a deposit
cannot feed does not carry the demand, the next cheapest does. Hand-built fixtures (economy_fixture.py); no game."""
import dataclasses
import unittest

from sim.economy import opening, opening_income, opening_metal, opening_runs
from sim.economy.households_orders import BUDGET_SAFETY_SHARE
from sim.economy.economy import Economy
from sim.economy.types import Recipe, SiteLimit
from sim.tests import economy_fixture as fixture
from sim.refusal import cause_of, facts_of

QUICK_TOPIC = True


def national_value(record, prices):
    return sum(quantity * prices.get(good, 0.0) for good, quantity in record.opening_basket.items())


class OpeningIncomeTests(unittest.TestCase):
    def test_income_per_head_is_the_fixed_point_of_income_and_the_demand_it_pays_for(self):
        # demand saturates: it never exceeds 5 a head, and is what income buys below that
        per_head, labour = opening_income.settled_income_per_head(
            100.0, 10.0, lambda income: (10.0 * min(income, 5.0), 0.5))
        self.assertAlmostEqual(per_head, 5.0, places=6)
        self.assertEqual(labour, 0.5)
        per_head, _labour = opening_income.settled_income_per_head(
            100.0, 10.0, lambda income: (10.0 * (0.5 * income + 1.0), 0.5))
        self.assertAlmostEqual(per_head, 2.0, places=6)

    def test_income_never_exceeds_the_full_employment_ceiling(self):
        per_head, _labour = opening_income.settled_income_per_head(
            3.0, 10.0, lambda income: (10.0 * (income + 5.0), 0.5))
        self.assertEqual(per_head, 3.0)

    def test_a_demand_with_an_autonomous_part_settles_at_the_closed_form_income(self):
        autonomous, propensity, people, ceiling = 40.0, 0.8, 1000.0, 1.0e6
        per_head, labour = opening_income.settled_income_per_head(
            ceiling, people, lambda income: (people * (autonomous + propensity * income), 0.25))
        self.assertAlmostEqual(per_head / (autonomous / (1.0 - propensity)), 1.0, places=6)
        self.assertEqual(labour, 0.25)

    def test_a_demand_that_equals_income_at_every_level_settles_at_the_ceiling_in_one_pass(self):
        asked = []

        def demand_at(income):
            asked.append(income)
            return 10.0 * income, 0.5
        per_head, _labour = opening_income.settled_income_per_head(7.0, 10.0, demand_at)
        self.assertEqual(per_head, 7.0)
        self.assertEqual(asked, [7.0])

    def test_a_demand_below_income_at_every_level_has_no_positive_fixed_point_and_is_refused(self):
        refused = opening_income.settled_income_per_head(100.0, 10.0, lambda income: (10.0 * 0.9 * income, 0.5))
        self.assertEqual(cause_of(refused), "no_positive_income_fixed_point")
        self.assertIn("ceiling", facts_of(refused))

    def test_no_people_is_refused_not_given_an_income_of_zero(self):
        self.assertEqual(cause_of(opening_income.settled_income_per_head(100.0, 0.0, lambda income: (0.0, 0.0))),
                         "no_people_to_pay")

    def test_the_income_where_households_stop_saving_is_found_in_few_passes(self):
        # households spend all they are paid up to 300 a head and a falling share of the rest, as Rome's do
        asked = []

        def demand_at(income):
            asked.append(income)
            return 10.0 * (income if income <= 300.0 else 300.0 + 0.5 * (income - 300.0)), 0.5
        per_head, _labour = opening_income.settled_income_per_head(900.0, 10.0, demand_at)
        self.assertAlmostEqual(per_head / 300.0, 1.0, delta=2.0 * opening_income.OPENING_INCOME_TOLERANCE)
        self.assertLessEqual(len(asked), 20)

    def test_the_tolerance_for_saving_covers_the_margin_the_bids_leave_unspent(self):
        self.assertGreater(opening_income.SAVING_TOLERANCE, BUDGET_SAFETY_SHARE)

    def test_workers_are_paid_alike_and_owners_by_what_they_own(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        paid = opening_income.with_income(record.cohorts, 100.0, 1.0)
        per_head = {cohort_id: cohort.last_year_income / cohort.people for cohort_id, cohort in paid.items()}
        self.assertAlmostEqual(max(per_head.values()), min(per_head.values()), places=6)
        owned = opening_income.with_income(record.cohorts, 100.0, 0.0)
        richest = max(owned.values(), key=lambda cohort: cohort.ownership_share)
        poorest = min(owned.values(), key=lambda cohort: cohort.ownership_share)
        self.assertGreater(richest.last_year_income / richest.people, poorest.last_year_income / poorest.people)

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


class CoinWorthTests(unittest.TestCase):
    """The metal a coin holds is worth what the last of the runs that make it costs (Complaint 473)."""

    def _setup(self, mine_runs):
        recipes = fixture.recipes()
        recipes[fixture.MINE] = dataclasses.replace(recipes[fixture.MINE], site_bound=True)
        recipes["scrap_metal"] = Recipe("scrap_metal", {fixture.METAL: 1.0}, {fixture.GRAIN: 1000.0}, {fixture.SMITH: 120.0})
        return fixture.small_setup(recipes=recipes, site_limits=(SiteLimit(fixture.MINE, fixture.HILLS, mine_runs, 1.0),))

    def _marginal(self, setup):
        from sim.economy import unit_cost
        record, _areas, _carriage = opening.open_economy(setup)
        smelt = setup.recipes[fixture.SMELT]
        cost_of = lambda recipe: (unit_cost.variable_cost_per_run(recipe, setup.opening_prices, setup.opening_wages)
                                  + unit_cost.capital_charge_per_run(recipe, setup.opening_prices, setup.opening_wages,
                                                                     setup.opening_rate)) / recipe.outputs[fixture.METAL]
        return opening_metal.marginal_cost(setup, record), cost_of(smelt), cost_of(setup.recipes["scrap_metal"])

    def test_where_the_cheap_way_supplies_all_the_metal_it_sets_the_cost(self):
        marginal, cheap, dear = self._marginal(self._setup(mine_runs=1.0e6))
        self.assertGreater(dear, cheap)
        self.assertAlmostEqual(marginal, cheap, delta=1e-6 * cheap)

    def test_where_a_deposit_cannot_feed_it_the_dearer_way_sets_the_cost(self):
        marginal, cheap, dear = self._marginal(self._setup(mine_runs=0.5))
        self.assertAlmostEqual(marginal, dear, delta=1e-6 * dear)
        self.assertGreater(marginal, cheap)


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


if __name__ == "__main__":
    unittest.main()
