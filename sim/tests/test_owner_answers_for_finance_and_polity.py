"""What finance and polity ask of other owners, one owner's method at a time: the projects' halt, the hazards' told-once mark, the
seats' country of a seat and the actors' figures of a government. Each is called on the owner's module over plain values."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.module import Actors
from sim.hazards.state import HazardsSeat
from sim.hazards.api import SayOnce
from sim.hazards.module import Hazards
from sim.projects.api import HaltActiveProjects
from sim.projects.projects import Projects
from sim.projects.state import ProjectsSeat
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness


class HaltActiveProjectsCommand(unittest.TestCase):
    def module(self, seat):
        return module_harness.build(Projects, seat=seat, module_id="projects")

    def test_work_in_hand_stops_and_the_names_and_the_money_kept_come_back(self):
        seat = ProjectsSeat(active={"b": {"spent": 40.0}, "a": {"spent": 5.0}}, bountied={"a"})
        self.assertEqual(self.module(seat).apply_halt_active_projects(HaltActiveProjects()), (["a", "b"], 45.0))
        self.assertEqual((seat.active, seat.paid_towards, seat.bountied), ({}, {"a": 5.0, "b": 40.0}, set()))

    def test_with_nothing_in_hand_the_record_of_credits_is_left_as_it_was(self):
        seat = ProjectsSeat(paid_towards={"c": 3.0})
        self.assertEqual(self.module(seat).apply_halt_active_projects(HaltActiveProjects()), ([], 0.0))
        self.assertEqual(seat.paid_towards, {"c": 3.0})


class SayOnceCommand(unittest.TestCase):
    def test_a_notice_is_new_the_first_time_and_old_after(self):
        seat = HazardsSeat()
        module = module_harness.build(Hazards, seat=seat, module_id="hazards")
        self.assertEqual([module.say_once(SayOnce("levy:x")), module.say_once(SayOnce("levy:x")), module.say_once(SayOnce("levy:y"))],
                         [True, False, True])
        self.assertEqual(seat.said_condition, {"levy:x", "levy:y"})

    def test_a_notice_already_in_the_saved_world_is_old(self):
        module = module_harness.build(Hazards, seat=HazardsSeat(said_condition={"levy:x"}), module_id="hazards")
        self.assertFalse(module.say_once(SayOnce("levy:x")))


class SeatCountry(unittest.TestCase):
    def test_a_seat_answers_the_country_it_names_and_none_when_it_names_none_or_is_unknown(self):
        seats = {"a": SeatsSeat(country="han"), "b": SeatsSeat(country=None)}
        module = module_harness.build(Seats, views={"registered_seats": list(seats)}, module_id="seats")
        module.seat_slot_of = seats.__getitem__
        self.assertEqual([module.seat_country("a"), module.seat_country("b"), module.seat_country("c")], ["han", None, None])


class GovernmentFigures(unittest.TestCase):
    def module(self, records):
        return module_harness.build(Actors, world=SimpleNamespace(records=records), module_id="actors")

    def test_a_government_answers_its_grant_and_its_two_levy_rates(self):
        record = SimpleNamespace(patron_grant=90.0, levy_requisition_rate=0.1, levy_office_rate=0.05)
        module = self.module({"government:han": record})
        self.assertEqual(module.government_figures("han"), (90.0, 0.1, 0.05))
        self.assertIsNone(module.government_figures("rome"))

    def test_the_cast_is_recorded_once_it_holds_any_record(self):
        self.assertEqual((self.module({}).cast_recorded(), self.module({"firm:1": object()}).cast_recorded()), (False, True))


if __name__ == "__main__":
    unittest.main()
