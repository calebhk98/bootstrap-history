"""Complaint 421 and 640: what automation does with a candidate project and how it sizes a mine order, on plain inputs."""

QUICK_TOPIC = True

import unittest

from sim.engine.auto_start_rule import judge_start_candidate, size_mine_order


def judge(active=0, cap=5, startable=True, cost=10.0, room=100.0):
    reads = []

    def can_start():
        reads.append("can_start")
        return startable

    def project_cost():
        reads.append("cost")
        return cost
    return judge_start_candidate(active, cap, can_start, project_cost, room), reads


class JudgeStartCandidate(unittest.TestCase):
    def test_a_startable_affordable_candidate_starts(self):
        self.assertEqual(judge()[0], "start")

    def test_at_the_cap_the_year_stops_without_reading_anything_else(self):
        verdict, reads = judge(active=5, cap=5)
        self.assertEqual((verdict, reads), ("cap", []))

    def test_a_candidate_that_cannot_start_is_blocked_before_its_cost_is_read(self):
        verdict, reads = judge(startable=False)
        self.assertEqual((verdict, reads), ("blocked", ["can_start"]))

    def test_a_candidate_dearer_than_the_room_is_too_dear(self):
        self.assertEqual(judge(cost=101.0, room=100.0)[0], "too_dear")

    def test_a_candidate_costing_exactly_the_room_starts(self):
        self.assertEqual(judge(cost=100.0, room=100.0)[0], "start")


class SizeMineOrder(unittest.TestCase):
    def test_active_and_pending_capacity_come_off_the_shortfall(self):
        wanted, _ordered = size_mine_order(100.0, 30.0, 20.0, 1e9, 1.0)
        self.assertAlmostEqual(wanted, 50.0)

    def test_no_negative_want_when_capacity_exceeds_the_shortfall(self):
        self.assertEqual(size_mine_order(10.0, 30.0, 20.0, 1e9, 1.0), (0.0, 0.0))

    def test_the_order_is_capped_by_a_quarter_of_capital_at_the_capex(self):
        wanted, ordered = size_mine_order(1000.0, 0.0, 0.0, 400.0, 2.0)
        self.assertEqual((wanted, ordered), (1000.0, 50.0))

    def test_a_tiny_capex_does_not_blow_up_the_cap(self):
        _wanted, ordered = size_mine_order(1000.0, 0.0, 0.0, 400.0, 0.0)
        self.assertEqual(ordered, 100.0)

    def test_no_capital_orders_nothing(self):
        self.assertEqual(size_mine_order(1000.0, 0.0, 0.0, 0.0, 2.0)[1], 0.0)


if __name__ == "__main__":
    unittest.main()
