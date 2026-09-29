"""Joint-process cost is split by demand-derived value, not by mass."""
import unittest

from sim import joint_allocation, simulator, solve_prices
from sim.world import demand


def joint_entry():
    return {"outputs": {"main_kg": 1000.0, "gem_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 100.0}}


class AllocateJointCostTests(unittest.TestCase):

    def test_without_anchors_the_split_is_unchanged(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0)
        self.assertAlmostEqual(prices["main_kg"], prices["gem_kg"])

    def test_an_anchored_minor_output_takes_a_demand_sized_share(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(
            outputs, {}, 100.0, {"gem_kg": 500.0})
        self.assertGreater(prices["gem_kg"], 100.0 * prices["main_kg"])
        recovered = sum(prices[name] * quantity for name, quantity in outputs.items())
        self.assertAlmostEqual(recovered, 100.0)

    def test_the_main_output_price_does_not_feed_back_into_its_own_share(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        cheap = joint_allocation.allocate_joint_cost(
            outputs, {"main_kg": 0.0001}, 100.0, {"gem_kg": 500.0})
        dear = joint_allocation.allocate_joint_cost(
            outputs, {"main_kg": 99.0}, 100.0, {"gem_kg": 500.0})
        self.assertAlmostEqual(cheap["main_kg"], dear["main_kg"])


class DemandAnchorsTests(unittest.TestCase):

    def anchors(self, supply_kg):
        bins = demand.income_bins(1_000_000.0, 500.0)
        basket = (demand.FOOD, demand.Good("gem_kg", 0.0, 0.70))
        return joint_allocation.DemandAnchors(bins, basket, {"gem_kg": supply_kg})

    def test_scarcer_supply_gives_a_higher_anchor(self):
        prices = {"wheat_kg": 0.5}
        scarce = self.anchors(10.0).prices(prices)["gem_kg"]
        plentiful = self.anchors(1000.0).prices(prices)["gem_kg"]
        self.assertGreater(scarce, plentiful)

    def test_a_good_with_no_known_supply_gets_no_anchor(self):
        anchors = joint_allocation.DemandAnchors(
            demand.income_bins(1_000_000.0, 500.0),
            (demand.FOOD, demand.Good("gem_kg", 0.0, 0.70)), {})
        self.assertEqual(anchors.prices({"wheat_kg": 0.5}), {})

    def test_a_custom_anchor_reaches_a_solved_joint_recipe(self):
        entries = {"smelt": joint_entry()}
        wages = {"labourer": 1.0}
        producers = solve_prices.build_producers_index(entries)
        resolvable = {"main_kg", "gem_kg"}
        # wheat is not solved here, so anchor prices come from a stub.
        anchors = self.anchors(50.0)
        anchors.prices = lambda _prices: {"gem_kg": 400.0}
        prices, _i, _r, _c = solve_prices.solve(
            entries, producers, resolvable, wages, demand_anchors=anchors)
        self.assertGreater(prices["gem_kg"], 100.0 * prices["main_kg"])


def solve_ungated(with_anchors):
    entries, _duplicates = solve_prices.load_production()
    _tree, prices_json, _nodes, _wages, _goods = simulator.load()
    wages = solve_prices.wage_ratios_by_trade(prices_json)
    producers = solve_prices.build_producers_index(entries)
    rent = solve_prices.rent_hours_per_kg_by_ore_material(entries, wages)
    resolvable = solve_prices.compute_resolvable_materials(
        entries, producers, rent_hours_per_kg_by_material=rent)
    anchors = joint_allocation.build_demand_anchors() if with_anchors else None
    prices, _i, _r, chosen = solve_prices.solve(
        entries, producers, resolvable, wages,
        rent_hours_per_kg_by_material=rent, demand_anchors=anchors)
    unanchored = solve_prices.minor_joint_byproducts_are_unanchored(
        entries, chosen, prices, wages, rent_hours_per_kg_by_material=rent,
        demand_anchors=anchors)
    return prices, unanchored


class RealDataJointSmeltTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.before, cls.unanchored_before = solve_ungated(False)
        cls.after, cls.unanchored_after = solve_ungated(True)

    def test_mass_split_prices_silver_like_lead(self):
        self.assertAlmostEqual(self.before["silver_kg"], self.before["lead_kg"], places=6)

    def test_silver_is_far_dearer_than_lead_per_kg_once_demand_is_used(self):
        self.assertGreater(self.after["silver_kg"], 50.0 * self.after["lead_kg"])

    def test_silver_is_no_longer_reported_as_unanchored(self):
        self.assertIn("silver_kg", self.unanchored_before)
        self.assertNotIn("silver_kg", self.unanchored_after)

    def test_byproducts_with_no_demand_curve_stay_flagged(self):
        for material in ("platinum_g", "germanium_g", "indium_g", "coal_tar_kg"):
            self.assertIn(material, self.unanchored_after)


if __name__ == "__main__":
    unittest.main()
