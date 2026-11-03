"""The commands that change the acting seat's hours, pay books and people, applied by the workforce module."""
from sim.agents.api import edges
from sim.assembly.api import Part
from sim.ledger.api import PayEdge


class ApplyingHours(Part):

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

    def set_wage_hours_sold(self, command):
        self.seat.wage_hours_this_year = command.hours

    def set_reserve(self, command):
        if command.craftsmen is not None:
            self.seat.reserve_craftsmen = command.craftsmen
        if command.scholars is not None:
            self.seat.reserve_scholars = command.scholars

    def bleed_staff(self, command):
        self.parts.core.labour.pools.bleed(command.artisan_floor, command.bleed, command.scholar_floor,
                                           command.bleed * command.scholar_discount)

    def disperse_dependants(self, command):
        self.parts.core.labour.pools.disperse_dependants(command.artisan_floor, command.artisan_retention)

    def lose_crew(self, command):
        return self.parts.core.labour.pools.lose_crew(command.crew)

    def build_housing(self, command):
        places = float(command.places)
        cost = places * self.needs.housing_price_per_place()
        if places <= 0 or cost > self.needs.acting_balance():
            return 0.0
        refusal = self.needs.send(PayEdge(edges.EDGE_BUILDERS, cost, "worker housing built"))
        if refusal:
            return refusal
        self.seat.worker_housing_places = (self.seat.worker_housing_places or 0.0) + places
        return places
