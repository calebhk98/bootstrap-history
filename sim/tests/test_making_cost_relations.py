"""The cost-of-making calculator (Complaints/507 stage 1): relationships, never dated values.

`cost_of_making` costs one good from the prices handed in; `long_run_costs` closes it over the recipe graph.
Neither reads a population, an income or a demand.
"""

QUICK_TOPIC = True

import unittest

from sim.engine import prices as price_engine
from sim.engine.long_run_costs import long_run_costs
from sim.engine.making_cost import cost_of_making

LABOURER = "labourer"
CAPITAL = [{"build_materials": {"steel_kg": 10.0}, "build_labour_hours": {LABOURER: 100.0},
            "service_life_years": 10.0, "annual_output_at_basis": 100.0}]


def entry(outputs, inputs=None, labour=None, requires_node=None, **fields):
    return dict({"outputs": outputs, "inputs": inputs or {}, "labour_hours": labour or {},
                 "requires_node": requires_node}, **fields)


def catalogue():
    return {
        "good_kg": entry({"good_kg": 1.0}, {"input_kg": 2.0}, {LABOURER: 3.0}),
        "batch_kg": entry({"batch_kg": 4.0}, {"input_kg": 2.0}, {LABOURER: 3.0}),
        "plant_kg": entry({"plant_kg": 1.0}, {"input_kg": 1.0}, {LABOURER: 1.0}, capital=CAPITAL),
        "rival_kg": entry({"rival_kg": 1.0}, {"input_kg": 5.0}, {LABOURER: 1.0}),
        "rival_better_kg": entry({"rival_kg": 1.0}, {"input_kg": 1.0}, {LABOURER: 1.0}, requires_node="better"),
        "ore_kg": entry({"ore_kg": 1.0}, labour={LABOURER: 1.0}),
        "smelt": entry({"main_kg": 9.0, "co_kg": 1.0}, {"ore_kg": 10.0}, {LABOURER: 10.0}),
        "input_kg": entry({"input_kg": 1.0}, labour={LABOURER: 1.0}),
        "steel_kg": entry({"steel_kg": 1.0}, labour={LABOURER: 1.0}),
    }


def cost(good, techniques=frozenset(), input_price=5.0, wage=10.0, rate=0.0, **arguments):
    return cost_of_making(
        good, techniques, arguments.pop("input_price_of", lambda material: input_price),
        arguments.pop("wage_of", lambda trade: wage), rate, production=catalogue(), **arguments)


class OneRecipeBillTests(unittest.TestCase):

    def test_a_good_made_one_way_costs_exactly_that_recipes_bill(self):
        made = cost("good_kg", input_price=5.0, wage=10.0)
        self.assertAlmostEqual(made.unit_cost, 2.0 * 5.0 + 3.0 * 10.0)
        self.assertEqual(made.recipe_id, "good_kg")

    def test_a_batch_is_shared_over_its_units(self):
        self.assertAlmostEqual(cost("batch_kg").unit_cost, cost("good_kg").unit_cost / 4.0)

    def test_the_shares_add_up_to_the_cost(self):
        made = cost("good_kg")
        self.assertAlmostEqual(sum(made.input_cost.values()) + sum(made.trade_cost.values()) + made.plant_cost
                               + made.rent_cost + made.energy_cost + made.holding_cost, made.unit_cost)
        self.assertAlmostEqual(made.input_cost["input_kg"], 10.0)
        self.assertAlmostEqual(made.trade_cost[LABOURER], 30.0)

    def test_an_input_with_no_price_leaves_the_good_with_no_cost(self):
        self.assertIsNone(cost("good_kg", input_price_of=lambda material: None))

    def test_a_good_nothing_makes_has_no_cost(self):
        self.assertIsNone(cost("nothing_kg"))


class MonotoneTests(unittest.TestCase):

    def test_cost_rises_with_each_input_price(self):
        self.assertGreater(cost("good_kg", input_price=6.0).unit_cost, cost("good_kg", input_price=5.0).unit_cost)

    def test_cost_rises_with_the_wage(self):
        self.assertGreater(cost("good_kg", wage=11.0).unit_cost, cost("good_kg", wage=10.0).unit_cost)

    def test_the_plant_charge_rises_with_the_rate(self):
        low = cost("plant_kg", rate=0.02)
        high = cost("plant_kg", rate=0.10)
        self.assertGreater(high.plant_cost, low.plant_cost)
        self.assertGreater(high.unit_cost, low.unit_cost)

    def test_a_built_plant_costs_less_to_run_than_to_build(self):
        full = cost("plant_kg", rate=0.05)
        running = cost("plant_kg", rate=0.05, include_plant=False)
        self.assertEqual(running.plant_cost, 0.0)
        self.assertAlmostEqual(full.unit_cost - full.plant_cost, running.unit_cost)

    def test_holding_a_cheaper_technique_lowers_the_cost(self):
        before = cost("rival_kg")
        after = cost("rival_kg", techniques=frozenset({"better"}))
        self.assertLess(after.unit_cost, before.unit_cost)
        self.assertEqual(before.recipe_id, "rival_kg")
        self.assertEqual(after.recipe_id, "rival_better_kg")

    def test_a_technique_not_held_is_not_used(self):
        self.assertEqual(cost("rival_kg", techniques=frozenset({"unrelated"})).recipe_id, "rival_kg")


class RentTests(unittest.TestCase):

    def test_no_rent_function_means_no_rent_is_charged(self):
        self.assertEqual(cost("ore_kg").rent_cost, 0.0)

    def test_rent_on_an_extracted_good_is_added_per_unit(self):
        free = cost("ore_kg")
        rented = cost("ore_kg", rent_of=lambda key: 4.0 if key == "ore_kg" else 0.0)
        self.assertAlmostEqual(rented.rent_cost, 4.0)
        self.assertAlmostEqual(rented.unit_cost - free.unit_cost, 4.0)


class JointRunTests(unittest.TestCase):

    def split(self, reference_prices):
        return {good: cost(good, reference_price_of=reference_prices.get) for good in ("main_kg", "co_kg")}

    def test_the_outputs_together_recover_the_runs_cost(self):
        batch = 10.0 * 5.0 + 10.0 * 10.0
        for reference_prices in ({"main_kg": 1.0, "co_kg": 10.0}, {"main_kg": 3.0, "co_kg": 0.1}, {}):
            made = self.split(reference_prices)
            recovered = 9.0 * made["main_kg"].unit_cost + 1.0 * made["co_kg"].unit_cost
            self.assertAlmostEqual(recovered, batch, msg=str(reference_prices))

    def test_the_split_follows_the_reference_values(self):
        made = self.split({"main_kg": 1.0, "co_kg": 18.0})
        # worth 18 against 9, so the co-product carries twice the main product's share of the run
        self.assertAlmostEqual(made["co_kg"].unit_cost * 1.0, 2.0 * made["main_kg"].unit_cost * 9.0)

    def test_a_dearer_reference_price_moves_cost_onto_that_output(self):
        low = self.split({"main_kg": 1.0, "co_kg": 2.0})
        high = self.split({"main_kg": 1.0, "co_kg": 20.0})
        self.assertGreater(high["co_kg"].unit_cost, low["co_kg"].unit_cost)
        self.assertLess(high["main_kg"].unit_cost, low["main_kg"].unit_cost)

    def test_with_no_reference_the_split_is_by_mass(self):
        made = self.split({})
        self.assertAlmostEqual(made["main_kg"].unit_cost, made["co_kg"].unit_cost)


class LongRunTests(unittest.TestCase):

    def table(self, wage=10.0, rate=0.0, techniques=frozenset(), rent_of=None):
        return long_run_costs(techniques, lambda trade: wage, rate, rent_of, production=catalogue())

    def test_a_good_costs_its_inputs_long_run_cost_plus_its_labour(self):
        table = self.table(wage=10.0)
        self.assertAlmostEqual(table["input_kg"].cost, 10.0)
        self.assertAlmostEqual(table["good_kg"].cost, 2.0 * 10.0 + 30.0)

    def test_the_whole_table_rises_with_the_wage(self):
        low, high = self.table(wage=10.0), self.table(wage=12.0)
        for good in low:
            if low[good].cost > 0.0:
                self.assertGreater(high[good].cost, low[good].cost, good)

    def test_the_plant_charge_rises_with_the_rate(self):
        self.assertGreater(self.table(rate=0.1)["plant_kg"].cost, self.table(rate=0.01)["plant_kg"].cost)

    def test_a_held_technique_lowers_what_it_makes(self):
        before = self.table()["rival_kg"]
        after = self.table(techniques=frozenset({"better"}))["rival_kg"]
        self.assertLess(after.cost, before.cost)
        self.assertEqual(after.recipe_id, "rival_better_kg")

    def test_rent_is_charged_only_when_supplied(self):
        self.assertAlmostEqual(
            self.table(rent_of=lambda key: 7.0 if key == "ore_kg" else 0.0)["ore_kg"].cost
            - self.table()["ore_kg"].cost, 7.0)

    def test_a_joint_runs_outputs_recover_its_cost(self):
        table = self.table()
        recovered = 9.0 * table["main_kg"].cost + 1.0 * table["co_kg"].cost
        self.assertAlmostEqual(recovered, 10.0 * table["ore_kg"].cost + 100.0)


class RealDataTests(unittest.TestCase):
    """The long-run table is a fixed point of the one-step calculator."""

    @classmethod
    def setUpClass(cls):
        from sim import simulator
        from sim.engine.data import load_civ
        cls.civilization = load_civ("rome_100ad")
        cls.held = frozenset(cls.civilization["starting_techs"])
        _tree, cls.wage_document, _nodes, _wages, _goods = simulator.load()
        ratios = price_engine.solve_prices.wage_ratios_by_trade(cls.wage_document)
        cls.wage_of = staticmethod(lambda trade: ratios.get(trade, 1.0))
        cls.rate = float(cls.civilization["starting_interest_rate"])
        cls.table = long_run_costs(cls.held, cls.wage_of, cls.rate, None, civilization=cls.civilization)

    def test_the_table_is_not_empty_and_costs_are_positive_for_made_goods(self):
        self.assertGreater(len(self.table), 50)
        self.assertGreater(self.table["wheat_kg"].cost, 0.0)

    def test_one_step_at_the_tables_own_prices_returns_the_table(self):
        def input_price(material):
            record = self.table.get(material)
            return None if record is None else record.cost
        checked = 0
        for good, record in sorted(self.table.items()):
            if record.provenance != "solved" or record.recipe_id not in price_engine.default_production_entries():
                continue
            if len(price_engine.default_production_entries()[record.recipe_id]["outputs"]) != 1:
                continue
            once = cost_of_making(good, self.held, input_price, self.wage_of, self.rate,
                                  civilization=self.civilization)
            self.assertIsNotNone(once, good)
            self.assertAlmostEqual(once.unit_cost, record.cost, delta=1e-3 * max(abs(record.cost), 1e-6), msg=good)
            checked += 1
            if checked >= 25:
                break
        self.assertGreater(checked, 10)

    def test_cost_does_not_depend_on_population(self):
        smaller = dict(self.civilization, population=self.civilization["population"] / 10.0)
        table = long_run_costs(self.held, self.wage_of, self.rate, None, civilization=smaller)
        for good in ("wheat_kg", "pig_iron_kg", "bread_kg"):
            if good in self.table:
                self.assertAlmostEqual(table[good].cost, self.table[good].cost, places=9, msg=good)


if __name__ == "__main__":
    unittest.main()
