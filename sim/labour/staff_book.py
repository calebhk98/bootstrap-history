"""The one book of the founder's staff: who is hired, who is posted for, who arrives, and the reservations
of every employer against the people the labour core holds.

The founder's household keeps its staff as a trade-to-head-count map (the workforce module's `employees`); only
this part reads or writes it from labour. Firms and states keep their own staff in the agent registry;
`reserved_people` adds both so one trade's reservations read from one place. Complaint 556."""
from .labour_wage_schedule import person_year_hours


class StaffBook:
    def __init__(self, world):
        self._world = world

    def employed(self, trade):
        """People of one trade on the founder's books."""
        return self._world.workforce.employees.get(trade, 0.0)

    def employed_by_trade(self):
        """A copy of the founder's staff, trade to head count."""
        return dict(self._world.workforce.employees)

    def employed_total(self):
        """Everyone on the founder's books."""
        return sum(self._world.workforce.employees.values())

    def staff_posting(self):
        """{trade: people} the founder's household has posted in the labour core: the places its staff are hired into."""
        return dict(self._world.workforce.staff_wanted)

    def once_posting(self):
        """{purpose: {trade: hours}} the founder's household asks the labour core for this year only."""
        return {purpose: dict(orders) for purpose, orders in self._world.workforce.hours_wanted_once.items() if orders}

    def wage_work_offered(self):
        """{trade: hours} the founder offers of its own in the labour core this year; paid what the clearing hires of them."""
        return {trade: hours for trade, hours in self._world.workforce.hours_offered_for_wages.items() if hours > 0.0}

    def newcomers(self):
        """{trade: people} trained or granted since the last clearing who are not yet in the labour core."""
        return {trade: people for trade, people in self._world.workforce.newcomers.items() if people > 0.0}

    def add_newcomers(self, trade, people):
        """Take `people` more of a trade onto the founder's books and queue them for the labour core, where they are hired like anyone."""
        if people <= 0.0:
            return
        self.add_employed(trade, people)
        newcomers = self._world.workforce.newcomers
        newcomers[trade] = newcomers.get(trade, 0.0) + people

    def set_employed(self, trade, people):
        """Put the founder's head count of a trade at `people`; a count of nothing leaves the trade off the books."""
        workforce = self._world.workforce
        employees = workforce.employees
        if people != employees.get(trade, 0.0):    # a change made outside the clearing moves the standing bid with it
            wanted = max(0.0, workforce.staff_wanted.get(trade, 0.0) + people - employees.get(trade, 0.0))
            if wanted:
                workforce.staff_wanted[trade] = wanted
            else:
                workforce.staff_wanted.pop(trade, None)
        if people:
            employees[trade] = people
        else:
            employees.pop(trade, None)

    def add_employed(self, trade, people):
        """Take `people` more (or fewer, when negative) of a trade onto the founder's books."""
        self.set_employed(trade, self.employed(trade) + people)

    def reserved_people(self, trade):
        """People of a trade already given to an employer: the founder's staff, and the home country's firms' and
        states' staff (the army counted whole)."""
        return self.employed(trade) + self._world.actors.actor_staff_fte(trade)

    def reserved_hours(self, trade):
        """Hours a year reserved by employers for a trade."""
        return self.reserved_people(trade) * person_year_hours(self._world)

    def core_people_by_trade(self):
        """Working people by trade in the agent economy's labour core; None while it opens."""
        return self._world.economy.agent_people_by_trade()

    def headcount(self):
        workforce = self._world.workforce
        return self.employed_total() + workforce.slaves + workforce.freedmen

    def trade_headcount_pending(self, trade):
        """People already on the books in this trade, plus people already
        being taught into it who are not ready yet - what a fresh hire or a
        fresh training run would be added ON TOP OF."""
        workforce = self._world.workforce
        pending = sum(row[3] for row in workforce.training
                      if len(row) > 3 and row[2] == trade)
        return max(self.employed(trade), self._world.workforce.staff_wanted.get(trade, 0.0)) + pending

    def staff_posted(self):
        """People wanted in the labour core for the household beyond those it hired at the last clearing."""
        workforce = self._world.workforce
        return sum(max(0.0, wanted - workforce.employees.get(name, 0.0)) for name, wanted in workforce.staff_wanted.items())
