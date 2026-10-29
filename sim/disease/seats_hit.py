"""What an epidemic year does to each playing seat: its staff, its deputies and its takings."""
from sim.hazards.api import LoseCapital, constants as hazard_constants
from sim.reporting.api import RecordEvent
from sim.workforce.api import ReportStaffReduction, ScaleDeputies, SurviveStaff

from . import rules
from .technology_effects import working_age_death_share


class SeatsHit:

    def hit_seats(self, command):
        """Cut each playing seat's people and cash by the working-age share the year's epidemics killed; the answer is
        that share (zero when nothing was done)."""
        share = working_age_death_share(command.deaths_by_band, float(self.needs.working_age()))
        if share < rules.EPIDEMIC_NOTICE_SHARE:
            return 0.0
        name = " and ".join(self._names or ["an epidemic"])
        for seat_id in self.needs.seat_list()["playing"]:
            with self.needs.act_as(seat_id):
                staff = self.needs.staff()
                people_before = staff["scholars"] + staff["artisans"] + sum(staff["employees"].values())
                staff_before = self.needs.staff_snapshot()
                self.needs.send(SurviveStaff(1 - share))
                self.needs.send(ScaleDeputies(1 - share))
                self.needs.send(ReportStaffReduction(name, staff_before))
                cash = self.needs.send(LoseCapital(share * hazard_constants.PLAGUE_CASH_LOSS_SHARE, "plague losses"))
                cash_text = self.needs.money_text(cash, grouped=True) if cash > 0.5 else ""
                text, took_nothing = rules.seat_loss_report(name, share, people_before, cash, cash_text)
                self.needs.send(RecordEvent.in_year(command.year, "hazard_hit", text, hazard=name, took_nothing=took_nothing,
                                                    lapsed_hedges=[]))
        return share
