"""Scenario: a saved game keeps the derived figures of the techniques its society held (Complaints/317). The rule
that research changes the figures is in test_node_revenue_follows_research."""
import os
import random
import tempfile
import unittest

from sim import simulator
from sim.engine import prices
from sim.engine.saveload import load_state, save_state
from sim.tests.harness import build_unopened

CIVILISATION = "rome_100ad"


def make_sim():
    _tree, _prices, nodes, _wages, _goods = simulator.load()
    sim = build_unopened(lambda: simulator.Sim(nodes, [], random.Random(1), events=False, manual=True,
                                               civ=simulator.load_civ(CIVILISATION)))
    sim.goal, sim.done_year = sorted(nodes)[0], {}
    return sim


def figures(sim):
    return {node_id: node.get("rev_hours") for node_id, node in sim.nodes.items()}


class SavedFigures(unittest.TestCase):

    def test_a_loaded_save_has_the_figures_of_the_techniques_it_holds(self):
        sim = make_sim()
        learned = sorted(prices.all_gate_nodes() - set(sim.state.projects.done))
        sim.state_treasury().knowledge.update(learned)
        sim.refresh_derived_nodes()
        after = figures(sim)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "game.json")
            save_state(sim, path)
            revived = make_sim()
            load_state(revived, path)
        self.assertEqual(figures(revived), after)


if __name__ == "__main__":
    unittest.main()
