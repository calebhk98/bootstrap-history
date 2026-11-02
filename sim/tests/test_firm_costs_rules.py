"""Complaints 345 and 341: a concern's running costs and takings are its own (no index of the economy's output scales
either) and the founder and an actor are quoted the same upkeep for the same concern. Rules: `node_upkeep.non_labour_upkeep_money`,
`EconomyPort.concern_upkeep` against the production module's `institution_upkeep` (the founder's). That pay follows output per head by a share is test_concern_volume; the one
wage for every employer is test_one_labour_market_wiring."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.production import node_upkeep
from sim.markets.port import EconomyPort
from sim.tests import production_host, ventures_host

NODE = {"up": 5000.0, "_upkeep_hours_parts": {"staff": 3.0, "plant": 1.0}, "_upkeep_basis": None}   # a quarter of the upkeep is not crew


class Founder:
    """The founder's side of a plain concern: no scalable institution, no capability gate."""

    def __init__(self, price_index):
        nodes = {"shop": NODE}
        self.production = production_host.build(tree_nodes=nodes, price_index=price_index, capability_sets=((), (), {}))
        self.ventures = ventures_host.build(
            tree_nodes=nodes, price_index=price_index, institution_upkeep=self.production.institution_upkeep)

    def venture_real_upkeep(self, node_id):
        return self.ventures.venture_real_upkeep(node_id)


class UpkeepTests(unittest.TestCase):
    def test_upkeep_is_the_stated_figure_times_the_non_crew_share_the_scale_and_the_capacity(self):
        self.assertAlmostEqual(node_upkeep.non_labour_upkeep_money(5000.0, NODE, 2.0, 1.5), 5000.0 * 0.25 * 1.5 * 2.0)

    def test_an_actors_concern_upkeep_is_the_non_crew_part_at_the_price_level(self):
        port = EconomyPort(SimpleNamespace(nodes={"shop": NODE}, price_index=1.7))
        self.assertAlmostEqual(port.concern_upkeep("shop"), 5000.0 * 0.25 * 1.7)

    def test_the_founders_quote_of_the_same_concern_is_the_non_crew_part_at_the_price_level(self):
        self.assertAlmostEqual(Founder(1.7).venture_real_upkeep("shop"), 5000.0 * 0.25 * 1.7)


if __name__ == "__main__":
    unittest.main()
