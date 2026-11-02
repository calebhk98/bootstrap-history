"""The books on selling your own hours on request: the hours offered, what the clearing paid last year, and a dry run before committing.

Methods of Labour, split from labour_wages.py, which prices the trade.
"""
from sim.reporting.api import RecordEvent


class WageLedgerMixin:
    """Hours offered on request this year, and what the clearing paid for them last year."""

    def wage_work_this_year(self):
        """Hours offered on request so far this year (the pay comes with the year's clearing)."""
        workforce = self._world.workforce
        if workforce.wage_hours_this_year <= 0:
            return {}
        return {"hours": round(workforce.wage_hours_this_year, 1)}

    def close_wage_year(self):
        """Keep the year's wage-work books as last year's (the clearing adds the pay when it comes), then clear them."""
        workforce = self._world.workforce
        summary = self.wage_work_this_year()
        if summary:
            summary["year"] = self._world.year
            summary["wage_income"] = 0.0
        workforce.wage_work_last_year = summary or None
        workforce.wage_hours_this_year = 0.0

    def log_wage_work(self, trade, hours, pay):
        """One log line saying what the offer should earn at the market wage."""
        self._world.send(RecordEvent.of("wage_work_sold", "wage work: offered %s hours as a %s, about %s at this year's clearing"
                    % (self._world.plain_number(hours), trade, self._world.money_text(pay, grouped=True, short=True)), trade=trade, hours=hours, pay=pay))

    def work_for_wages_dry_run(self, trade, hours):
        """(pay, message) for work_for_wages as a quote: nothing is posted, logged or kept."""
        return self.work_for_wages(trade, hours, commit=False)
