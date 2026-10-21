"""What debt costs against what the household earns every year.

The formal credit ceiling (credit_limit) says how much anyone will lend; this
says how much debt the recurring surplus can carry. One method per figure, read
by `money`, `state` and the start warning alike.
"""
from sim.constants import declare


def interest_on_arrears(capital, rate):
    """The yearly interest on a debt: nothing while the purse is in credit."""
    return max(0.0, -capital) * rate


def net_after_interest(net_before_interest, capital, rate):
    """Recurring net once the interest on any debt is counted as the cost it is."""
    return net_before_interest - interest_on_arrears(capital, rate)


def dependants_not_carried(dependants, surplus, creditors_share):
    """The part of the dependants' cost the income cannot carry: what the surplus leaves after the creditors' share,
    never more than the dependants cost and never less than nothing."""
    carried = surplus * (1.0 - creditors_share)
    return dependants - min(dependants, max(0.0, carried))


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
        return revenue - upkeep - self.recurring_living_cost(revenue, upkeep) - self.mine_operating_cost()

    def dependants_beyond_means(self, living, revenue, upkeep, mine_cost=0.0):
        """The part of the dependants' cost the household cannot carry this year: what its income leaves after
        upkeep, mine costs, the rest of its living cost and the interest on any arrears. A household with savings
        keeps all that surplus for its dependants (its savings are not spent on them); one in arrears also pays the
        creditors their share of it (DEBT_SERVICE_SHARE_OF_SURPLUS). Either way it lives within its income, as a
        society household of the same income does, so a lone scholar's wage that covers one person's subsistence
        does not bleed the purse for a household the wage cannot keep."""
        capital = self.state.household.capital
        dependants = self.dependants_cost()
        interest = interest_on_arrears(capital, self.debt_interest_rate())
        surplus = revenue - upkeep - mine_cost - (living - dependants) - interest
        creditors_share = self.DEBT_SERVICE_SHARE_OF_SURPLUS if capital < 0 else 0.0
        return dependants_not_carried(dependants, surplus, creditors_share)

    def recurring_living_cost(self, revenue, upkeep):
        """The living cost of an ordinary next year: what is paid once the dependants the income cannot carry are shed."""
        living = self.living_cost(_rev=revenue, _upkeep=upkeep)
        return living - self.dependants_beyond_means(living, revenue, upkeep, self.mine_operating_cost())

    def recurring_net(self):
        """Recurring net after the interest arrears cost now."""
        return net_after_interest(self.recurring_net_before_interest(), self.state.household.capital,
                                  self.debt_interest_rate())

    def interest_on_arrears(self):
        """This year's interest on the household's debt at the rate it pays."""
        return interest_on_arrears(self.state.household.capital, self.debt_interest_rate())

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
