"""What each module forgets when the acting seat changes (`Module.seat_bound`): one module, one hook call, its own memory read after."""

QUICK_TOPIC = True

import unittest

from sim.invalidating import _InvalidatingDict
from sim.knowledge.api import KnowledgeSeat
from sim.knowledge.module import HELD_CHANGES, Knowledge
from sim.markets.module import Markets
from sim.materials.module import Materials
from sim.production.caches import SeatMemos
from sim.production.module import Production
from sim.projects.projects import ACTIVE_CHANGES, Projects
from sim.projects.state import ProjectsSeat
from sim.tests import module_harness
from sim.ventures.channels import OPERATING_CHANGES
from sim.ventures.module import Ventures
from sim.ventures.state import VenturesSeat
from sim.workforce.module import Workforce
from sim.workforce.state import STAFF
from sim.workforce.api import WorkforceSeat


class SeatBoundHooks(unittest.TestCase):
    def test_production_drops_every_seats_memos(self):
        module = module_harness.build(Production)
        module._memos = {"a": SeatMemos(), "b": SeatMemos()}
        module.clock.act_as("a")
        module.seat_bound()
        self.assertEqual(module._memos, {})

    def test_markets_drops_the_acting_seats_goods_category_figures_and_no_other_seats(self):
        module = module_harness.build(Markets)
        module._caches = {("a", "goods_cat_state"): 1, ("a", "income_factor"): 2, ("a", "kept"): 3, ("b", "income_factor"): 4}
        module.clock.act_as("a")
        module.seat_bound()
        self.assertEqual(module._caches, {("a", "kept"): 3, ("b", "income_factor"): 4})

    def test_materials_drops_the_acting_seats_remembered_demand(self):
        module = module_harness.build(Materials)
        module._readings = {}
        module.clock.act_as("a")
        readings = module.readings
        readings.annual, readings.held, readings.by_tag = {"x": 1}, {"y": 2}, {"z": 3}
        module.seat_bound()
        self.assertEqual((readings.annual, readings.held, readings.by_tag), (None, None, None))

    def test_knowledge_counts_a_change_of_what_the_acting_seat_holds(self):
        module = module_harness.build(Knowledge, seat=KnowledgeSeat())
        module.clock.act_as("a")
        before = module.clock.counter(module.module_id, HELD_CHANGES, True)
        module.seat_bound()
        self.assertNotEqual(module.clock.counter(module.module_id, HELD_CHANGES, True), before)

    def test_ventures_watches_the_acting_seats_business_and_counts_a_change_of_what_operates(self):
        module = module_harness.build(Ventures, seat=VenturesSeat(), views={}, answers={})
        module.needs.sent.clear()
        module.clock.act_as("a")
        before = module.clock.counter(module.module_id, OPERATING_CHANGES, True)
        module.seat_bound()
        self.assertEqual(module.seat.business.watch, module.operating_changed)
        self.assertNotEqual(module.clock.counter(module.module_id, OPERATING_CHANGES, True), before)

    def test_projects_wraps_the_acting_seats_projects_in_hand_and_counts_the_change(self):
        module = module_harness.build(Projects, seat=ProjectsSeat())
        module.seat_slot_of = lambda seat_id: module.seat
        module.clock.act_as("a")
        before = module.clock.counter(module.module_id, ACTIVE_CHANGES, True)
        module.seat_bound()
        self.assertIsInstance(module.seat.active, _InvalidatingDict)
        self.assertNotEqual(module.clock.counter(module.module_id, ACTIVE_CHANGES, True), before)

    def test_workforce_wraps_the_acting_seats_payroll_and_counts_the_change(self):
        module = module_harness.build(Workforce, seat=WorkforceSeat(), views={"game_random": None})
        module.seat_slot_of = lambda seat_id: module.seat
        module.clock.act_as("a")
        before = module.clock.counter(module.module_id, STAFF, True)
        module.seat_bound()
        self.assertIsInstance(module.seat.employees, _InvalidatingDict)
        self.assertNotEqual(module.clock.counter(module.module_id, STAFF, True), before)


if __name__ == "__main__":
    unittest.main()
