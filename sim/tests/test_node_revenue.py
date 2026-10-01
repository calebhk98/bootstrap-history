"""Node revenue follows solved costs: declared output sells at solved prices,
and authored revenue is held under the payback floor."""
import unittest

from sim.engine import data, node_revenue


class NodeRevenue(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour

    def test_no_node_repays_its_cost_faster_than_the_floor(self):
        for node_id, node in self.nodes.items():
            if node["rev"] > 0 and node["_total_cost"] > 0:
                self.assertGreaterEqual(
                    node["_total_cost"] / node["rev"], node_revenue.MINIMUM_PAYBACK_YEARS - 1e-6, node_id)

    def test_declared_output_sells_at_solved_prices(self):
        from sim.engine.actors.supply import materials_made_by
        checked = 0
        for node_id, node in self.nodes.items():
            made = [m for m in materials_made_by(node_id) if m in self.goods]
            if node.get("annual_output_t") and made:
                expected = sum(node["annual_output_t"] * 1000.0 / len(made) * self.goods[m]
                               for m in made) / self.rate
                self.assertAlmostEqual(node["rev_hours"], expected, delta=expected * 1e-9, msg=node_id)
                checked += 1
        self.assertGreater(checked, 0)

    def test_authored_revenue_is_kept_where_it_is_below_the_cap(self):
        kept = [n for n in self.nodes.values()
                if n["rev_hours"] > 0 and n["rev_hours"] == n["_rev_hours_authored"]]
        self.assertGreater(len(kept), 100)


if __name__ == "__main__":
    unittest.main()
