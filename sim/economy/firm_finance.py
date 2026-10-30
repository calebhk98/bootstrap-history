"""A producer's year-end finances, after Eurace@Unibi's firm financial management (Financial_Management/
Firm_Financial_Management_Functions.c): the income statement, the dividend rule, the liquidity needs and the two
bankruptcy routes. Pure functions on numbers; year_close.py applies them to the record.

Eurace runs monthly and we run yearly, so a "month" of its history is a year here. Our loans are serviced before the
close (lending.py), so what Eurace calls payments the firm cannot make is, here, arrears left after that service.
Not ported: the tax on earnings (our producers pay no profit tax), the interest on deposits (their cash earns none),
and the innovation and R&D costs.
"""
from typing import Iterable, NamedTuple, Sequence, Tuple

from sim.constants import declare

from .replaced import replaced

HISTORY_YEARS = declare(
    "HISTORY_YEARS", 5, kind="temporary_heuristic", unit="years of net earnings and revenue a producer remembers",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi, Financial_Management/Firm_Financial_Management_Functions.c, Firm_compute_income_statement and "
        "Firm_compute_dividends smooth net earnings over a few months of history (five kept) and revenue over six. "
        "Its months are our years; the length here is the same count, with no source for either.")
DIVIDEND_EARNINGS_RATIO = declare(
    "DIVIDEND_EARNINGS_RATIO", 0.7, kind="temporary_heuristic", unit="share of average net earnings paid out",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi, Firm_compute_dividends: below the cash threshold a firm pays const_dividend_earnings_ratio of its "
        "smoothed net earnings. No source found for its value (the cloned repository sets none; a unit test there uses "
        "0.01). This is a placeholder until payout follows owners' need for income.")
FULL_PAYOUT_YEARS_OF_REVENUE = declare(
    "FULL_PAYOUT_YEARS_OF_REVENUE", 0.25, kind="temporary_heuristic", unit="years of average revenue held as cash",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi, Firm_compute_dividends: a firm whose cash exceeds const_dividend_treshold_full_payout times its "
        "average revenue pays out all of its smoothed net earnings. No source found for the threshold's value; stated "
        "here in years of revenue because Eurace's revenue is a month's.")
DEBT_RESCALING_FACTOR = declare(
    "DEBT_RESCALING_FACTOR", 1.0 / 3.0, kind="temporary_heuristic", unit="target debt over assets after bankruptcy",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi, Firm_bankruptcy_rescale_loans: a bankrupt firm's debt is written down to this share of its "
        "assets. The value is the one Eurace's own unit tests set (Financial_Management/unittests/"
        "Firm_Financial_Management_unittests_new.c); the model sets its own at run time and none was found.")
BANKRUPTCY_IDLE_YEARS = declare(
    "BANKRUPTCY_IDLE_YEARS", 1, kind="temporary_heuristic", unit="years a bankrupt producer stays idle",
    source=None, confidence="D", retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi, Firm_set_bankruptcy_illiquidity and Firm_set_bankruptcy_insolvency: a bankrupt firm is inactive "
        "for const_bankruptcy_idle_period iterations before it resumes. Its unit tests use 240, a year of its 20-day "
        "months; no source for the model's own value.")
ARREARS_EPSILON = 1e-9


class Liquidity(NamedTuple):
    total: float        # production needs plus financial commitments plus dividend
    external: float     # what the cash lacks of that


def net_earnings(revenue: float, running_costs: float, interest: float, depreciation: float) -> float:
    """Eurace@Unibi, Firm_compute_income_statement: earnings are revenue less production costs and interest paid
    (no tax or deposit interest here); `depreciation` is the plant that wore out, at replacement cost."""
    return revenue - running_costs - interest - depreciation


def appended(history: Iterable[float], value: float) -> Tuple[float, ...]:
    """Eurace@Unibi, Firm_compute_income_statement: the history of earnings drops its oldest entry and takes the new."""
    return tuple(history)[-(HISTORY_YEARS - 1):] + (value,) if HISTORY_YEARS > 1 else (value,)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def dividend_total(net_earnings_history: Sequence[float], revenue_history: Sequence[float], cash: float) -> Tuple[float, bool]:
    """Eurace@Unibi, Firm_compute_dividends: (the dividend, whether it is a full payout). Cash under the threshold
    times average revenue, or no revenue: the payout ratio of average net earnings; cash over it: all of them. Never
    negative."""
    average_revenue = _mean(revenue_history)
    average_earnings = max(0.0, _mean(net_earnings_history))
    if average_revenue < 1e-6 or cash < FULL_PAYOUT_YEARS_OF_REVENUE * average_revenue:
        return DIVIDEND_EARNINGS_RATIO * average_earnings, False
    return average_earnings, True


def liquidity_needs(cash: float, production: float, financial: float, dividend: float) -> Liquidity:
    """Eurace@Unibi, Firm_compute_total_liquidity_needs: production needs, commitments and the dividend, and what the
    payment account lacks of them (credit makes up the rest)."""
    total = production + financial + dividend
    return Liquidity(total, max(0.0, total - cash))


def financial_state(cash: float, payable: float, total_needs: float) -> str:
    """Eurace@Unibi, Firm_check_financial_and_bankruptcy_state: "illiquid" when the cash is short of the commitments
    payable, "crisis" when it covers them but not the total needs, else "ok"."""
    if cash >= total_needs:
        return "ok"
    return "crisis" if cash >= payable - 1e-12 else "illiquid"


def crisis_dividend(cash: float, financial: float, production: float) -> float:
    """Eurace@Unibi, Firm_in_financial_crisis: the dividend is cut to the cash left after the commitments and the
    planned production expenditure."""
    return max(0.0, cash - financial - production)


def insolvent(equity: float) -> bool:
    """Eurace@Unibi, Firm_set_bankruptcy_insolvency (the condition in Financial_Management/model.xml): negative equity."""
    return equity < 0.0


def installment_of(loan) -> float:
    """The principal a loan returns at the year's end (credit.service_split's rule)."""
    return loan.principal if loan.years_left <= 1.0 else loan.principal / loan.years_left


def interest_due(loans: Iterable, borrower: str) -> float:
    """Eurace@Unibi, Firm_compute_financial_payments: interest on the loans standing."""
    return sum(loan.principal * loan.rate for loan in loans if loan.borrower == borrower)


def financial_commitments(loans: Iterable, borrower: str) -> float:
    """Eurace@Unibi, Firm_compute_financial_payments: interest plus installments on the loans standing."""
    return sum(loan.principal * loan.rate + installment_of(loan) for loan in loans if loan.borrower == borrower)


def write_off_ratio(debt: float, assets: float, illiquid: bool) -> float:
    """Eurace@Unibi, Firm_bankruptcy_rescale_loans: the share of every loan written off so that the debt falls to
    the rescaling factor times the assets; an illiquid firm whose assets would let the debt rise takes the factor
    times the debt instead. The whole write-off falls in the one idle year (its months of idle period are our one
    step)."""
    if debt <= ARREARS_EPSILON:
        return 0.0
    target = DEBT_RESCALING_FACTOR * assets
    if illiquid and target > debt:
        target = DEBT_RESCALING_FACTOR * debt
    return min(1.0, max(0.0, (debt - target) / debt))


def written_down(loan, ratio: float):
    """(the loan after a write-off of `ratio`, the loss to its lender): Eurace@Unibi, Firm_bankruptcy_rescale_loans."""
    keep = 1.0 - ratio
    lost = ratio * (loan.principal + loan.arrears)
    return replaced(loan, principal=keep * loan.principal, arrears=keep * loan.arrears,
                    arrears_interest=keep * loan.arrears_interest), lost
