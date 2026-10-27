"""Telling the world when the payroll changes: the seat's employees report each change, and the staff channel moves."""
from sim.invalidating import _InvalidatingDict

from .state import STAFF


class StaffWatch:

    def staff_changed(self):
        """Something on the acting seat's payroll changed."""
        self.bump_seat(STAFF)

    def watch_staff(self, command):
        seat = self.seat_of(command.seat_id)
        seat.employees = _InvalidatingDict(seat.employees or {}, on_change=self.staff_changed)
        self.bump_seat(STAFF, command.seat_id)

    def staff_version(self):
        """A count that moves whenever the acting seat's payroll does, for a figure cached on the staff."""
        return self.clock.counter(self.module_id, STAFF, True)[1]
