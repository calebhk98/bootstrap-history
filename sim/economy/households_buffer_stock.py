"""A household's spending from its mean net income, its cash and the shares it owns.

Follows Eurace@Unibi (ETACE/eurace_unibi, used with the authors' permission; see NOTICE.md),
`Household_determine_consumption_budget` in Cons_Goods/Household_Consumer_Functions.c, lines 56-57:
    budget = mean net income + carrol * payment account + trading * carrol * (share wealth - target * mean net income)
and line 127 (without trading the budget is capped at the payment account). The Carroll rule on total wealth that
the manual (section 3.3.2) describes is commented out in that file; this follows the live line. The C sets no
default for either constant; the manual's section 10.1.3 gives them.
"""
from typing import Optional

from sim.constants import declare

MONTHS_PER_YEAR = 12

CARROL_CONSUMPTION_PARAMETER = declare(
    "CARROL_CONSUMPTION_PARAMETER", 0.01, kind="temporary_heuristic",
    unit="share of the payment account spent each month, on top of income",
    source=(
        "Eurace@Unibi user manual (documents/EuraceUnibi-UserManual.pdf, section 10.1.3, 'carrol consumption "
        "parameter', opened): 0.01. The C (Cons_Goods/Household_Consumer_Functions.c) has no default; it declares "
        "the variable only. Not measured for any pre-modern society."), confidence="D",
    why="The monthly share of cash a household spends beyond its income; the yearly share compounds it "
        "(`yearly_cash_share`). A method driven by income risk, age and the return on saving would replace it.",
    retire="Complaints/606: a method driven by income risk, age and the return on saving replaces the stored share")
WEALTH_INCOME_RATIO_TARGET = declare(
    "WEALTH_INCOME_RATIO_TARGET", 16.67, kind="temporary_heuristic",
    unit="monthly mean net incomes held as share wealth, above which share wealth is spent",
    source=(
        "Eurace@Unibi user manual (section 10.1.3, 'wealth income ratio target', opened): 16.67. The C has no "
        "default. Not measured for any pre-modern society."), confidence="D",
    why="Share wealth above this many months of income adds to spending, below it cuts spending, at the "
        "carrol share. One value for every household.",
    retire="Complaints/606: a method driven by income risk, age and the return on saving replaces the stored ratio")


def yearly_cash_share(monthly_share: float = None) -> float:
    """The share of an account spent in a year when `monthly_share` of what is left is spent each month:
    one minus the share left after twelve months. (Eurace spends the monthly share each month.)"""
    monthly_share = CARROL_CONSUMPTION_PARAMETER if monthly_share is None else monthly_share
    return 1.0 - (1.0 - monthly_share) ** MONTHS_PER_YEAR


def spending_budget(mean_net_income: float, cash: float, share_wealth: float, claims: float = 0.0) -> float:
    """Spending for the year, after Eurace's `Household_determine_consumption_budget`: mean net income, plus the
    yearly share of cash, plus (when the household owns shares) the yearly share of share wealth over the target
    of WEALTH_INCOME_RATIO_TARGET months of mean net income. Never above cash (Eurace's cap without trading,
    line 127) and never negative. Eurace's payment account is a bank deposit, a claim on the bank; the money a
    household has lent here (`claims`) is the same kind of holding, so it is in the account the share applies to
    (a default cuts it), while only cash can be spent."""
    budget = mean_net_income + yearly_cash_share() * (cash + claims)
    if share_wealth > 0.0:
        target = WEALTH_INCOME_RATIO_TARGET / MONTHS_PER_YEAR * mean_net_income
        budget += yearly_cash_share() * (share_wealth - target)
    return max(0.0, min(cash, budget))


def share_wealth_carried(recorded: Optional[float], current: float) -> float:
    """The share wealth the spending rule reads for the year: what the household owned at the last close (year end,
    producers' cash back from the year's sales), not the reading at the goods orders, by which the producers have paid
    the year's wages and what they own is mostly out of their accounts. With no record (a new household) the
    current reading."""
    return current if recorded is None else recorded


def mean_net_income(income_this_year: float, last_year_income: float) -> float:
    """Eurace's MEAN_NET_INCOME (Labour/Household_Employee_Functions.c, line 1012) is the mean of the last
    LAST_NET_INCOME months. Here it is the mean of this year's and last year's income (the window is ours); with no
    last year it is this year's."""
    if last_year_income <= 0.0:
        return income_this_year
    return 0.5 * (income_this_year + last_year_income)
