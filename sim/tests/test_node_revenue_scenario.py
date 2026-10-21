"""Scenario: a running game applies the market to an output-derived node and not to an authored one (the rule itself,
`output_market_factor`, is in test_node_factor_is_economy_over_cost)."""
import unittest


class SimMarketFactor(unittest.TestCase):

    def test_the_engine_applies_the_market_to_an_output_node_and_not_to_an_authored_one(self):
        import random
        from sim import simulator
        _tree, _prices, nodes, _wages, _goods = simulator.load()
        sim = simulator.Sim(nodes, [], random.Random(1), events=False, manual=True,
                            civ=simulator.load_civ("rome_100ad"))
        derived = next(node for node in nodes.values() if node.get("_revenue_basis") == "output")
        authored = next(node for node in nodes.values() if node.get("_revenue_basis") != "output")
        # an output node's factor comes from the market (zero when its purchases cost more than its output
        # sells for); an authored node's is exactly one
        self.assertEqual(sim.node_output_market_factor(authored), 1.0)
        factor = sim.node_output_market_factor(derived)
        self.assertTrue(0.0 <= factor < float("inf"), factor)


