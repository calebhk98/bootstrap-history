"""The books on selling your own hours on request: what the wage brought in, and a dry run before committing.

Methods of Labour, split from labour_wages.py, which prices the trade.
"""
from sim.reporting.api import DiscardEventsAfter, RecordEvent


class WageLedgerMixin:
    """Wage income from hours sold on request, this year and last."""

    def wage_work_this_year(self):
        """Hours sold on request and pay taken so far this year."""
        household = self._world.state.household
        if household.wage_hours_this_year <= 0:
            return {}
        return self._wage_work_summary(household.wage_hours_this_year,
                                       household.wage_income_this_year)

    def _wage_work_summary(self, hours, income):
        return {"hours": round(hours, 1), "wage_income": round(income, 1)}

    def close_wage_year(self):
        """Keep the year's wage-work books as last year's, then clear them."""
        household = self._world.state.household
        summary = self.wage_work_this_year()
        if summary:
            summary["year"] = self._world.state.scenario.year
        household.wage_work_last_year = summary or None
        household.wage_hours_this_year = 0.0
        household.wage_income_this_year = 0.0

    def log_wage_work(self, trade, hours, pay):
        """One log line saying what the sale earned."""
        self._world.send(RecordEvent.of("wage_work_sold", "wage work: sold %s hours as a %s for %s"
                    % (self._world.plain_number(hours), trade, self._world.money_text(pay, grouped=True, short=True)), trade=trade, hours=hours, pay=pay))

    def work_for_wages_dry_run(self, trade, hours):
        """(pay, message) for work_for_wages, with every book put back afterwards."""
        household = self._world.state.household
        saved = (household.capital, household.wage_hours_this_year,
                 household.wage_income_this_year, household.wages_earned,
                 self._world.logged_events())
        try:
            return self.work_for_wages(trade, hours)
        finally:
            (household.capital, household.wage_hours_this_year,
             household.wage_income_this_year, household.wages_earned,
             logged) = saved
            self._world.send(DiscardEventsAfter(logged))
