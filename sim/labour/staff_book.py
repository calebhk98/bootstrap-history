"""Who is hired by whom: the one book of the founder's staff, and the views of every employer's staff
against the people the country supplies.

The founder's household keeps its staff as a trade-to-head-count map (`household.employees`); only this
mixin reads or writes it from labour, and code outside labour asks `sim.labour`. Firms and states keep
their own staff in the agent registry; `reserved_people` adds both so one trade's reservations read from
one place. Complaint 556.
"""


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
