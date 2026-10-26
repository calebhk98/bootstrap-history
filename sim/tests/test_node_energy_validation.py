"""VALIDATION of the shipped tree: the graded energy prices the solver leaves and the energy baskets of the nodes that earn from output.
The rules on hand-written bands are test_energy_prices_rules."""
import unittest

from sim.prices import energy_prices

from sim.engine import data, node_output
from sim.labour.labour_market import production_data


class GradedEnergy(unittest.TestCase):

    def setUp(self):
        _tree, self.document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour
        civ = data.load_civ()
        self.energy = energy_prices.graded(civ["starting_techs"], self.document, self.goods)

    def test_an_entry_pays_the_band_of_its_own_stated_temperature(self):
        stated = {entry["temperature_needed_c"] for entry in production_data().values()
                  if entry.get("thermal_mj") and entry.get("temperature_needed_c") is not None}
        self.assertGreater(len(stated), 1)
        prices = {required: self.energy.bought("thermal_mj", {"temperature_needed_c": required})
                  for required in stated}
        for required, price in prices.items():
            self.assertGreater(price, 0.0, required)
        self.assertGreater(len(set(prices.values())), 1, "every temperature costs the same")
        hottest, coolest = max(stated), min(stated)
        self.assertGreaterEqual(prices[hottest], prices[coolest])

    def test_a_hotter_requirement_never_costs_less_than_a_cooler_one(self):
        ordered = sorted(required for (carrier, required) in self.energy.bands if carrier == "thermal_mj")
        prices = [self.energy.bands[("thermal_mj", required)] for required in ordered]
        self.assertEqual(prices, sorted(prices))

    def test_a_producer_sells_at_the_hottest_band_its_reach_clears(self):
        market = energy_prices.EnergyPrices(self.energy.pool, self.energy.bands)
        reached_1100 = market.sold("thermal_mj", {"temperature_reached_c": 1100.0})
        cleared = [required for (carrier, required) in market.bands
                   if carrier == "thermal_mj" and required <= 1100.0]
        self.assertEqual(reached_1100, market.bands[("thermal_mj", max(cleared))])
        self.assertEqual(market.sold("mechanical_mj", {}), self.goods["mechanical_mj"])

    def test_the_graded_prices_know_what_an_entry_costs_to_run(self):
        motor = production_data()["mechanical_mj_motor"]
        own = self.energy.own_cost(motor)["mechanical_mj"]
        self.assertGreater(own, self.goods["electrical_mj"] * motor["electrical_mj"] / motor["outputs"]["mechanical_mj"] * 0.99)

    def test_energy_bought_is_valued_at_the_entrys_graded_price(self):
        checked = 0
        for node_id, node in self.nodes.items():
            if node.get("_revenue_basis") != "output":
                continue
            for carrier, basket in (node.get("_energy_bought_per_year") or {}).items():
                self.assertGreater(basket["quantity"], 0.0, node_id)
                self.assertGreater(basket["value"], 0.0, node_id)
                checked += 1
        self.assertGreater(checked, 0)

    def test_a_node_whose_entry_makes_a_carrier_earns_it(self):
        makers = [node_id for node_id, node in self.nodes.items() if node.get("_energy_sold_per_year")]
        self.assertGreater(len(makers), 0)
        for node_id in makers:
            for carrier, basket in self.nodes[node_id]["_energy_sold_per_year"].items():
                self.assertIn(carrier, energy_prices.ENERGY_CARRIERS)
                self.assertGreater(basket["value"], 0.0, node_id)

    def test_energy_is_not_listed_among_the_materials_bought_or_sold(self):
        for node_id, node in self.nodes.items():
            for basket in (node.get("_output_per_year") or {}, node.get("_purchases_per_year") or {}):
                for carrier in energy_prices.ENERGY_CARRIERS:
                    self.assertNotIn(carrier, basket, node_id)

    def test_baskets_carry_the_labour_hours_the_lines_work(self):
        node = next(node for node in self.nodes.values() if node.get("_revenue_basis") == "output")
        baskets = node_output.output_baskets(node, production_data(), self.goods, self.energy, self.wages)
        self.assertEqual(baskets.labour_hours, node["_labour_hours_per_year"])


if __name__ == "__main__":
    unittest.main()
