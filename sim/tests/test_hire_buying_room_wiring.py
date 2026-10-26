"""Complaint 525, Complaint 640: `hire_buying_room` hires, and when the hire is refused only for want of room buys room
(if the budget covers it) and hires again; any other refusal stands. `buy_room_for` builds the housing the rule
(housing_places_to_buy, in test_auto_hire_buys_room) asks for and logs it."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_staff_controls import StaffControlsMixin
from sim.refusal import Refusal, cause_of
from sim.tests import event_stand_in


class Staff(StaffControlsMixin):
    def __init__(self, room, refusal_cause="household_room", power=1e9):
        self.room = room
        self.refusal_cause = refusal_cause
        self.hires = []
        self.built = []
        self.log = []
        self.labour_market = types.SimpleNamespace(whole_recruits=lambda trade, count, premium: count,
                                                   hire_cost=lambda trade, count, premium: 10.0 * count)
        self._world = types.SimpleNamespace(
            housing_price_per_place=lambda: 100.0, spending_power=lambda kind: power,
            build_worker_housing=lambda places: self.built.append(places) or True,
            state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=7),
                                        household=types.SimpleNamespace(log=self.log)))
        event_stand_in.stood_in(self._world)

    def household_room(self):
        return self.room

    def hire(self, trade, count):
        self.hires.append((trade, count))
        if self.room >= count:
            return True, None
        return False, Refusal(self.refusal_cause, "no")


class HireBuyingRoom(unittest.TestCase):
    def test_a_hire_that_fits_buys_no_room(self):
        staff = Staff(room=5.0)
        self.assertEqual(staff.hire_buying_room("smith", 2)[0], True)
        self.assertEqual((staff.built, len(staff.hires)), ([], 1))

    def test_a_hire_refused_for_room_buys_the_missing_places_and_hires_again(self):
        staff = Staff(room=0.0)
        staff.hire = lambda trade, count: (staff.hires.append((trade, count)) or
                                           ((True, None) if staff.built else (False, Refusal("household_room", "no"))))
        hired, _reply = staff.hire_buying_room("smith", 2)
        self.assertTrue(hired)
        self.assertEqual(staff.built, [2])
        self.assertEqual(len(staff.hires), 2)
        self.assertEqual([line[1].cause for line in staff.log], ["policy_housing"])

    def test_a_budget_that_cannot_cover_the_housing_and_the_hire_leaves_the_refusal(self):
        staff = Staff(room=0.0, power=50.0)
        hired, reply = staff.hire_buying_room("smith", 2)
        self.assertFalse(hired)
        self.assertEqual(cause_of(reply), "household_room")
        self.assertEqual((staff.built, len(staff.hires)), ([], 1))

    def test_a_refusal_for_another_reason_is_not_answered_with_housing(self):
        staff = Staff(room=0.0, refusal_cause="cash_short")
        hired, reply = staff.hire_buying_room("smith", 2)
        self.assertFalse(hired)
        self.assertEqual(cause_of(reply), "cash_short")
        self.assertEqual(staff.built, [])


if __name__ == "__main__":
    unittest.main()
