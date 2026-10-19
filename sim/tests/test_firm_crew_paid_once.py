"""Complaint 514 open question 6: a firm's crew is paid once, as wages through the labour market.

A node's upkeep is derived as its staff's pay plus plant wear (`node_revenue._apply_output`). A firm that pays that
upkeep and also pays its crew wages paid the crew twice; the upkeep a firm pays is the non-labour part."""
import unittest

from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.engine.state import ActorRecord


def labour_share(node):
    parts = node["_upkeep_hours_parts"]
    return parts["staff"] / node["up_hours"]


def output_node_with_mixed_upkeep(game):
    """The first output-derived node whose upkeep is part crew pay and part something else."""
    for node_id, node in sorted(game.nodes.items()):
        parts = node.get("_upkeep_hours_parts")
        if parts and node.get("_revenue_basis") == "output" and node["up_hours"] > 0.0 and 0.1 < labour_share(node) < 0.9:
            return node_id
    raise AssertionError("no output node with a mixed upkeep")


def firm_running(game, node_id):
    year = game.state.scenario.year
    projects = game.state.projects
    projects.done.add(node_id)
    projects.done_year[node_id] = year - 5
    projects.operating.add(node_id)
    projects.business.set_opened_year(node_id, year - 5)
    game._done_changed()
    firm = game.actors.add("firm:crew_paid_once", ActorRecord(kind="firm", money=1.0e9, target=node_id))
    firm.business.open_plant(node_id, year - 5)
    firm.knowledge.add(node_id)
    return firm


class FirmCrewPaidOnceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = ready_for_entry(unopened_sim())
        cls.node_id = output_node_with_mixed_upkeep(cls.game)
        cls.node = cls.game.nodes[cls.node_id]
        cls.firm = firm_running(cls.game, cls.node_id)
        cls.world = SimWorld(cls.game)
        cls.quote = cls.world.upkeep(cls.node_id, cls.firm.capacity_of(cls.node_id))
        cls.wage_bill = cls.world.concern_wage_bill(cls.node_id, cls.firm.capacity_of(cls.node_id))
        cls.game.state.scenario.year += 1
        cls.game.advance_actors(cls.game.state.scenario.year)

    def test_upkeep_quote_leaves_out_the_crews_pay(self):
        scale = self.game.economy.cost_scale() * self.firm.capacity_of(self.node_id)
        self.assertAlmostEqual(self.quote, self.node["up"] * scale * (1.0 - labour_share(self.node)), places=6)

    def test_the_year_charges_upkeep_without_labour_and_wages_once(self):
        outlays = self.firm.record.outlays
        self.assertAlmostEqual(outlays.get("upkeep", 0.0), self.quote, places=6)
        self.assertGreater(outlays.get("wages", 0.0), 0.0)
        self.assertLessEqual(outlays["wages"], self.wage_bill * (1.0 + 1e-9))

    def test_a_node_whose_upkeep_has_no_stated_crew_keeps_its_whole_upkeep(self):
        node_id = next(node_id for node_id, node in sorted(self.game.nodes.items())
                       if node["up"] > 0.0 and "_upkeep_hours_parts" not in node)
        self.assertAlmostEqual(self.world.upkeep(node_id, 1.0), self.game.nodes[node_id]["up"] * self.game.economy.cost_scale())


if __name__ == "__main__":
    unittest.main()
