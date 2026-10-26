"""Complaint 640: the allocator's callers over stand-ins: a project is offered the hours the rule gives it and the
directive is written back for the screens to read; the standing work order tops up the hours already sold by hand
and says so when it falls short; a standing order is stored in the household state and survives a save. The queue, the
offer and the `allocate` command are in test_allocate."""
QUICK_TOPIC = True

import json
import types
import unittest

from sim.agents.api import Household
from sim.engine.allocation_notes import AllocationNotesMixin
from sim.engine.core_step_phases import StepPhasesMixin
from sim.engine.hour_offer import work_order_shortfall
from sim.engine.state import SimulationState, deserialize_state, serialize_state
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.step_phase_projects import ProjectProgressPhaseMixin
from sim.tests import event_stand_in


class WorkOrderShortfall(unittest.TestCase):
    def test_it_tops_up_the_hours_already_sold_by_hand_and_is_never_negative(self):
        self.assertEqual(work_order_shortfall(100.0, 40.0), 60.0)
        self.assertEqual(work_order_shortfall(100.0, 100.0), 0.0)
        self.assertEqual(work_order_shortfall(100.0, 250.0), 0.0)
        self.assertEqual(work_order_shortfall(100.0, 0.0), 100.0)


class Directive(AllocationNotesMixin, StepPhasesMixin):
    send = event_stand_in.send

    def __init__(self, directive, sold, room, trade="labourer"):
        household = types.SimpleNamespace(hour_allocations={"work": directive}, work_trade=trade,
                                          wage_hours_this_year=sold, log=[], unused_hours_reported={})
        self.state = types.SimpleNamespace(household=household, scenario=types.SimpleNamespace(year=50))
        self.room = room
        self.sold = []
        self.labour = types.SimpleNamespace(director_pool=lambda: room, director_hours_committed=lambda: 0.0,
                                            work_for_wages=self._work)

    def _work(self, trade, hours):
        self.sold.append((trade, hours))
        self.state.household.wage_hours_this_year += hours
        return hours * 2.0, None


class StandingWorkDirective(unittest.TestCase):
    def test_it_sells_only_what_the_hand_sold_hours_leave_of_the_directive(self):
        game = Directive(directive=100.0, sold=40.0, room=1000.0)
        game._step_standing_work_directive()
        self.assertEqual(game.sold, [("labourer", 60.0)])
        self.assertEqual(game.state.household.wage_hours_this_year, 100.0)
        self.assertEqual(game.state.household.log, [])

    def test_a_directive_the_hand_has_met_sells_nothing(self):
        game = Directive(directive=100.0, sold=100.0, room=1000.0)
        game._step_standing_work_directive()
        self.assertEqual(game.sold, [])

    def test_no_trade_named_sells_nothing(self):
        game = Directive(directive=100.0, sold=0.0, room=1000.0, trade=None)
        game._step_standing_work_directive()
        self.assertEqual(game.sold, [])

    def test_with_less_room_than_the_directive_it_sells_the_room_and_says_the_hours_ran_out(self):
        game = Directive(directive=100.0, sold=0.0, room=30.0)
        game._step_standing_work_directive()
        self.assertEqual(game.sold, [("labourer", 30.0)])
        facts = [line[1].facts for line in game.state.household.log]
        self.assertEqual([fact["reason"] for fact in facts], ["no_hours_left"])


class Offer(ProjectProgressPhaseMixin):
    def __init__(self, directive):
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(hour_allocations={"b": directive} if directive else {}),
            founder=types.SimpleNamespace(director_hours_spent_founder=0.0),
            holdings=types.SimpleNamespace(binding=None))
        self.founder_alive = True

    def project_hour_pace(self, node_id):
        return 3000.0

    def project_resource_throttle(self, node_id):
        return 1.0


class OfferHours(unittest.TestCase):
    def test_a_directed_project_is_offered_its_directive_and_the_screens_read_it_back(self):
        game = Offer(500.0)
        project = {"ph_left": 2000.0}
        game._project_progress_offer_hours("b", project, 1900.0, 1900.0, [])
        self.assertEqual(project["hours_offered_this_year"], 500.0)
        self.assertEqual(project["hours_directed_this_year"], 500.0)
        self.assertEqual(project["ph_left"], 1500.0)
        self.assertEqual(game.state.founder.director_hours_spent_founder, 500.0)

    def test_an_undirected_project_has_no_directive_to_read_back(self):
        game = Offer(None)
        project = {"ph_left": 2000.0}
        game._project_progress_offer_hours("a", project, 1900.0, 1900.0, [])
        self.assertIsNone(project["hours_directed_this_year"])
        self.assertEqual(project["hours_offered_this_year"], 1900.0)

    def test_a_directive_cut_short_by_the_pool_is_reported_as_unused(self):
        game = Offer(1000.0)
        unused = []
        game._project_progress_offer_hours("b", {"ph_left": 2000.0}, 600.0, 1900.0, unused)
        self.assertEqual([(node_id, hours) for node_id, hours, _why in unused], [("b", 400.0)])


class StandingOrdersSave(unittest.TestCase):
    def test_standing_directives_and_the_work_trade_survive_a_save(self):
        state = Household(starting_capital=100.0, port=HouseholdPort())._state
        state.household.hour_allocations = {"academy_network": 321.0, "work": 77.0}
        state.household.work_trade = "scribe"
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(state))), SimulationState)
        self.assertEqual(loaded.household.hour_allocations, {"academy_network": 321.0, "work": 77.0})
        self.assertEqual(loaded.household.work_trade, "scribe")


if __name__ == "__main__":
    unittest.main()
