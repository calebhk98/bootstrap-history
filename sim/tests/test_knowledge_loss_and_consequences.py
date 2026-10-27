"""Complaint 233/237: a rebuild keeps what survives, derived from state: a dispersed copy of the record, people who still
practise the node's trades, and plant built on it. Called on the projects module over a society's facts; the effect on a game's
cost and the failure, effect, benefit, patron and succession readouts are in `test_knowledge_loss_and_consequences_scenario`."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.knowledge.api import CORPUS_HEDGE_LOSS_CHANCE_NONE
from sim.projects.constants import REBUILD_RETAINED_CEILING
from sim.tests import projects_host

NODE = "furnace"
NONE_CHANCE = CORPUS_HEDGE_LOSS_CHANCE_NONE   # the corpus hedge's loss chance with no copy dispersed


def Society(forgotten=True, hedge_chance=NONE_CHANCE, practitioners=(), dependents_done=0, dependents=4):
    """The projects module over a society holding a forgotten node, with the survivors given."""
    nodes = {NODE: {"pre": [], "lab": {"smith": 1.0, "miner": 1.0}}}
    done = set()
    for index in range(dependents):
        dependent = "dependent_%d" % index
        nodes[dependent] = {"pre": [NODE], "lab": {}}
        if index < dependents_done:
            done.add(dependent)
    return projects_host.build(
        tree=nodes, techniques_held=done, legacy_projects=SimpleNamespace(done=done, active={}),
        techniques_forgotten={NODE: 100} if forgotten else {}, corpus_hedge=(hedge_chance, None, None),
        staff={"employees": {trade: 5.0 for trade in practitioners}})


class RebuildRetainedShare(unittest.TestCase):

    def test_a_node_never_lost_keeps_nothing(self):
        self.assertEqual(Society(forgotten=False, hedge_chance=0.0, practitioners=("smith",)).rebuild_retained_share(NODE), 0.0)

    def test_a_forgotten_node_with_nothing_surviving_keeps_nothing_so_it_costs_a_first_build(self):
        self.assertEqual(Society().rebuild_retained_share(NODE), 0.0)

    def test_a_dispersed_copy_of_the_record_keeps_a_share(self):
        self.assertGreater(Society(hedge_chance=0.1).rebuild_retained_share(NODE), 0.0)

    def test_a_better_hedged_record_keeps_more(self):
        self.assertGreater(Society(hedge_chance=0.05).rebuild_retained_share(NODE),
                           Society(hedge_chance=0.25).rebuild_retained_share(NODE))

    def test_living_practitioners_of_the_nodes_trades_keep_more_of_it(self):
        bare = Society(hedge_chance=0.1).rebuild_retained_share(NODE)
        half = Society(hedge_chance=0.1, practitioners=("smith",)).rebuild_retained_share(NODE)
        all_trades = Society(hedge_chance=0.1, practitioners=("smith", "miner")).rebuild_retained_share(NODE)
        self.assertLess(bare, half)
        self.assertLess(half, all_trades)

    def test_surviving_plant_built_on_it_keeps_more_of_it(self):
        self.assertGreater(Society(dependents_done=2).rebuild_retained_share(NODE), Society().rebuild_retained_share(NODE))

    def test_everything_surviving_keeps_the_ceiling_and_never_more(self):
        full = Society(hedge_chance=0.0, practitioners=("smith", "miner"), dependents_done=4)
        self.assertAlmostEqual(full.rebuild_retained_share(NODE), REBUILD_RETAINED_CEILING)

    def test_the_work_left_is_what_the_rebuild_does_not_keep(self):
        society = Society(hedge_chance=0.1, practitioners=("smith",))
        self.assertAlmostEqual(society.rebuild_work_factor(NODE), 1.0 - society.rebuild_retained_share(NODE))


if __name__ == "__main__":
    unittest.main()
