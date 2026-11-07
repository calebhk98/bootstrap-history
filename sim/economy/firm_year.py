"""A producer's year-end finances applied to the record, after Eurace@Unibi (Financial_Management/
Firm_Financial_Management_Functions.c): the income statement, the dividend, the financing check, and the two
bankruptcy routes. The numbers are firm_finance.py's; this module reads the record and writes the outcome.

`settled(producer, closed, ...)` is the pure decision: the producer after the year (histories, idle years), the
dividend it pays, and the state it is in. `settle_year` reads the record for it, and `write_off` applies a
bankruptcy to the producer's loans. A producer that closed to exit is left to producer_exit.py.
"""
from typing import List, NamedTuple, Optional, Tuple

from . import credit_claims, equity, firm_finance as finance, unit_cost
from .credit import Default
from .producers import live_input_prices, live_wages
from .replaced import replaced
from .types import Transfer

BANKRUPT_STATES = ("illiquid", "insolvent")


class FirmYear(NamedTuple):
    producer: object
    dividend: float
    state: str                  # "ok", "crisis", "illiquid" or "insolvent"
    write_off_ratio: float


def settled(producer, survivor, revenue: float, running_costs: float, interest: float, depreciation: float,
            commitments: float, arrears: float, cash: float, equity_value: float, capital_and_cash: float, debt: float,
            cash_kept: Optional[float] = None) -> FirmYear:
    """Eurace@Unibi's order: income statement, dividend, liquidity needs, the check for illiquidity, the
    cut to the dividend in a crisis, then insolvency. `survivor` is the producer after the close (its cash target is
    the production liquidity needs); `commitments` are the interest and installments next due, `arrears` what it could
    not pay this year. `capital_and_cash` is what the write-off is scaled to: plant and cash without the stock held
    (Eurace@Unibi, Firm_bankruptcy_rescale_loans: TOTAL_ASSETS = TOTAL_VALUE_CAPITAL_STOCK + PAYMENT_ACCOUNT), while
    `equity_value`, which the insolvency test reads, counts the stock. A producer in order pays at least the cash
    above `cash_kept` (None: no such rule)."""
    earnings = finance.net_earnings(revenue, running_costs, interest, depreciation)
    earnings_history = finance.appended(producer.net_earnings_history, earnings)
    revenue_history = finance.appended(producer.revenue_history, revenue)
    dividend, _full = finance.dividend_total(earnings_history, revenue_history, cash)
    needs = finance.liquidity_needs(cash, survivor.cash_target, commitments, dividend)
    state = finance.financial_state(cash, arrears, needs.total)
    if arrears > finance.ARREARS_EPSILON and state != "ok":
        state = "illiquid"
    elif state == "crisis":
        dividend = finance.crisis_dividend(cash, commitments, survivor.cash_target)
    elif cash_kept is not None:
        dividend = finance.payout(dividend, finance.excess_cash(cash, cash_kept))
    if state != "illiquid" and finance.insolvent(equity_value):
        state = "insolvent"
    kept = replaced(survivor, net_earnings_history=earnings_history, revenue_history=revenue_history)
    if state in BANKRUPT_STATES:
        ratio = finance.write_off_ratio(debt, capital_and_cash, state == "illiquid")
        return FirmYear(replaced(kept, idle_years=finance.BANKRUPTCY_IDLE_YEARS), 0.0, state, ratio)
    return FirmYear(kept, max(0.0, min(dividend, cash)), state, 0.0)


def settle_year(setup, record, view, producer, closed, recipe, revenue: float, running_costs: float,
                loans: List, inputs=None, wages=None) -> Tuple[object, Tuple[Transfer, ...], FirmYear]:
    """The producer's close with its finances settled: (the `YearClose` to keep, the dividend as transfers, the
    outcome). `loans` are the producer's own. The caller applies a write-off with `write_off`. `inputs` and `wages` are
    `live_input_prices` and `live_wages` when the caller has them already."""
    money = setup.currency_id
    survivor = closed.producer
    cash = max(0.0, record.book.balance(producer.agent_id, money))
    debt = sum(loan.principal + loan.arrears for loan in loans)
    stock = equity.inventory_value(record, producer, view)
    assets = equity.firm_assets(survivor, recipe, cash, stock, view)
    capital_and_cash = equity.firm_assets(survivor, recipe, cash, 0.0, view)
    inputs = live_input_prices(producer, recipe, view) if inputs is None else inputs
    wages = live_wages(producer, recipe, view) if wages is None else wages
    wear = 0.0
    if recipe.plant_life_years > 0.0 and producer.capacity_runs > 0.0:
        per_run = unit_cost.plant_value_per_run(recipe, inputs, wages)
        wear = producer.capacity_runs / recipe.plant_life_years * per_run
    replacement = closed.replacement_runs * unit_cost.plant_value_per_run(recipe, inputs, wages)
    kept = finance.cash_to_keep(survivor.cash_target, finance.financial_commitments(loans, producer.agent_id), replacement, running_costs)
    year = settled(producer, survivor, revenue, running_costs, finance.interest_due(loans, producer.agent_id),
                   wear, finance.financial_commitments(loans, producer.agent_id), sum(loan.arrears for loan in loans),
                   cash, assets - debt, capital_and_cash, debt, kept)
    transfers = (Transfer(producer.agent_id, producer.owner, money, year.dividend, "dividend"),) if year.dividend > 0.0 else ()
    if year.state in BANKRUPT_STATES:        # a bankrupt producer asks for no loan to grow
        return replaced(closed, producer=year.producer, transfers=(), loan_request=None, expansion_runs=0.0), (), year
    return replaced(closed, producer=year.producer, transfers=transfers), transfers, year


def write_off(record, borrower: str, ratio: float) -> float:
    """Eurace@Unibi, Firm_bankruptcy_rescale_loans: every loan of the borrower loses `ratio` of principal and arrears;
    each lender's loss is booked and the borrower's default remembered, as for any default (credit_claims).
    Returns the total lost."""
    if ratio <= 0.0:
        return 0.0
    kept: List = []
    defaults: List[Default] = []
    for loan in record.credit.loans:
        if loan.borrower != borrower:
            kept.append(loan)       # the list keeps its order
            continue
        written, lost = finance.written_down(loan, ratio)
        defaults.append(Default(loan.loan_id, loan.lender, loan.borrower, loan.currency, lost))
        if written.principal > finance.ARREARS_EPSILON or written.arrears > finance.ARREARS_EPSILON:
            kept.append(written)
    record.credit.replace_loans(kept)
    for lender, lost in credit_claims.losses_by_lender(defaults).items():
        record.credit.add_loss(lender, lost)
    record.credit.remember(defaults)
    return sum(default.loss for default in defaults)
