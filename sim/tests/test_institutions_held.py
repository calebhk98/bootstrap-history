"""Complaint 106, Complaint 640: `held` hands the economy the institutions the home government's knowledge gives, none
without a government, and nothing for a mechanic no known node declares. The mechanic table is in
test_bank_institution_gate."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import api as economy_api
from sim.engine import agents_port, economy_port_institutions


class Government:
    def __init__(self, known):
        self.known = known

    def knows(self, node_id, world):
        return node_id in self.known


def game(government, nodes_by_mechanic):
    return types.SimpleNamespace(actors=types.SimpleNamespace(government_of=lambda actor: government),
                                 nodes_with_mechanic=lambda mechanic: nodes_by_mechanic.get(mechanic, []))


class Held(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.object(agents_port, "SimWorld", lambda sim: None)
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_government_that_knows_a_banking_node_gives_the_economy_deposit_banking_and_nothing_else(self):
        sim = game(Government({"fin_bank"}), {"deposit_banking": ["fin_bank"], "bond_market": ["fin_bonds"]})
        self.assertEqual(economy_port_institutions.held(sim), (economy_api.DEPOSIT_BANKING,))

    def test_a_government_that_knows_no_such_node_gives_none(self):
        sim = game(Government(set()), {"deposit_banking": ["fin_bank"]})
        self.assertEqual(economy_port_institutions.held(sim), ())

    def test_learning_the_node_adds_the_institution_and_removes_none(self):
        government = Government({"fin_risk"})
        nodes = {"deposit_banking": ["fin_bank"], "risk_pooling": ["fin_risk"]}
        before = economy_port_institutions.held(game(government, nodes))
        government.known.add("fin_bank")
        after = economy_port_institutions.held(game(government, nodes))
        self.assertEqual(set(after) - set(before), {economy_api.DEPOSIT_BANKING})
        self.assertLessEqual(set(before), set(after))

    def test_no_government_holds_no_institution(self):
        self.assertEqual(economy_port_institutions.held(game(None, {"deposit_banking": ["fin_bank"]})), ())


if __name__ == "__main__":
    unittest.main()
