"""Builds a whole game (slow, so not in the quick tier; not run where a game takes long to build)."""
import unittest


class WholeGame(unittest.TestCase):
    """Builds a whole game (slow, so not in the quick tier): the society's output of a made material is its
    producers' capacity, independent of price."""

    def test_a_made_materials_national_output_is_what_its_producers_can_make(self):
        import random
        from sim import simulator
        _tree, _prices, nodes, _wages, _goods = simulator.load()
        sim = simulator.Sim(nodes, [], random.Random(1), events=False, manual=True,
                            civ=simulator.load_civ("rome_100ad"))
        agent = sim.economy.agent
        self.assertIsNotNone(agent)
        generic = next(good for recipe in agent._economy.setup.recipes.values() for good in recipe.outputs
                       if good not in sim.res["empire_output_100ad"] and good not in sim._commodity_ledger().commodities
                       and sim.producer_capacity_tonnes(good) > 0.0)
        before = sim._national_output_tonnes(generic)
        self.assertAlmostEqual(before, sim.producer_capacity_tonnes(generic)
                               + sum(row["rate_tonnes_per_year"] for row in sim.found_deposits(generic)))
        sim.price_index *= 2.0
        sim._done_memo_store = None
        self.assertAlmostEqual(sim._national_output_tonnes(generic), before)


if __name__ == "__main__":
    unittest.main()
