"""A long-run price repays the plant at the market rate, so a concern selling at it earns a return.

The solver charges each production entry's plant its build bill over its service life; Complaints/319
found that left a concern priced at cost earning its staff and nothing above. The charge now repays the
build bill with interest at the civilisation's market rate (`capital_recovery_factor`), so a concern
selling at the solved price earns its wages plus that return."""
import unittest
from unittest import mock

from sim import solve_prices
from sim.engine import data, energy_prices, node_output, node_revenue
from sim.world import capital_market
from sim.world.labour_market import production_data

# Entries that state a plant and gate a node, whose inputs at solved prices cost more than what they
# make: a technique dearer than the one that sets the price, so it adds nothing a staff could be paid from.
INPUTS_DEARER_THAN_PRODUCT = {"mechanical_mj_motor", "zinc_electrolytic_kg"}

WAGES = {"labourer": 1.0}
BUILD_LABOUR_HOURS = 20000.0
LIFE_YEARS = 20.0
PLANT_OUTPUT_PER_YEAR = 1000.0


def works_entry():
    return {"outputs": {"widget_kg": 10.0}, "inputs": {"ore_kg": 10.0}, "labour_hours": {"labourer": 5.0},
            "requires_node": "widget_works",
            "capital": [{"good": "pan", "build_labour_hours": {"labourer": BUILD_LABOUR_HOURS},
                         "service_life_years": LIFE_YEARS, "annual_output_at_basis": PLANT_OUTPUT_PER_YEAR}]}


def unit_price(rate):
    _cost, prices = solve_prices.recipe_cost_and_allocation(
        "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=rate)
    return prices["widget_kg"]


class CapitalRecoveryFactor(unittest.TestCase):

    def test_a_nil_rate_is_depreciation_alone(self):
        self.assertAlmostEqual(capital_market.capital_recovery_factor(0.0, 20.0), 1.0 / 20.0)

    def test_the_yearly_share_repays_the_bill_with_interest_on_what_is_unpaid(self):
        rate, life = 0.12, 25.0
        share = capital_market.capital_recovery_factor(rate, life)
        owed = 1.0
        for _year in range(int(life)):
            owed = owed * (1.0 + rate) - share
        self.assertAlmostEqual(owed, 0.0, places=9)

    def test_a_dearer_rate_asks_more_of_the_same_plant(self):
        self.assertGreater(capital_market.capital_recovery_factor(0.2, 20.0),
                           capital_market.capital_recovery_factor(0.1, 20.0))


class SolvedPriceCarriesTheReturn(unittest.TestCase):

    def test_the_price_covers_materials_labour_and_the_plants_repayment_at_the_market_rate(self):
        rate = 0.12
        share = capital_market.capital_recovery_factor(rate, LIFE_YEARS)
        batch_cost = 10.0 * 1.0 + 5.0 * 1.0
        plant_per_unit = BUILD_LABOUR_HOURS * share / PLANT_OUTPUT_PER_YEAR
        self.assertAlmostEqual(unit_price(rate), batch_cost / 10.0 + plant_per_unit)

    def test_a_dearer_market_rate_raises_the_price_of_what_a_plant_makes(self):
        self.assertGreater(unit_price(0.2), unit_price(0.1))
        self.assertGreater(unit_price(0.1), unit_price(0.0))

    def test_an_entry_with_no_plant_is_unmoved_by_the_rate(self):
        entry = works_entry()
        entry["capital"] = []
        prices = [solve_prices.recipe_cost_and_allocation("widget_kg", entry, {"ore_kg": 1.0}, WAGES,
                                                          interest_rate=rate)[1]["widget_kg"]
                  for rate in (0.0, 0.3)]
        self.assertAlmostEqual(prices[0], prices[1])


class ConcernEarnsItsReturn(unittest.TestCase):

    def earnings(self, rate):
        """(revenue less staff, build hours of its plant) of a concern selling at its solved price."""
        node = {"id": "widget_works", "kind": "ENGINEERING", "rev_hours": 1.0, "up_hours": 1.0, "sch": 0.0,
                "art": 0.0, "annual_output_t": 0.0}
        goods = {"ore_kg": 1.0, "widget_kg": unit_price(rate)}
        table = {"widget_works_entry": works_entry()}
        with mock.patch("sim.world.labour_market.production_data", return_value=table):
            node_revenue.apply_revenue([node], goods, WAGES, 1.0, energy_prices.pool_only(goods))
        self.assertEqual(node["_revenue_basis"], "output")
        staff = node["_upkeep_hours_parts"]["staff"]
        return node["rev_hours"] - staff, node["_upkeep_hours_parts"]["plant_build_hours"]

    def test_a_concern_priced_at_its_solved_cost_earns_wages_plus_a_return_on_its_plant(self):
        rate = 0.12
        # no staff is held, so the plant bounds the output: the whole plant runs
        surplus, build_hours = self.earnings(rate)
        self.assertGreaterEqual(surplus, build_hours * rate * (1 - 1e-9))

    def test_with_no_return_charged_a_concern_earns_less_than_with_it(self):
        self.assertLess(self.earnings(0.0)[0], self.earnings(0.12)[0])

    def test_the_surplus_repays_what_the_plant_wears_and_then_some(self):
        surplus, build_hours = self.earnings(0.12)
        self.assertGreater(surplus, build_hours / LIFE_YEARS)


class MakersWithAStatedPlant(unittest.TestCase):

    def test_a_maker_with_a_stated_plant_adds_its_staff_cost_at_its_solved_price(self):
        _tree, document, _nodes, wages, goods = data.load()
        civ = data.load_civ()
        energy = energy_prices.graded(civ["starting_techs"], document, goods, civ["id"])
        short = set()
        for key, entry in production_data().items():
            if not (entry.get("requires_node") and entry.get("capital") and entry.get("outputs")):
                continue
            if any(material not in goods for material in entry["outputs"]):
                continue
            staff = sum(wages.get(trade, 0.0) * hours for trade, hours in (entry.get("labour_hours") or {}).items())
            if node_output._net_per_batch(entry, goods, energy) < staff * (1 - 1e-9):
                short.add(key)
        self.assertLessEqual(short, INPUTS_DEARER_THAN_PRODUCT, "adds less than its staff: %s" % sorted(short))
        self.assertFalse(INPUTS_DEARER_THAN_PRODUCT - short,
                         "now adds its staff cost, remove from the list: %s" % sorted(INPUTS_DEARER_THAN_PRODUCT - short))


if __name__ == "__main__":
    unittest.main()
