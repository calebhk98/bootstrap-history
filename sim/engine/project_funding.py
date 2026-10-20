"""What a household can pay a project in a year, and what a shortfall costs the project in hours. Plain arithmetic
on the numbers handed in."""
from typing import NamedTuple, Optional

CREDIT_DRAW_SHARE = 0.6
ARREARS_HOURS_NOTICED = 1.0

WHY_IN_ARREARS = ("in arrears: after fixed costs there is nothing left to draw on, so the hours offered "
                  "this year did almost nothing")
WHY_INSTALMENT = "this year's instalment is more than the purse will bear"


class YearFunding(NamedTuple):
    money: float             # what the project is paid this year
    refunded: float          # hours handed back so far, the trade-shortage refund included
    gave_back: float         # hours handed back by this shortfall
    underfunded: bool
    why: Optional[str]
    hours_lost_to_arrears: float   # the hours given back while in arrears, when they were worth reporting


def project_purse(capital, credit_limit, fixed_costs, revenue):
    """What the household may draw on for projects: its capital and part of its credit line, less the shortfall of
    its fixed costs over revenue (revenue already covers the rest)."""
    return capital + credit_limit * CREDIT_DRAW_SHARE - max(0.0, fixed_costs - revenue)


def fund_year(money, purse, spent_hours, refunded, hours_offered, in_arrears):
    """A project's bill (`money`) against the household's `purse`. A bill the purse covers, or no bill at all (a
    project paid in full only waits on the calendar, however deep the household's arrears), is paid whole. Past the
    purse the project is paid what the purse holds and gets back the hours offered in proportion to the unfunded
    part, never more than was taken off and not yet handed back."""
    if not (money > 0 and money > purse):
        return YearFunding(money, refunded, 0.0, False, None, 0.0)
    funded_share = max(0.0, min(1.0, purse / money))
    give_back = max(0.0, min(spent_hours - refunded, hours_offered * (1.0 - funded_share)))
    lost = give_back if in_arrears and give_back > ARREARS_HOURS_NOTICED else 0.0
    return YearFunding(max(0.0, purse), refunded + give_back, give_back, True,
                       WHY_IN_ARREARS if in_arrears else WHY_INSTALMENT, lost)
