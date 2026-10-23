"""Complaint 640: the automatic opening of concerns over a stand-in: deep in arrears (past a share of the credit line) an
ordinary concern opens only when it pays for its own doors within the limit and an institution opens not at all; out of
arrears every concern is offered to open_venture. The payback and arrears rules are in test_affordability_and_credit."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.projects_staffing import StaffingMixin


class Opener(StaffingMixin):
    LIMIT_YEARS = 3.0

    def __init__(self, capital, credit_limit, nodes, done=()):
        self.AUTO_OPEN_PAYBACK_LIMIT_YEARS = self.LIMIT_YEARS
        self.nodes = nodes
        self._limit = credit_limit
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(capital=capital),
            projects=types.SimpleNamespace(done=set(done), operating=set()))
        self.offered = []

    def credit_limit(self):
        return self._limit

    def venture_capex(self, node_id):
        return self.nodes[node_id]["capex"]

    def is_venture(self, node_id):
        return True

    def exclusion_reason(self, node_id):
        return None

    def open_venture(self, node_id, units=None):
        self.offered.append(node_id)
        return True, ""


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
        opener.open_venture = lambda node_id, units=None: (False, "no room")
        opened, blocked = opener._auto_open_ordinary_ventures(["quick", "slow"], False)
        self.assertEqual((opened, blocked), ([], ("quick", "no room")))


class Institutions(unittest.TestCase):
    def _candidates(self, deep):
        opener = Opener(0.0, 1000.0, NODES, done=["school", "quick"])
        opener.CAPABILITY_INSTITUTIONS = {"school"}
        return opener._auto_open_institution_candidates(deep)

    def test_an_institution_that_costs_more_than_it_brings_is_a_candidate_out_of_deep_arrears(self):
        self.assertEqual(self._candidates(False), ["school"])

    def test_nothing_is_a_candidate_deep_in_arrears(self):
        self.assertEqual(self._candidates(True), [])


if __name__ == "__main__":
    unittest.main()
