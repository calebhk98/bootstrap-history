"""What the coin a run ties up costs its producer, under the clearing rule set.

A run's inputs and hours are paid for before its output sells, so the producer holds that money for the time between
(`producers_close.WORKING_CAPITAL_YEARS_OF_VARIABLE_COST`), its own or borrowed. Either way it costs the interest on it:
a lender charges it, and coin of its own could have been lent or paid out. So what is paid in advance costs that money
and the interest for the time it is tied up; rent, paid at the year's end, carries none. With this in a run's cost a
good at rest sells for enough to keep the coin its making needs, and a producer that must borrow its wage bill does not
sink under an interest no figure of its plan counted. The charge on plant is `unit_cost.capital_charge_per_run`; this is
its twin for coin."""
import math

from .producers_close import WORKING_CAPITAL_YEARS_OF_VARIABLE_COST
from .rates import own_rate


def share_charged(interest_rate: float, years_tied_up: float = WORKING_CAPITAL_YEARS_OF_VARIABLE_COST) -> float:
    """The share of a payment made in advance that its coin costs: the interest on it for the years it is tied up.
    Nothing at a rate of nothing or less, or at a rate that is no number."""
    if not math.isfinite(interest_rate) or interest_rate <= 0.0:
        return 0.0
    return interest_rate * max(0.0, years_tied_up)


def run_cost(paid_in_advance: float, paid_at_the_years_end: float, share: float) -> float:
    """A run's cost with the coin it ties up: what is paid in advance and the charge on it, and what is paid at the
    year's end as it is."""
    return paid_in_advance * (1.0 + share) + paid_at_the_years_end


def left_for_hours(room: float, share: float) -> float:
    """The wage bill a run can carry when `room` is what its revenue leaves after its other costs: the wage bill and
    the charge on it together fill the room."""
    return room / (1.0 + share)


def no_charge(_setup, _view) -> float:
    """The search rule set charges a run nothing for its coin."""
    return 0.0


def charge_at_the_going_rate(setup, view) -> float:
    """The share charged at the rate the economy's own currency lends at this year."""
    return share_charged(own_rate(view, setup.currency_id))
