"""Complaints/34: buying SCHOLAR hours bought nothing.

Buying labourer hours worked. Commissioning a scholar took the money,
confirmed the purchase, and left the project gate refusing in exactly the
same words - because `start_reason` tested the standing HEADCOUNT
(`effective_scholars`) rather than the hands actually available.

It is the same defect `craft_hands_available` was written to fix, and that
function's own comment records what it cost: a Norse run ended six hundred
years in with 136 technologies and 1.6 craftsmen, unable to build the
workshop that craftsmen work in because it needs two. Nobody extended the
fix to scholars, so the identical bug survived for them until a player hit
it and reported it.

unittest.TestCase style, like the other focused complaint suites.
"""
import os
import random
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)
from sim import simulator
from sim.engine.core import Sim

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim():
    return Sim(_NODES, list(_NODES), random.Random(1))


class ContractedScholarHoursCountTests(unittest.TestCase):

    def test_headcount_ignores_contracted_hours_and_should(self):
        # effective_scholars stays a pure headcount deliberately: other
        # callers want "how many people are there", and conflating the two
        # is what made this bug hard to see. The fix is a SECOND function,
        # not a changed one.
        sim = _fresh_sim()
        before = sim.effective_scholars()
        sim.household.contract_hours = {"scholar": 4000.0}
        self.assertEqual(sim.effective_scholars(), before)

    def test_contracted_hours_become_hands(self):
        sim = _fresh_sim()
        before = sim.scholar_hands_available()
        sim.household.contract_hours = {"scholar": 4000.0}
        after = sim.scholar_hands_available()
        # 4,000 hours at 2,000 hours a person-year is two more scholars.
        self.assertAlmostEqual(
            after - before, 4000.0 / sim.HOURS_PER_PERSON_YEAR, places=9)

    def test_the_project_gate_reads_hands_not_headcount(self):
        # The decisive one. Pick a node whose ONLY remaining blocker is the
        # scholar count - every prerequisite satisfied - so the gate under
        # test is the one actually reached. A first attempt at this test
        # picked a node still missing prerequisites and "passed" against an
        # unchanged message for the wrong reason, which is worth recording:
        # a gate test that never reaches the gate proves nothing.
        sim = _fresh_sim()
        needed = int(sim.effective_scholars()) + 2
        target = None
        for node_id, node in _NODES.items():
            if node.get("sch") != needed:
                continue
            sim.household.done.update(node.get("pre", []))
            message = sim.start_reason(node_id, _why=True)[1] or ""
            if "scholars" in message:
                target = (node_id, message)
                break
        self.assertIsNotNone(
            target, "no node reachable with only the scholar count blocking")
        node_id, blocked_message = target

        sim.household.contract_hours = {
            "scholar": 2.0 * sim.HOURS_PER_PERSON_YEAR}
        after_message = sim.start_reason(node_id, _why=True)[1] or ""
        self.assertNotEqual(
            blocked_message, after_message,
            "the refusal is byte-identical before and after buying two "
            "scholar-years, which is exactly the bug Complaints/34 reports: "
            "commission cannot unblock the gate that recommends commission.")
        self.assertNotIn(
            "trained scholars", after_message,
            "two bought scholar-years did not clear a two-scholar gate")

    def test_craft_and_scholar_gates_now_agree_in_shape(self):
        # The bug was an asymmetry, so the regression test is the symmetry.
        # Both must count staff plus the founder plus contracted hours.
        sim = _fresh_sim()
        sim.household.contract_hours = {
            "scholar": sim.HOURS_PER_PERSON_YEAR,
            "carpenter": sim.HOURS_PER_PERSON_YEAR,
        }
        self.assertAlmostEqual(
            sim.scholar_hands_available() - sim.effective_scholars(),
            1.0, places=9)
        self.assertGreater(
            sim.craft_hands_available(), sim.household.artisans)


if __name__ == "__main__":
    unittest.main()
