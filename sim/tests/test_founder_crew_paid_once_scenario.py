"""Scenario (Complaint 640): the founder's crew is paid once, in a running game. The share rule on nodes is in
test_founder_crew_paid_once.py.

The founder's crew is paid once: a derived upkeep is staff pay plus plant wear, and the staff's pay is already in
the payroll (`labour.wage_bill`, part of `living_cost`), so the upkeep the founder is charged is the plant part."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.engine import node_upkeep


def founder_with_mixed_upkeep_running():
    game = sim(capital=1e9)
    node_id = next(node_id for node_id, node in sorted(game.nodes.items())
                   if node["up"] > 0.0 and "_upkeep_hours_parts" in node and game.is_venture(node_id)
                   and 0.1 < node_upkeep.non_labour_share(node) < 0.9
                   and node_id not in game.CAPABILITY_INSTITUTIONS and node_id not in game.SCALABLE_INSTITUTIONS)
    game.done.add(node_id)
    game.operating.add(node_id)
    game._done_changed()
    return game, node_id


class FounderCrewPaidOnceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game, cls.node_id = founder_with_mixed_upkeep_running()
        cls.node = cls.game.nodes[cls.node_id]

    def test_upkeep_leaves_out_the_crews_pay(self):
        expected = self.node["up"] * node_upkeep.non_labour_share(self.node)
        self.assertAlmostEqual(self.game.institution_upkeep(self.node_id), expected, places=6)
        self.assertLess(self.game.institution_upkeep(self.node_id), self.node["up"])

    def test_the_quote_a_screen_shows_is_what_the_year_charges(self):
        quote = self.game.venture_upkeep_quote(self.node_id)["now"]
        self.assertAlmostEqual(self.game.upkeep_by_concern()[self.node_id], quote, places=6)
        self.assertAlmostEqual(quote, self.game.institution_upkeep(self.node_id) * self.game.price_index, places=6)

    def test_a_node_with_no_stated_crew_keeps_its_whole_upkeep(self):
        node_id = next(node_id for node_id, node in sorted(self.game.nodes.items())
                       if node["up"] > 0.0 and "_upkeep_hours_parts" not in node and node.get("_upkeep_basis") != "staff"
                       and node_id not in self.game.CAPABILITY_INSTITUTIONS and node_id not in self.game.SCALABLE_INSTITUTIONS)
        self.assertAlmostEqual(self.game.institution_upkeep(node_id), self.game.nodes[node_id]["up"], places=6)


if __name__ == "__main__":
    unittest.main()
