"""What debt costs against what the household earns every year.

The formal credit ceiling (credit_limit) says how much anyone will lend; this
says how much debt the recurring surplus can carry. One method per figure, read
by `money`, `state` and the start warning alike.
"""
from sim.constants import declare


class DebtServiceMixin:

    DEBT_SERVICE_SHARE_OF_SURPLUS = declare(
        "DEBT_SERVICE_SHARE_OF_SURPLUS", 0.5, kind="temporary_heuristic",
        unit="fraction of the recurring surplus", source=None, confidence="D",
        why="How much of the yearly surplus may go on arrears interest before "
            "a debt is called unsustainable, leaving the rest to pay the "
            "principal down. A tuned prudence level, not a lender's rule.")

    def recurring_net_before_interest(self):
        """Standing revenue less every standing cost, for an ordinary next
        year: wages count in full, so a hiring advance paid this year does not
        flatter it."""
        revenue = self.revenue_capacity()
        upkeep = self.upkeep()
        living = self.living_cost(_rev=revenue, _upkeep=upkeep)
        return revenue - upkeep - living - self.mine_operating_cost()

    def recurring_net(self):
        """Recurring net after the interest arrears cost now."""
        return (self.recurring_net_before_interest()
                - max(0.0, -self.state.household.capital) * self.debt_interest_rate())

    def sustainable_debt(self):
        """The largest debt whose yearly interest stays within the allowed
        share of the recurring surplus (zero when there is no surplus)."""
        rate = self.debt_interest_rate()
        surplus = self.recurring_net_before_interest()
        if rate <= 0:
            return 0.0
        return max(0.0, surplus * self.DEBT_SERVICE_SHARE_OF_SURPLUS / rate)

    def debt_service_forecast(self, draw):
        """Interest on a debt of `draw`, against the surplus, beside the
        formal ceiling."""
        surplus = self.recurring_net_before_interest()
        interest = draw * self.debt_interest_rate()
        return {
            "interest_per_year_at_that_draw": round(interest, 1),
            "recurring_surplus_before_interest": round(surplus, 1),
            "interest_as_share_of_recurring_surplus": (
                round(interest / surplus, 2) if surplus > 0 else None),
            "sustainable_debt": round(self.sustainable_debt(), 1),
            "sustainable_debt_means": (
                "the largest debt whose yearly interest stays within %d%% of "
                "your recurring surplus; the credit limit is only what "
                "lenders will allow, not a safe level"
                % round(self.DEBT_SERVICE_SHARE_OF_SURPLUS * 100)),
        }
