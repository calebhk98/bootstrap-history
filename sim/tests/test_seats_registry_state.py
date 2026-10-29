"""The seat's goal, country, kind, holder and policy are the seats module's seat state: each owner command writes the slot, each
view answers a set value, the slot survives a save round trip, and a handover leaves the replacement its own policy. Each test
calls one handler, view or rule on a written-out slot."""
QUICK_TOPIC = True

import unittest

from sim.engine.saveload import goal_of_blob
from sim.engine.state import deserialize_state, serialize_state
from sim.seats.api import COUNTRY_SEAT, ForgetGoalCaches, HandOverSeat, MoveSeat, SetGoal, SetPolicy, SetSeatHolder
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness


def seats_over(slots, acting="a", **views):
    module = module_harness.build(Seats, seat=slots[acting], views=dict({"registered_seats": list(slots)}, **views))
    module.seat_slot_of = slots.__getitem__
    module.clock.act_as(acting)
    return module


class Commands(unittest.TestCase):

    def test_set_goal_writes_the_acting_seats_goal_only(self):
        slots = {"a": SeatsSeat(), "b": SeatsSeat(goal="kept")}
        module = seats_over(slots)
        module.set_goal(SetGoal("steel"))
        self.assertEqual((slots["a"].goal, slots["b"].goal), ("steel", "kept"))
        self.assertIsInstance(module_harness.sent(module)[0], ForgetGoalCaches)

    def test_set_policy_writes_the_acting_seats_switch(self):
        slots = {"a": SeatsSeat(), "b": SeatsSeat()}
        seats_over(slots).set_policy(SetPolicy("auto_hire", "replace"))
        self.assertEqual((slots["a"].policy, slots["b"].policy), ({"auto_hire": "replace"}, {}))

    def test_set_seat_holder_writes_the_government_id(self):
        slots = {"a": SeatsSeat(kind=COUNTRY_SEAT)}
        seats_over(slots).set_seat_holder(SetSeatHolder("government:han"))
        self.assertEqual(slots["a"].holder, "government:han")


class Views(unittest.TestCase):

    def test_goal_answers_the_set_goal(self):
        self.assertEqual(seats_over({"a": SeatsSeat(goal="steel")}).goal()["node"], "steel")

    def test_founder_answers_the_set_policy_as_the_live_record(self):
        slot = SeatsSeat(policy={"auto_mine": False})
        self.assertIs(seats_over({"a": slot}).founder()["policy"], slot.policy)

    def test_a_country_seat_has_no_policy(self):
        self.assertIsNone(seats_over({"a": SeatsSeat(kind=COUNTRY_SEAT, policy={})}).founder()["policy"])

    def test_the_automatic_policy_reads_the_set_switch(self):
        module = seats_over({"a": SeatsSeat(policy={"auto_mine": False})}, automation={"manual": False})
        self.assertFalse(module.automatic_policy("auto_mine"))

    def test_kind_holder_and_country_answer_per_seat(self):
        slots = {"a": SeatsSeat(), "b": SeatsSeat(kind=COUNTRY_SEAT, holder="government:han", country="han")}
        module = seats_over(slots)
        self.assertEqual((module.seat_kind("b"), module.seat_holder("b"), module.seat_country("b"), module.seat_country("a")),
                         (COUNTRY_SEAT, "government:han", "han", None))

    def test_seat_list_names_the_household_seats(self):
        slots = {"a": SeatsSeat(), "r": SeatsSeat(kind=COUNTRY_SEAT), "c": SeatsSeat(dead_reason="fell")}
        self.assertEqual(seats_over(slots).seat_list(), {"joined": ["a", "r", "c"], "households": ["a", "c"], "playing": ["a"]})

    def test_the_seats_holding_a_patent_are_listed_in_joining_order(self):
        slots = {"a": SeatsSeat(patents={"loom": {}}), "b": SeatsSeat(), "c": SeatsSeat(patents={"loom": {}, "kiln": {}})}
        module = seats_over(slots)
        self.assertEqual((module.seats_holding_patent("loom"), module.seats_holding_patent("kiln")), (["a", "c"], ["c"]))


class SaveRoundTrip(unittest.TestCase):

    def test_the_slot_comes_back_as_it_was_saved(self):
        slot = SeatsSeat(goal="steel", country="han", kind=COUNTRY_SEAT, holder="government:han", policy={"auto_hire": "replace"})
        self.assertEqual(deserialize_state(serialize_state(slot), SeatsSeat), slot)

    def test_goal_of_blob_reads_the_slot(self):
        blob = {"acting_seat": "a", "seats": {"a": {"modules": {"seats": {"goal": "steel"}}}}}
        self.assertEqual(goal_of_blob(blob), "steel")


class Handover(unittest.TestCase):

    def test_the_replacement_keeps_its_own_policy_and_takes_the_leavers_goal(self):
        leaver, heir = SeatsSeat(goal="steel", policy={"auto_hire": True}), SeatsSeat(policy={"auto_hire": False})
        slots = {"a": leaver, "b": heir}
        module = seats_over(slots, seat_holds={"b": []}, disclosures={"b": {}})

        def move(command):
            if isinstance(command, MoveSeat):   # the registry gives the replacement the leaver's slot and drops the leaver
                slots["b"] = leaver
                del slots["a"]
                module.needs.registered_seats = lambda: list(slots)
            return {}

        module.needs.send = move
        module.hand_over_seat(HandOverSeat("a", "b"))
        self.assertEqual((slots["b"].goal, slots["b"].policy), ("steel", {"auto_hire": False}))


if __name__ == "__main__":
    unittest.main()
