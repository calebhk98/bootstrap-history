"""Who is hired by whom: the one book of the founder's staff, and the views of every employer's staff
against the people the country supplies.

The founder's household keeps its staff as a trade-to-head-count map (`household.employees`); only this
mixin reads or writes it from labour, and code outside labour asks `sim.labour`. Firms and states keep
their own staff in the agent registry; `reserved_people` adds both so one trade's reservations read from
one place. Complaint 556.
"""
from . import core_reservations


class StaffBookMixin:
    """Methods of Labour: the founder's payroll and the reservations against supply."""

    def employed(self, trade):
        """People of one trade on the founder's books."""
        return self._world.state.household.employees.get(trade, 0.0)

    def employed_by_trade(self):
        """A copy of the founder's staff, trade to head count."""
        return dict(self._world.state.household.employees)

    def employed_total(self):
        """Everyone on the founder's books."""
        return sum(self._world.state.household.employees.values())

    def set_employed(self, trade, people):
        """Put the founder's head count of a trade at `people`; a count of nothing leaves the trade off the books."""
        employees = self._world.state.household.employees
        if people:
            employees[trade] = people
        else:
            employees.pop(trade, None)

    def add_employed(self, trade, people):
        """Take `people` more (or fewer, when negative) of a trade onto the founder's books."""
        self.set_employed(trade, self.employed(trade) + people)

    def reserved_people(self, trade):
        """People of a trade already given to an employer: the founder's staff, and the firms' and states' staff
        (the army counted whole)."""
        return self.employed(trade) + self._world.actors_staff_nationwide(trade)

    def reserved_hours(self, trade):
        """Hours a year reserved by employers for a trade."""
        return self.reserved_people(trade) * self._world.HOURS_PER_PERSON_YEAR

    def supplied_people(self, trade):
        """People of a trade the country supplies, the ceiling every reservation is held under."""
        return self.people_who_exist(trade)

    def unreserved_people(self, trade):
        """What is left of a trade's supply after every employer's reservation."""
        return max(0.0, self.supplied_people(trade) - self.reserved_people(trade))

    def core_people_by_trade(self):
        """Working people by trade in the agent economy's labour core; None while it opens."""
        return self._world.economy.agent_people_by_trade()

    def core_people_by_tile_and_trade(self):
        """The labour core's working people by tile, then trade; None while the economy opens."""
        return self._world.economy.agent_people_by_tile_and_trade()

    def hires_by_tile_and_trade(self):
        """The founder's staff by the tile they work from (the household's base tile) and trade."""
        staff = self.employed_by_trade()
        return {self.base_tile(): staff} if staff else {}

    def free_core_people_by_tile(self):
        """The core's people by tile and trade with the founder's hires taken out, so a person hired by the founder
        is not also counted as available to another employer; None while the economy opens."""
        core = self.core_people_by_tile_and_trade()
        return None if core is None else core_reservations.free_people(core, self.hires_by_tile_and_trade())

    def free_core_people(self, trade):
        """People of a trade the core holds that no hire of the founder's has taken; None while the economy opens."""
        free = self.free_core_people_by_tile()
        return None if free is None else sum(by_trade.get(trade, 0.0) for by_trade in free.values())

    def reservations_over_core(self):
        """(tile, trade, people hired, people the core holds there) for every hire of the founder's the core's people
        at that tile and trade do not cover; empty while the economy opens."""
        core = self.core_people_by_tile_and_trade()
        return [] if core is None else core_reservations.over_reserved(core, self.hires_by_tile_and_trade())
