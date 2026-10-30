"""Complaint 640: the automatic opening of concerns over a stand-in: deep in arrears (past a share of the credit line) an
ordinary concern opens only when it pays for its own doors within the limit and an institution opens not at all; out of
arrears every concern is offered to open_venture. The payback and arrears rules are in test_affordability_and_credit."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import projects_host


def Opener(capital, credit_limit, nodes, done=()):
    """The projects module over a household with this purse and credit line; what it offers `open` is recorded."""
    module = projects_host.build(
        tree=nodes, acting_balance=capital, credit_limit=lambda *arguments: credit_limit,
        projects_record=types.SimpleNamespace(done=set(done), operating=set()), techniques_held=set(done), operating=lambda: set(),
        venture_capex=lambda node_id: nodes[node_id]["capex"], is_venture=lambda node_id: True,
        capability_sets=(frozenset({"school"}), frozenset(), {}))
    module.exclusion_reason = lambda node_id: None
    module.offered = []

    def open_venture(node_id, units=None):
        module.offered.append(node_id)
        return True, ""
    module._open_venture = open_venture
    return module


NODES = {"quick": {"rev": 500.0, "up": 100.0, "capex": 400.0},        # pays back in a year
         "slow": {"rev": 200.0, "up": 100.0, "capex": 1000.0},        # pays back in ten years
         "school": {"rev": 10.0, "up": 100.0, "capex": 50.0}}


class DeepArrears(unittest.TestCase):
    def test_past_half_the_line_is_deep_and_inside_it_is_not(self):
        self.assertTrue(Opener(-600.0, 1000.0, NODES)._auto_open_check_deep_arrears())
        self.assertFalse(Opener(-400.0, 1000.0, NODES)._auto_open_check_deep_arrears())
        self.assertFalse(Opener(500.0, 1000.0, NODES)._auto_open_check_deep_arrears())


class OrdinaryConcerns(unittest.TestCase):
    def test_deep_in_arrears_only_the_concern_that_pays_for_its_door_within_the_limit_is_offered(self):
        opener = Opener(-600.0, 1000.0, NODES)
        opened, blocked = opener._auto_open_ordinary_ventures(["quick", "slow"], True)
        self.assertEqual((opened, opener.offered), (["quick"], ["quick"]))
        self.assertEqual(blocked[0], "slow")

    def test_out_of_deep_arrears_every_concern_is_offered_whatever_its_payback(self):
        opener = Opener(-100.0, 1000.0, NODES)
        opened, blocked = opener._auto_open_ordinary_ventures(["quick", "slow"], False)
        self.assertEqual((opened, opener.offered, blocked), (["quick", "slow"], ["quick", "slow"], None))

    def test_a_refusal_by_open_venture_is_the_one_reported(self):
        opener = Opener(0.0, 1000.0, NODES)
        opener._open_venture = lambda node_id, units=None: (False, "no room")
        opened, blocked = opener._auto_open_ordinary_ventures(["quick", "slow"], False)
        self.assertEqual((opened, blocked), ([], ("quick", "no room")))


class Institutions(unittest.TestCase):
    def _candidates(self, deep):
        opener = Opener(0.0, 1000.0, NODES, done=["school", "quick"])
        return opener._auto_open_institution_candidates(deep)

    def test_an_institution_that_costs_more_than_it_brings_is_a_candidate_out_of_deep_arrears(self):
        self.assertEqual(self._candidates(False), ["school"])

    def test_nothing_is_a_candidate_deep_in_arrears(self):
        self.assertEqual(self._candidates(True), [])


if __name__ == "__main__":
    unittest.main()
