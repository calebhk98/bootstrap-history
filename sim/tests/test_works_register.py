"""Complaint 133: a construction belongs to the tiles where it is built, with a capacity that scales its cost.

The register is saved state beside the ways (`works`, `works_under_construction`). Small fixtures only."""

QUICK_TOPIC = True

import dataclasses
import unittest
from types import SimpleNamespace

from sim.engine.state import EconomyState
from sim.engine.works import WorksMixin

TOWN, PORT, ELSEWHERE = "town_01", "port_02", "far_03"


class _Host(WorksMixin):
    INSTITUTION_EXPANSION_CONVEXITY = 0.5

    def __init__(self, year=100.0, cash=1e9, known=("granary",)):
        self.nodes = {"granary": {"id": "granary", "up": 3.0, "rev": 0.0, "build_yrs": 2.0},
                      "lore": {"id": "lore", "up": 0.0, "rev": 0.0}}
        self.state = SimpleNamespace(
            economy=EconomyState(), scenario=SimpleNamespace(year=year),
            projects=SimpleNamespace(done=set(known) | {"lore"}, granted=set()))
        self.cash = cash
        self.paid = []
        self.labour = SimpleNamespace(settlement_tiles=lambda: [TOWN, PORT])

    def project_cost_now(self, node_id):
        return 1000.0

    def is_venture(self, node_id):
        return self.nodes[node_id]["up"] > 0

    def pay_edge(self, edge, money, purpose):
        self.paid.append(money)

    def spending_power(self, kind="buy"):
        return self.cash


class WorksRegisterTests(unittest.TestCase):

    def test_the_register_is_saved_state(self):
        names = {field.name for field in dataclasses.fields(EconomyState)}
        self.assertLessEqual({"works", "works_under_construction"}, names)

    def test_a_work_is_built_on_a_tile_the_nation_holds_and_opens_when_its_time_has_passed(self):
        host = _Host()
        built, message = host.build_work(TOWN, "granary", 1.0)
        self.assertTrue(built, message)
        self.assertEqual(host.works_at(TOWN), {})
        host.state.scenario.year = 101.0
        host.finish_works()
        self.assertEqual(host.works_at(TOWN), {})
        host.state.scenario.year = 102.0
        host.finish_works()
        self.assertEqual(host.works_at(TOWN), {"granary": 1.0})
        self.assertEqual(host.works_at(PORT), {})
        self.assertEqual(host.work_capacity("granary"), 1.0)

    def test_the_cost_of_a_work_rises_with_the_capacity_asked_for(self):
        host = _Host()
        small, large = host.work_quote(TOWN, "granary", 1.0), host.work_quote(TOWN, "granary", 3.0)
        self.assertAlmostEqual(small["money"], 1000.0)
        self.assertGreater(large["money"], 3 * small["money"])

    def test_adding_to_a_tile_costs_more_than_the_first_unit_there(self):
        host = _Host()
        host.state.economy.works = {TOWN: {"granary": 2.0}}
        first_elsewhere = host.work_quote(PORT, "granary", 1.0)["money"]
        added_at_town = host.work_quote(TOWN, "granary", 1.0)["money"]
        self.assertGreater(added_at_town, first_elsewhere)

    def test_capacity_adds_across_tiles(self):
        host = _Host()
        host.state.economy.works = {TOWN: {"granary": 2.0}, PORT: {"granary": 1.5}}
        self.assertEqual(host.work_capacity("granary"), 3.5)

    def test_a_tile_the_nation_does_not_hold_is_refused(self):
        built, message = _Host().build_work(ELSEWHERE, "granary", 1.0)
        self.assertFalse(built)
        self.assertIn("hold", message)

    def test_knowledge_is_not_a_work(self):
        built, message = _Host().build_work(TOWN, "lore", 1.0)
        self.assertFalse(built)
        self.assertIn("not something that can be built", message)

    def test_a_work_not_yet_known_is_refused(self):
        built, message = _Host(known=()).build_work(TOWN, "granary", 1.0)
        self.assertFalse(built)
        self.assertIn("do not know", message)

    def test_a_second_order_on_the_same_tile_waits_for_the_first(self):
        host = _Host()
        self.assertTrue(host.build_work(TOWN, "granary", 1.0)[0])
        built, message = host.build_work(TOWN, "granary", 1.0)
        self.assertFalse(built)
        self.assertIn("already being built", message)

    def test_a_work_is_paid_for_when_started_and_refused_when_it_cannot_be_afforded(self):
        host = _Host()
        host.build_work(TOWN, "granary", 1.0)
        self.assertEqual(host.paid, [1000.0])
        poor = _Host(cash=10.0)
        built, message = poor.build_work(PORT, "granary", 1.0)
        self.assertFalse(built)
        self.assertEqual(poor.paid, [])
        self.assertEqual(poor.state.economy.works_under_construction, {})

    def test_a_work_can_be_lost_and_its_capacity_leaves_the_tile(self):
        host = _Host()
        host.state.economy.works = {TOWN: {"granary": 2.0}}
        host.lose_work(TOWN, "granary", 0.5)
        self.assertEqual(host.works_at(TOWN), {"granary": 1.5})
        host.lose_work(TOWN, "granary", 9.0)
        self.assertEqual(host.state.economy.works, {})


if __name__ == "__main__":
    unittest.main()
