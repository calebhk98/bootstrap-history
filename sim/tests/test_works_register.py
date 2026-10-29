"""Complaint 133: a construction belongs to the tiles where it is built, with a capacity that scales its cost.

The register is saved state beside the ways (`works`, `works_under_construction`). Small fixtures only."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.finance import purchase_rules
from sim.land import works_rules
from sim.land.commands import BuildWork, LoseWork
from sim.land.module import Land
from sim.land.state import LandSeat, LandWorld
from sim.ledger.api import PayEdge
from sim.tests import module_harness

TOWN, PORT, ELSEWHERE = "town_01", "port_02", "far_03"
NODES = {"granary": {"id": "granary", "up": 3.0, "rev": 0.0, "build_yrs": 2.0}, "lore": {"id": "lore", "up": 0.0, "rev": 0.0}}


class _Host:
    """The land module over plain values for the views the works register reads."""

    def __init__(self, year=100.0, cash=1e9, known=("granary",)):
        self.year = year
        self.cash = cash
        self.paid = []
        self.module = module_harness.build(
            Land, world=LandWorld(), seat=LandSeat(),
            views={"tree_nodes": NODES, "project_cost_now": lambda node_id: 1000.0,
                   "is_venture": lambda node_id: NODES[node_id]["up"] > 0, "year": lambda: self.year,
                   "institution_expansion_convexity": lambda: 0.5,
                   "settlement_tiles": {TOWN: 1.0, PORT: 1.0}, "techniques_held": set(known) | {"lore"},
                   "techniques_granted": set(), "can_pay": lambda cost: purchase_rules.can_pay(cost, self.cash),
                   "afford_means": "cash", "money_text": lambda amount, grouped=False: "%d coin" % amount},
            answers={PayEdge: lambda command: self.paid.append(command.amount)})
        self.world = self.module.world

    def build_work(self, tile, node_id, capacity):
        return self.module.build_work(BuildWork(tile, node_id, capacity))

    def finish_works(self):
        self.module.finish_works()

    def lose_work(self, tile, node_id, capacity):
        self.module.lose_work(LoseWork(tile, node_id, capacity))

    def works_at(self, tile):
        return self.module.works_at(tile)

    def work_capacity(self, node_id):
        return self.module.work_capacity(node_id)

    def work_quote(self, tile, node_id, capacity):
        return self.module.work_quote(tile, node_id, capacity)


class WorksRulesTests(unittest.TestCase):

    def test_each_further_unit_costs_more_than_the_one_before(self):
        self.assertEqual(works_rules.cost_curve(1.0, 0.5), 1.0)
        self.assertEqual(works_rules.cost_curve(3.0, 0.5), 3.0 + 0.5 * 0.5 * 4.0)

    def test_the_money_is_the_nodes_cost_over_the_units_between_the_two_points_on_the_curve(self):
        self.assertEqual(works_rules.work_money(1000.0, 2.0, 1.0, 0.5),
                         1000.0 * (works_rules.cost_curve(3.0, 0.5) - works_rules.cost_curve(2.0, 0.5)))

    def test_a_work_that_finishes_moves_from_the_pending_register_to_the_built_one(self):
        pending, built = {"t": {"mill": [105.0, 1.0], "farm": [110.0, 2.0]}}, {"t": {"mill": 0.5}}
        works_rules.finish_works(pending, built, 105.0)
        self.assertEqual((pending, built), ({"t": {"farm": [110.0, 2.0]}}, {"t": {"mill": 1.5}}))
        works_rules.finish_works(pending, built, 110.0)
        self.assertEqual((pending, built), ({}, {"t": {"mill": 1.5, "farm": 2.0}}))

    def test_a_loss_larger_than_the_work_removes_it_and_the_empty_tile(self):
        built = {"t": {"mill": 2.0}}
        works_rules.lose_work(built, "t", "mill", 0.5)
        self.assertEqual(built, {"t": {"mill": 1.5}})
        works_rules.lose_work(built, "t", "mill", 9.0)
        self.assertEqual(built, {})

    def test_the_refusals_come_in_the_order_the_checks_are_made(self):
        self.assertIn("above nothing", works_rules.start_refusal(0, False, "n", False, (), True, "t"))
        self.assertIn("hold", works_rules.start_refusal(1, False, "n", False, (), True, "t"))
        self.assertIn("not something", works_rules.start_refusal(1, True, "n", False, (), True, "t"))
        self.assertIn("do not know", works_rules.start_refusal(1, True, "n", True, (), True, "t"))
        self.assertIn("already being built", works_rules.start_refusal(1, True, "n", True, ("n",), True, "t"))
        self.assertIsNone(works_rules.start_refusal(1, True, "n", True, ("n",), False, "t"))


class WorksRegisterTests(unittest.TestCase):

    def test_the_register_is_saved_state(self):
        names = {field.name for field in dataclasses.fields(LandWorld)}
        self.assertLessEqual({"works", "works_under_construction"}, names)

    def test_a_work_is_built_on_a_tile_the_nation_holds_and_opens_when_its_time_has_passed(self):
        host = _Host()
        built, message = host.build_work(TOWN, "granary", 1.0)
        self.assertTrue(built, message)
        self.assertEqual(host.works_at(TOWN), {})
        host.year = 101.0
        host.finish_works()
        self.assertEqual(host.works_at(TOWN), {})
        host.year = 102.0
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
        host.world.works = {TOWN: {"granary": 2.0}}
        first_elsewhere = host.work_quote(PORT, "granary", 1.0)["money"]
        added_at_town = host.work_quote(TOWN, "granary", 1.0)["money"]
        self.assertGreater(added_at_town, first_elsewhere)

    def test_capacity_adds_across_tiles(self):
        host = _Host()
        host.world.works = {TOWN: {"granary": 2.0}, PORT: {"granary": 1.5}}
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
        self.assertEqual(poor.world.works_under_construction, {})

    def test_a_work_can_be_lost_and_its_capacity_leaves_the_tile(self):
        host = _Host()
        host.world.works = {TOWN: {"granary": 2.0}}
        host.lose_work(TOWN, "granary", 0.5)
        self.assertEqual(host.works_at(TOWN), {"granary": 1.5})
        host.lose_work(TOWN, "granary", 9.0)
        self.assertEqual(host.world.works, {})


if __name__ == "__main__":
    unittest.main()
