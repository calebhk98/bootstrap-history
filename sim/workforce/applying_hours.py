"""The commands that change the acting seat's hours, pay books and people, applied by the workforce module."""
from sim.agents.api import edges
from sim.ledger.api import PayEdge

from . import rules


class ApplyingHours:

    def allocate_hours(self, command):
        self.seat.hour_allocations[command.target] = float(command.hours)

    def release_hours(self, command):
        return self.seat.hour_allocations.pop(command.target, None)

    def order_work(self, command):
        self.seat.hour_allocations["work"] = float(command.hours)
        self.seat.work_trade = command.trade

    def cancel_work(self, command):
        had = self.seat.hour_allocations.pop("work", None)
        self.seat.work_trade = None
        return had

    def draw_trade_hours(self, command):
        used = self.seat.trade_hours_used
        used[command.trade] = used.get(command.trade, 0.0) + command.hours

    def reset_trade_hours(self, command):
        self.seat.trade_hours_used = {}

    def spend_director_hours(self, command):
        self.seat.director_hours_spent_founder += command.hours

    def settle_living_cost(self, command):
        self.seat.wages_prepaid = 0.0
        self.seat.living_cost_paid += command.amount

    def set_wage_hours_sold(self, command):
        self.seat.wage_hours_this_year = command.hours

    def set_reserve(self, command):
        if command.craftsmen is not None:
            self.seat.reserve_craftsmen = command.craftsmen
        if command.scholars is not None:
            self.seat.reserve_scholars = command.scholars

    def bleed_staff(self, command):
        seat = self.seat
        seat.artisans = max(command.artisan_floor, seat.artisans * (1.0 - command.bleed))
        seat.scholars = max(command.scholar_floor, seat.scholars * (1.0 - command.bleed * command.scholar_discount))

    def disperse_dependants(self, command):
        seat = self.seat
        seat.freedmen = 0
        seat.artisans = max(command.artisan_floor, seat.artisans * command.artisan_retention)

    def lose_crew(self, command):
        employees = self.seat.employees
        dice = self.needs.game_random()
        lost = []
        for trade, share in command.crew:
            have = employees.get(trade, 0.0)
            kept = rules.surviving_people(dice, have, 1.0 - share)
            if kept > 0:
                employees[trade] = kept
            else:
                employees.pop(trade, None)
            lost.append((trade, have, kept))
        return tuple(lost)

    def build_housing(self, command):
        places = float(command.places)
        cost = places * self.needs.housing_price_per_place()
        if places <= 0 or cost > self.needs.acting_balance():
            return 0.0
        self.needs.send(PayEdge(edges.EDGE_BUILDERS, cost, "worker housing built"))
        self.seat.worker_housing_places = (self.seat.worker_housing_places or 0.0) + places
        return places
