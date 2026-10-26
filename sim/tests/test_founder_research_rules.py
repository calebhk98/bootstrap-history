"""The founder's start goes through the shared research path with the seat as the researcher (Complaint 491): `start_project`
hands the seat to `research.begin` and carries its refusal back, and the seat answers the shared path's questions from its
own books (`SeatResearcher`). Each is called on the projects module built with only the views it reads."""
QUICK_TOPIC = True
UNDER_TEST = {"start_project"}

import unittest
from unittest import mock

from sim.agents.player_commands import CommandRejected
from sim.projects import starting
from sim.projects.api import StartProject
from sim.projects.researcher import SeatResearcher
from sim.tests import projects_host

NODE = "smithing"


def seat_module(capital=100.0, credit=50.0, active=None, paid_towards=None, cost=80.0):
    state = projects_host.projects_state(active=active if active is not None else {}, paid_towards=paid_towards)
    return projects_host.build(
        legacy_projects=state, techniques_held={"known"}, acting_balance=capital, credit_limit=credit,
        project_cost=lambda node_id: cost, hours_available={"scholar_hands": 2.0, "craft_hands": 7.0},
        acting_seat=3)


class StartProjectTests(unittest.TestCase):
    def start(self, begin, refusal=None, precaution=False, spec=object()):
        module = projects_host.build(
            start_refusal=lambda node_id, extra_owed=0.0: refusal, tree={NODE: {"name": "Smithing"}},
            research_world="world", precaution_spec=lambda node_id: spec)
        with mock.patch.object(starting.research, "begin", begin), \
             mock.patch.object(starting, "SeatResearcher", lambda projects, precaution=False: ("seat", precaution)):
            return module.start_project(StartProject(NODE, precaution))

    def test_a_start_is_the_shared_research_path_with_the_seat_as_researcher(self):
        begun = []
        self.assertEqual(self.start(lambda actor, node, world: begun.append((actor, node, world))), (True, None))
        self.assertEqual(begun, [(("seat", False), NODE, "world")])

    def test_the_shared_gates_refusal_is_carried_back(self):
        def refuse(actor, node, world):
            raise CommandRejected("scholar_staff refusal")
        self.assertEqual(self.start(refuse), (False, "scholar_staff refusal"))

    def test_a_start_the_game_refuses_never_reaches_the_shared_path(self):
        reached = []
        self.assertEqual(self.start(lambda *args: reached.append(args), refusal="no"), (False, "no"))
        self.assertEqual(reached, [])

    def test_a_precaution_the_node_offers_nothing_to_pay_for_is_refused_before_the_shared_path(self):
        reached = []
        started, _reason = self.start(lambda *args: reached.append(args), precaution=True, spec=None)
        self.assertFalse(started)
        self.assertEqual(reached, [])


class SeatResearcherTests(unittest.TestCase):
    def test_the_seat_knows_what_the_household_has_done(self):
        seat = SeatResearcher(seat_module())
        self.assertTrue(seat.knows("known", None))
        self.assertFalse(seat.knows(NODE, None))

    def test_the_seat_offers_the_scholar_hands_for_scholars_and_craft_hands_otherwise(self):
        seat = SeatResearcher(seat_module())
        self.assertEqual((seat.research_hands("scholar"), seat.research_hands("craft")), (2.0, 7.0))

    def test_the_price_is_the_projects_cost_less_what_was_already_paid_towards_it(self):
        with mock.patch("sim.projects.researcher.funding.paid_credit", lambda price, paid: paid * 0.5):
            price = SeatResearcher(seat_module(paid_towards={NODE: 40.0}, cost=80.0)).research_price({}, NODE, None)
        self.assertEqual(price, 60.0)

    def test_the_price_is_the_full_cost_when_nothing_was_paid_and_never_negative(self):
        self.assertEqual(SeatResearcher(seat_module(cost=80.0)).research_price({}, NODE, None), 80.0)
        with mock.patch("sim.projects.researcher.funding.paid_credit", lambda price, paid: price * 2):
            self.assertEqual(SeatResearcher(seat_module(paid_towards={NODE: 1.0})).research_price({}, NODE, None), 0.0)

    def test_the_budget_is_cash_and_credit_less_what_is_owed_on_work_in_hand(self):
        module = seat_module(capital=100.0, credit=50.0, active={"a": {"cost_left": 30.0}, "b": {"cost_left": None}})
        self.assertEqual(SeatResearcher(module).copy_budget(None), 120.0)

    def test_a_purse_in_debt_adds_no_negative_cash_to_the_budget(self):
        self.assertEqual(SeatResearcher(seat_module(capital=-500.0, credit=50.0)).copy_budget(None), 50.0)

    def test_committing_begins_the_seat_project_with_the_precaution_it_was_given(self):
        began = []
        module = seat_module()
        module.begin_project = lambda node_id, precaution: began.append((node_id, precaution)) or "begun"
        self.assertEqual(SeatResearcher(module, precaution=True).commit_research(NODE, {}, None), "begun")
        self.assertEqual(began, [(NODE, True)])


if __name__ == "__main__":
    unittest.main()
