"""The views of the acting seat's people, hours and pay books. Tables hold the live containers: read them, never write to them."""
from sim.assembly.api import Part


class ViewsState(Part):

    def staff(self):
        """The acting seat's people: hired hands by trade, its scholars, artisans, deputy directors, slaves and freedmen, and the
        spare hands it keeps in reserve."""
        seat = self.seat
        return {"employees": seat.employees, "scholars": seat.scholars, "artisans": seat.artisans,
                "directors_extra": seat.directors_extra, "slaves": seat.slaves, "freedmen": seat.freedmen,
                "manumitted_total": seat.manumitted_total, "reserve_craftsmen": seat.reserve_craftsmen,
                "reserve_scholars": seat.reserve_scholars}

    def staff_wanted(self):
        """{trade: people} the acting seat has posted in the labour core: the standing bid its staff are hired through."""
        return self.seat.staff_wanted

    def staff_on_all_books(self, trade):
        """People of `trade` on the payroll of every seat together."""
        return sum(self.seat_of(seat_id).employees.get(trade, 0.0) for seat_id in self.needs.seat_list()["joined"])

    def training_queue(self):
        """The apprentices in training, one row per intake."""
        return self.seat.training

    def hour_commitments(self):
        """Where the acting seat's year of hours is promised and has gone."""
        seat = self.seat
        return {"allocations": seat.hour_allocations, "work_trade": seat.work_trade, "wage_hours": seat.wage_hours_this_year,
                "teaching_hours": seat.teaching_hours_this_year, "last_year": seat.hours_this_year,
                "wage_work_last_year": seat.wage_work_last_year, "trade_hours_used": seat.trade_hours_used,
                "unused_reported": seat.unused_hours_reported}

    def pay_book(self):
        """The acting seat's pay book: what the last clearing charged it for its staff and one-year orders (the payroll at the
        market wage before any clearing)."""
        return {"paid_in_clearing": self.parts.fact_views.wages_charged_last_year()}

    def trade_schools(self):
        """{trade: training seats the acting seat has founded}."""
        return self.seat.trade_schools or {}

    def worker_housing_places(self):
        """Places of worker housing the acting seat has bought."""
        return self.seat.worker_housing_places or 0.0

    def trade_spread(self):
        """{absent: the trades that do not exist until taught, created: those the seat taught, endemic: those the society
        has, introduced_year: the year each was first seen taught}; the last three are live."""
        seat = self.seat
        return {"absent": sorted(self.needs.trades_absent()), "created": seat.trades_created,
                "endemic": seat.trades_endemic, "introduced_year": seat.trade_introduced_year}

    def society_labour_hours(self):
        """{trade: labour hours the society's workers of the trade give in a year}."""
        return self.world.society_labour_hours
