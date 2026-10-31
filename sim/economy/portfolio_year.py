"""The year's portfolio trading in shares: each household orders shares up to its portfolio fraction or sells down to
it, the orders are matched at the index price, and the index price moves with the excess demand.

The households' side follows Eurace@Unibi (see household_portfolio.py for the files and functions). The savings a
household orders shares with are the savings it offers the year's lending (the cash left after its planned spending,
`households_orders.goods_orders`), which is Eurace's portfolio budget less the consumption budget; the shares it
holds are valued at the index price, the same value `equity.holdings` gives the spending rule as share wealth, so
a sale lowers the wealth the rule spends from by what it brings in. Buyers that no seller meets keep a buy order
(`capital.share_buy_orders`) that the producers' new issues fill (shares.raise_equity): their money reaches the
issuing producer's cash. Selling needs the institution `SHARE_TRADING`; without it nobody sells, and the index price
does not move.
"""
from dataclasses import replace
from typing import Dict, List, Mapping, Sequence

from . import equity, household_portfolio, secondary_trade
from .types import AgentId, FundsOffer, Transfer

PORTFOLIO_SALE_PURPOSE = "portfolio sale"
EPSILON = 1e-9


def orders_of(fraction: float, savings: Mapping[AgentId, float], wealth: Mapping[AgentId, float]) -> Dict[AgentId, float]:
    """Each trader's net order: the value to buy (positive) or sell (negative)."""
    return {trader: household_portfolio.net_investment(fraction, savings.get(trader, 0.0), wealth.get(trader, 0.0))
            for trader in sorted(set(savings) | set(wealth))}


def apply_matches(record, currency: str, matched: Mapping[AgentId, float], wealth: Mapping[AgentId, float]) -> None:
    """Book the matched orders (values at the index price): each seller sells the same part of every producer it
    holds, the buyers take what is sold in proportion to what they were matched for and pay the sellers in proportion."""
    sellers = {trader: -value for trader, value in matched.items() if value < -EPSILON and wealth.get(trader, 0.0) > EPSILON}
    buyers = {trader: value for trader, value in matched.items() if value > EPSILON}
    bought = sum(buyers.values())
    if not sellers or bought <= EPSILON:
        return
    payments: List[Transfer] = []
    for seller, sold in sorted(sellers.items()):
        for buyer, spent in sorted(buyers.items()):
            payments.append(Transfer(buyer, seller, currency, sold * spent / bought, PORTFOLIO_SALE_PURPOSE))
    record.book.transfer_many(payments)
    for producer_id in sorted(record.shares):
        held = record.shares[producer_id]
        pool = 0.0
        for seller, sold in sorted(sellers.items()):
            if seller in held:
                moved = held[seller] * sold / wealth[seller]
                held[seller] -= moved
                pool += moved
        for buyer, spent in sorted(buyers.items()):
            held[buyer] = held.get(buyer, 0.0) + pool * spent / bought
        for holder in [each for each, part in held.items() if part <= EPSILON]:
            del held[holder]


def run(setup, record, view, funds: Sequence[FundsOffer], institutions: Sequence[str]) -> List[FundsOffer]:
    """The year's portfolio trading. Returns the offers with what each buyer spent taken off; leaves each saver's
    unfilled buy order in `record.capital.share_buy_orders` for the producers' new issues."""
    money = setup.currency_id
    state = record.capital
    state.share_buy_orders = {}
    savings = {offer.lender: offer.amount for offer in funds if offer.currency == money and offer.lender in record.cohorts
               and offer.amount > EPSILON}
    worths = equity.producer_worths(setup, record, view)
    factor = state.share_price_factor
    prices = {producer_id: factor * worth for producer_id, worth in worths.items() if worth > 0.0}
    expected = household_portfolio.expected_yield(record.last_dividends, prices)
    fraction = None if expected is None else household_portfolio.fraction_to_invest(view.interest_rate(money), expected)
    if fraction is None:
        return list(funds)
    trading = secondary_trade.SHARE_TRADING in institutions
    wealth = {holder: household_portfolio.share_wealth(
        {producer_id: held[holder] for producer_id, held in record.shares.items() if holder in held}, worths, factor)
        for holder in sorted({holder for held in record.shares.values() for holder in held if holder in record.cohorts})}
    orders = orders_of(fraction, savings, wealth)
    if not trading:
        orders = {trader: max(0.0, value) for trader, value in orders.items()}
    matched, ratio = household_portfolio.match_orders(orders)
    if trading:
        apply_matches(record, money, matched, wealth)
        state.share_price_factor = household_portfolio.next_price_factor(factor, ratio)
    spent = {trader: value for trader, value in matched.items() if value > 0.0}
    state.share_buy_orders = {trader: max(0.0, value - spent.get(trader, 0.0)) for trader, value in orders.items()
                              if value > 0.0 and trader in savings}
    return [replace(offer, amount=offer.amount - spent[offer.lender]) if offer.lender in spent and offer.currency == money else offer
            for offer in funds]
