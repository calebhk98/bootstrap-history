"""A household's standing job: the hours it has not spoken for are sold in a trade it holds, at that trade's
market wage, the way any worker's are.

Methods of Labour, split from labour_wages.py, which prices the trade and sells hours on request.
"""


from .founder_hours import hours_free


class StandingJobMixin:
    """Hours left to sell, and what they pay in a given trade."""

    def hours_for_sale(self):
        """Hours of the year the household has not spoken for (teaching, moving, supervising its own
        businesses, hours already sold on request); none once the founder is dead. TEMPORARY HEURISTIC:
        hours put into the household's own projects are not taken out (they are worked alongside the job)
        until a project's hours are the hours of a seat."""
        if not self._world.founder_alive:
            return 0.0
        return hours_free(self.director_pool(), self.director_hours_committed())

    def standing_job_pay(self, trade):
        """A year of the unspoken-for hours sold in `trade` at its market wage; nothing without a trade."""
        if trade is None:
            return 0.0
        return self.wage_for_hours(trade, self.hours_for_sale())

    def wage_signature(self):
        """A cheap fingerprint of what moves a trade's market wage within a year (the hiring pressure on
        it), for callers that cache a figure derived from `standing_job_pay`."""
        return self.labour_market.pressure_signature()
