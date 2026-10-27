"""The views of the acting seat's people, hours and pay books. Tables hold the live containers: read them, never write to them."""


class ViewsState:

    def staff(self):
        """The acting seat's people: hired hands by trade, its scholars, artisans, deputy directors, slaves and freedmen, and the
        spare hands it keeps in reserve."""
        seat = self.seat
        return {"employees": seat.employees, "scholars": seat.scholars, "artisans": seat.artisans,
                "directors_extra": seat.directors_extra, "slaves": seat.slaves, "freedmen": seat.freedmen,
                "manumitted_total": seat.manumitted_total, "reserve_craftsmen": seat.reserve_craftsmen,
                "reserve_scholars": seat.reserve_scholars}

    def training_queue(self):
        """The apprentices in training, one row per intake."""
        return self.seat.training

    def hour_commitments(self):
        """Where the acting seat's year of hours is promised and has gone."""
        seat = self.seat
        return {"allocations": seat.hour_allocations, "work_trade": seat.work_trade, "wage_hours": seat.wage_hours_this_year,
                "wage_income": seat.wage_income_this_year, "teaching_hours": seat.teaching_hours_this_year,
                "relocation_hours": seat.relocation_hours_this_year, "supervision_hours": seat.supervision_hours_this_year,
                "contract_hours": seat.contract_hours, "commissioned": seat.commissioned, "last_year": seat.hours_this_year,
                "wage_work_last_year": seat.wage_work_last_year, "trade_hours_used": seat.trade_hours_used,
                "unused_reported": seat.unused_hours_reported, "last_taught": seat.last_taught,
                "director_hours_spent": seat.director_hours_spent_founder}

    def pay_book(self):
        """The acting seat's pay books: wages paid in advance, wages its own work earned, the pay last settled by trade."""
        seat = self.seat
        return {"prepaid": seat.wages_prepaid, "earned": seat.wages_earned, "paid": seat.wages_paid, "pay_held": seat.staff_pay_held,
                "living_cost_paid": seat.living_cost_paid}

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
