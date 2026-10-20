"""What a year's epidemic takes from every seat: the share of the nation's working-age people the disease model killed
is the share of each seat's staff (and takings) lost. The deaths come from the model, not from a hazard table."""
from sim.refusal import LogLine

from .units_prose import money_text

# below this share of working-age people dead, a seat notices nothing
EPIDEMIC_NOTICE_SHARE = 0.002


class EpidemicStaffMixin:

    def epidemic_hits_seats(self, deaths_by_band, year):
        """Cut each playing seat's people and cash by the working-age share the year's epidemics killed; the reply
        is that share (zero when nothing was done)."""
        working_age = float(self.population.working_age)
        share = deaths_by_band.get("working_age", 0.0) / (working_age + deaths_by_band.get("working_age", 0.0)) if working_age > 0 else 0.0
        if share < EPIDEMIC_NOTICE_SHARE:
            return 0.0
        names = self.__dict__.get("_epidemic_names") or ["an epidemic"]
        name = " and ".join(names)
        for seat_id in self.playing_seats():
            with self.act_as(seat_id):
                household = self.state.household
                people_before = household.scholars + household.artisans + sum(household.employees.values())
                staff_before = self.labour.staff_snapshot()
                self.apply_staff_survival(1 - share)
                household.directors_extra *= (1 - share)
                self.labour.log_staff_reduction(name, staff_before)
                cash = self.lose_capital(share * self.PLAGUE_CASH_LOSS_SHARE, "plague losses")
                parts = ["staff -%d%%" % round(share * 100)] if people_before > 0.05 else []
                if cash > 0.5:
                    parts.append("%s of takings lost while the trade stood idle" % money_text(cash, self, grouped=True))
                took_nothing = not parts
                household.log.append((year, LogLine(
                    "hazard_hit", "%s: %s. Empire-wide, %d%% of working-age people died" % (
                        name, ", ".join(parts) or "you had nothing it could take", round(share * 100)),
                    hazard=name, took_nothing=took_nothing, lapsed_hedges=[])))
        return share
