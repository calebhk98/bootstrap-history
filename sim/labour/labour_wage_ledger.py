"""The books on selling your own hours: what the wage brought in, what the
practice lost for it, and a dry run before committing.

Methods of Labour, split from labour_wages.py, which prices the trade.
"""


class WageLedgerMixin:
    """Wage income and the practice income it displaces, this year and last."""

    def practice_income_displaced(self):
        """Practice income this year's wage hours cost, at the standing rate."""
        return max(0.0, self._world.revenue_capacity() - self._world.revenue())

    def wage_work_this_year(self):
        """Hours sold, pay taken and practice income given up so far this year."""
        household = self._world.state.household
        if household.wage_hours_this_year <= 0:
            return {}
        return self._wage_work_summary(household.wage_hours_this_year,
                                       household.wage_income_this_year)

    def _wage_work_summary(self, hours, income):
        displaced = self.practice_income_displaced()
        return {"hours": round(hours, 1), "wage_income": round(income, 1),
                "practice_income_displaced": round(displaced, 1),
                "net": round(round(income, 1) - round(displaced, 1), 1)}

    def close_wage_year(self):
        """Keep the year's wage-work books as last year's, then clear them."""
        household = self._world.state.household
        summary = self.wage_work_this_year()
        if summary:
            summary["year"] = self._world.state.scenario.year
        household.wage_work_last_year = summary or None
        household.wage_hours_this_year = 0.0
        household.wage_income_this_year = 0.0

    def log_wage_work(self, trade, hours, pay, displaced):
        """One log line saying what the sale earned and what it cost."""
        self._world.state.household.log.append((
            self._world.state.scenario.year,
            "wage work: sold %s hours as a %s for %s; your practice will "
            "earn %s less this year, so the net is %s"
            % (self._world.plain_number(hours), trade, self._world.money_text(pay, grouped=True, short=True),
               self._world.money_text(displaced, grouped=True, short=True),
               ("+" if round(pay) >= round(displaced) else "-")
               + self._world.money_text(abs(round(pay) - round(displaced)), grouped=True, short=True))))

    def work_for_wages_dry_run(self, trade, hours):
        """(pay, message, practice income given up) for work_for_wages, with
        every book put back afterwards."""
        household = self._world.state.household
        saved = (household.capital, household.wage_hours_this_year,
                 household.wage_income_this_year, household.wages_earned,
                 len(household.log))
        revenue_before = self._world.revenue()
        try:
            pay, message = self.work_for_wages(trade, hours)
            return pay, message, revenue_before - self._world.revenue()
        finally:
            (household.capital, household.wage_hours_this_year,
             household.wage_income_this_year, household.wages_earned,
             log_length) = saved
            del household.log[log_length:]
