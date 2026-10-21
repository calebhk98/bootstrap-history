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


def year_bill(cost_left, project_cost, year_share):
    """What a project asks for this year: the instalment its constrained year can do (the whole cost scaled by the
    share of the work the year managed), never more than is left. A shortage so sets how fast the bill is paid and
    never stops the last payment landing."""
    return min(cost_left, project_cost * year_share)


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


def cash_covers_start(price, paid_towards, owed_on_work_in_hand, capital):
    """Whether cash in hand pays for a start (its price less what is already paid towards it) on top of what work
    in hand still owes."""
    price -= min(price, max(0.0, paid_towards or 0.0))
    return owed_on_work_in_hand + price <= capital


def funding_parts(capital, revenue, fixed_costs, debt_interest_rate, credit_line, draw_share, surplus_years,
                  committed):
    """What can be spent on projects, kept in parts: cash held, the drawable share of the credit line less what is
    already drawn (arrears use up the room), the yearly surplus over fixed costs (arrears interest included) and
    its allowance over the planning years, and what work in hand still owes."""
    fixed = fixed_costs + max(0.0, -capital) * debt_interest_rate
    surplus = max(0.0, revenue - fixed)
    return {"cash_on_hand": max(0.0, capital),
            "credit_available_now": max(0.0, credit_line * draw_share - max(0.0, -capital)),
            "sustainable_annual_surplus": surplus,
            "surplus_allowance_over_years": surplus * surplus_years,
            "surplus_years_counted": surplus_years,
            "already_committed": committed}
