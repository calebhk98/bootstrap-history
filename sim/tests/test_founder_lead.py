"""What the founder completes is not the society's until the society's own actors learn it.

The derived revenue of every node is worked out at the technologies the society holds. The founder's
completed nodes (`done`) are not the society's: a firm or the government holds one only once it has copied
or been licensed it (agents/imitation.py, `disclose`). Until then the founder's technique earns at prices
the society's techniques set, which is the lead."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import node_rederive, node_revenue, society_holdings


def actor(kind, knowledge, exited=None):
    record = types.SimpleNamespace(exited_year=exited)
    return types.SimpleNamespace(kind=kind, knowledge=set(knowledge), record=record)


class HeldBySociety(unittest.TestCase):

    def test_the_society_holds_its_own_techniques_and_what_its_actors_have_learnt(self):
        held = society_holdings.held_by_society({"fire"}, [actor("firm", {"loom"}), actor("government", {"coin"})])
        self.assertEqual(held, {"fire", "loom", "coin"})

    def test_a_node_only_the_founder_holds_is_not_the_societys(self):
        self.assertEqual(society_holdings.held_by_society({"fire"}, []), {"fire"})

    def test_households_bodies_and_exited_firms_do_not_count(self):
        held = society_holdings.held_by_society(
            {"fire"}, [actor("household", {"steam"}), actor("interest_group", {"guild"}), actor("firm", {"kiln"}, exited=1700)])
        self.assertEqual(held, {"fire"})


class Rederivation(unittest.TestCase):

    def test_revenue_is_rederived_at_the_societys_techniques_not_the_founders(self):
        seen = []
        projects = types.SimpleNamespace(done={"fire", "steam"}, granted={"fire"})
        fake = types.SimpleNamespace(
            state=types.SimpleNamespace(projects=projects), nodes={}, start_civ={"id": "x"}, _derived_gate_set=frozenset(),
            _society_held_techs=lambda: frozenset({"fire"}),
            _done_changed=lambda: None, _operating_changed=lambda: None)
        schedule = types.SimpleNamespace(wages_per_hour=lambda: {}, money_per_labour_hour=1.0)
        with mock.patch.object(node_revenue, "for_civilisation",
                               lambda nodes, civ, schedule, held_techs=None: seen.append(set(held_techs)) or {}), \
                mock.patch.object(node_rederive, "held_gate_set", lambda held: frozenset(held)), \
                mock.patch.object(node_rederive, "build_schedule", lambda *arguments: schedule), \
                mock.patch.object(node_rederive.money_units, "price_nodes", lambda *arguments: None):
            node_rederive.NodeRederiveMixin.refresh_derived_nodes(fake)
        self.assertEqual(seen, [{"fire"}])


if __name__ == "__main__":
    unittest.main()
