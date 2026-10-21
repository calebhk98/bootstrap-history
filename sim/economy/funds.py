"""A fund: a pool of shares and loans that households hold units in.

A fund is an agent with a purse and holdings of the same kinds as a household's (shares in `record.shares`, loans it
lends), so it buys and sells in the secondary market like a saver and lends the cash it holds. Its holdings are
marked at what a saver would pay for them (the worth at the market rate plus each issuer's premium, secondary_trade.py),
so a unit is worth the fund's cash and marked holdings over the units outstanding. A household subscribes the savings
it did not lend and buys units at that worth, and redeems them at that worth for the cash it needs, which the fund
pays from its purse; a fund short of cash sells holdings to the savers at the secondary price and pays what that
raises, the units left bearing what the sale lost.

The first unit costs one unit of money; a fund with nothing in it is worth nothing per unit. A fund earns the dividends
and interest its holdings pay, which stay in it (units are not paid an income, their worth rises), so a household
reads a fund's yield from what it has earned over what it is worth.
"""
from typing import Dict, List, Optional, Sequence

from . import credit_claims, secondary_trade, shares
from .capital_state import Fund
from .secondary_trade import Shortfall
from .types import AgentId, FundsOffer, Transfer

EPSILON = 1e-9
SUBSCRIPTION_PURPOSE = "fund units bought"
REDEMPTION_PURPOSE = "fund units redeemed"
FIRST_UNIT_PRICE = 1.0
POOLED_FUNDS = "pooled_funds"        # the institution a society must hold for its households to pool savings in a fund


def standing(record) -> List[Fund]:
    return [fund for _id, fund in sorted(record.capital.funds.items()) if fund.closed_year < 0]


def found(record, manager: AgentId, year: int) -> Fund:
    """A new fund run by `manager`, with no money in it and no units."""
    fund = Fund("fund:%d" % len(record.capital.funds), manager, year)
    record.capital.funds[fund.agent_id] = fund
    return fund


def units_outstanding(fund: Fund) -> float:
    return sum(fund.units.values())


def marked_holdings(setup, record, fund_id: AgentId, market_rate: float) -> float:
    """What the fund's shares and loans would fetch from a saver at the market rate and each issuer's premium."""
    rate_floor = shares.rate_floor_of(setup)
    debts = credit_claims.principal_by_borrower(record.loans)
    arrears = credit_claims.arrears_history(record.loans, record.remembered_defaults)
    total = 0.0
    for producer_id, held in sorted(record.shares.items()):
        part = held.get(fund_id, 0.0)
        if part > EPSILON and producer_id in record.producers:
            premium = secondary_trade.issuer_premium(record, producer_id, debts, arrears,
                                                     secondary_trade.share_value(record, producer_id, market_rate, rate_floor))
            total += part * secondary_trade.share_value(record, producer_id, market_rate + premium, rate_floor)
    for loan in record.loans:
        if loan.lender == fund_id:
            premium = secondary_trade.issuer_premium(record, loan.borrower, debts, arrears, loan.collateral_value)
            total += secondary_trade.loan_value(loan, market_rate + premium)
    return total


def net_assets(setup, record, fund: Fund, market_rate: float) -> float:
    """The fund's cash and its holdings at their marked worth."""
    return record.book.balance(fund.agent_id, setup.currency_id) + marked_holdings(setup, record, fund.agent_id, market_rate)


def unit_price(setup, record, fund: Fund, market_rate: float) -> Optional[float]:
    """What one unit is worth: the net assets over the units outstanding; the first unit's price while none exist."""
    units = units_outstanding(fund)
    if units <= EPSILON:
        return FIRST_UNIT_PRICE
    worth = net_assets(setup, record, fund, market_rate)
    return worth / units if worth > EPSILON else None


def subscribe(setup, record, fund: Fund, holder: AgentId, amount: float, market_rate: float) -> float:
    """The holder pays `amount` and takes units at the unit price; the units bought (none when the units are worth
    nothing, or the holder holds less than `amount`)."""
    money = setup.currency_id
    amount = min(amount, record.book.balance(holder, money))
    price = unit_price(setup, record, fund, market_rate)
    if price is None or price <= EPSILON or amount <= EPSILON or fund.closed_year >= 0:
        return 0.0
    units = amount / price
    record.book.transfer(Transfer(holder, fund.agent_id, money, amount, SUBSCRIPTION_PURPOSE))
    fund.units[holder] = fund.units.get(holder, 0.0) + units
    return units


def redeem(setup, record, fund: Fund, holder: AgentId, wanted: float, market_rate: float) -> float:
    """The holder gives up units worth `wanted` (at most what it holds) and is paid from the fund's purse, as much as
    the purse holds; the money paid. The units given up are those the money paid buys."""
    money = setup.currency_id
    price = unit_price(setup, record, fund, market_rate)
    held = fund.units.get(holder, 0.0)
    if price is None or price <= EPSILON or held <= EPSILON:
        return 0.0
    paid = min(wanted, held * price, max(0.0, record.book.balance(fund.agent_id, money)))
    if paid <= EPSILON:
        return 0.0
    record.book.transfer(Transfer(fund.agent_id, holder, money, paid, REDEMPTION_PURPOSE))
    fund.units[holder] = held - paid / price
    if fund.units[holder] <= EPSILON:
        del fund.units[holder]
    return paid


def redeem_for_cash(setup, record, fund: Fund, holder: AgentId, need: float, offers: Sequence[FundsOffer], market_rate: float,
                    institutions: Sequence[str]) -> List[FundsOffer]:
    """The holder redeems units for `need` of cash. A fund short of it sells holdings to the savers first, as a seller
    that needs the cash; the offers less what the savers spent."""
    money = setup.currency_id
    price = unit_price(setup, record, fund, market_rate)
    if price is None:
        return list(offers)
    wanted = min(need, fund.units.get(holder, 0.0) * price)
    short = wanted - record.book.balance(fund.agent_id, money)
    if short > EPSILON:
        offers, _trades = secondary_trade.run(setup, record, offers, {fund.agent_id: Shortfall(short, market_rate)},
                                              market_rate, institutions, sellers=[fund.agent_id])
    redeem(setup, record, fund, holder, wanted, market_rate)
    return list(offers)


def expected_income(record, fund: Fund) -> float:
    """What the fund's holdings are expected to pay in a year: its part of each producer's last dividend and the interest on its loans."""
    dividends = sum(held.get(fund.agent_id, 0.0) * record.last_dividends.get(producer_id, 0.0)
                    for producer_id, held in record.shares.items() if producer_id in record.producers)
    return dividends + sum(loan.principal * loan.rate for loan in record.loans if loan.lender == fund.agent_id)


def yield_of(setup, record, fund: Fund, market_rate: float) -> Optional[float]:
    """The expected income over what the fund is worth; none when it is worth nothing."""
    worth = net_assets(setup, record, fund, market_rate)
    return expected_income(record, fund) / worth if worth > EPSILON else None


def cash_to_invest(setup, record, fund: Fund) -> float:
    return max(0.0, record.book.balance(fund.agent_id, setup.currency_id))


def offer_of(setup, record, fund: Fund, market_rate: float) -> Optional[FundsOffer]:
    """The cash the fund holds, offered to the credit market and to the savers' claims at the market rate."""
    cash = cash_to_invest(setup, record, fund)
    return FundsOffer(fund.agent_id, setup.currency_id, cash, market_rate) if cash > EPSILON else None


def owned_by(record, holder: AgentId) -> Dict[str, float]:
    """The units a holder has in each fund."""
    return {fund_id: fund.units[holder] for fund_id, fund in sorted(record.capital.funds.items()) if holder in fund.units}
