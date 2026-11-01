"""The mint as a market participant, holding a real stock of the metal (or good) its money is made of.

The stock is the metal embodied in the money in circulation: it is seeded with the opening money's
metal, grows only by what the mint buys (striking), and falls by what it sells (melting). It sells
only what it holds and strikes only what it buys. A struck coin pays the seller the mint price (parity
less the issuer's charge, `mint_price.py`) and the charge goes to the issuer as seigniorage; weighed metal and commodity
money are exchanged at parity both ways with no issuer. Fiat has no metal and no mint orders.
"""
import math
from typing import Dict

from . import currency, mint_labour, mint_price, mint_staffing
from .market_memory import market_key
from .metal_stock import COIN_WEAR_PER_YEAR, METAL_GOODS_LOSS_PER_YEAR
from .types import EDGE_EXTERNAL, EDGE_MINT, EDGE_PRODUCTION, EDGE_WEAR, Bid, GoodsMove, Offer, Transfer

MINT_PRIORITY = -1         # served before every other buyer: it pays up to the mint price, which bullion holders prefer to the ask


def stock_by_tile(book, metal) -> Dict[str, float]:
    """The metal the mint holds, by tile."""
    return {tile: quantity for tile, quantity in book.holdings(EDGE_MINT)["goods"].get(metal, {}).items()
            if quantity > 0.0}


def seed_opening_metal(setup, record) -> None:
    """Metal embodied in the opening money, placed by where people live."""
    spec = record.currency
    if spec.backing_good is None:
        return
    metal_total = record.book.money_supply(spec.currency_id) * spec.backing_per_unit
    people = sum(setup.opening_population_by_tile.values())
    if metal_total <= 0.0 or people <= 0.0:
        return
    record.book.move_many([GoodsMove(EDGE_PRODUCTION, EDGE_MINT, spec.backing_good, tile,
                                     metal_total * count / people, "metal of the opening money")
                           for tile, count in sorted(setup.opening_population_by_tile.items()) if count > 0.0])


def _book_foreign_coin_metal(record) -> None:
    """Coin that left through edge:external took its metal with it; coin that came in brought its metal.
    Only as much as the mint's stock is out of line with the metal in the money is booked."""
    spec = record.currency
    held = stock_by_tile(record.book, spec.backing_good)
    total = math.fsum(held.values())
    embodied = record.book.money_supply(spec.currency_id) * spec.backing_per_unit
    coin_in = record.book.edge_net(EDGE_EXTERNAL, spec.currency_id)
    if total > embodied and coin_in < 0.0 and total > 0.0:
        share = min(total - embodied, -coin_in * spec.backing_per_unit) / total
        record.book.move_many([GoodsMove(EDGE_MINT, EDGE_EXTERNAL, spec.backing_good, tile, quantity * share,
                                         "metal of coin sent abroad")
                               for tile, quantity in sorted(held.items())])
    elif total < embodied and coin_in > 0.0 and total > 0.0:
        share = min(embodied - total, coin_in * spec.backing_per_unit) / total
        record.book.move_many([GoodsMove(EDGE_EXTERNAL, EDGE_MINT, spec.backing_good, tile, quantity * share,
                                         "metal of coin from abroad")
                               for tile, quantity in sorted(held.items())])


def _lose_worn_metal(record) -> None:
    """Metal beyond what the money in circulation holds, once coin sent abroad is accounted for, is what
    wear and loss took out of it."""
    spec = record.currency
    _book_foreign_coin_metal(record)
    held = stock_by_tile(record.book, spec.backing_good)
    total = math.fsum(held.values())
    embodied = record.book.money_supply(spec.currency_id) * spec.backing_per_unit
    if total <= embodied or total <= 0.0:
        return
    share = (total - embodied) / total
    record.book.move_many([GoodsMove(EDGE_MINT, EDGE_WEAR, spec.backing_good, tile, quantity * share,
                                     "metal of worn money")
                           for tile, quantity in sorted(held.items())])


def yearly_monetisation(setup, record) -> float:
    """Most money the mint turns metal or a commodity into in a year: what holders want to add to their cash
    balances, plus what the money loses (wear of coin, loss of weighed metal, spoilage of a commodity) over the
    year, on the stock after striking. A mint
    that struck without limit would bid for metal no one wants as money, and the producers of the metal would be
    sized to that bid; the price level, not a capacity, then decides how far a surplus of metal becomes money
    (Complaints/reports/economy-research-commodity-money.md)."""
    spec = record.currency
    supply = record.book.money_supply(spec.currency_id)
    wanted = (math.fsum(cohort.cash_target for cohort in getattr(record, "cohorts", {}).values())
              + math.fsum(producer.cash_target for producer in getattr(record, "producers", {}).values())
              + math.fsum(merchant.capital_base for merchant in getattr(record, "merchants", {}).values()))
    loss = loss_share(setup, spec)
    return (max(0.0, wanted - supply) + loss * supply) / (1.0 - loss)       # the money struck wears too, before the year ends


def loss_share(setup, spec) -> float:
    """Share of the money in circulation that the backing good loses in a year, by the regime's own loss."""
    if spec.regime == "struck_coin":
        return COIN_WEAR_PER_YEAR
    if spec.regime == "weighed_metal":
        return METAL_GOODS_LOSS_PER_YEAR
    backing = getattr(setup, "specs", {}).get(spec.backing_good)
    return backing.spoilage_per_year if spec.regime == "commodity" and backing is not None else 0.0


def capacity_fine_kilograms(setup, record) -> float:
    """Fine metal the mint hires hands to strike in a year (`mint_staffing.staffed_money`)."""
    spec = record.currency
    if spec.backing_per_unit <= 0.0:
        return 0.0
    loss = loss_share(setup, spec)
    worn_money = loss * record.book.money_supply(spec.currency_id) / (1.0 - loss)
    return mint_staffing.staffed_money(yearly_monetisation(setup, record), worn_money) * spec.backing_per_unit


def staff(setup, record, view, labour_bids) -> None:
    """Before the labour market clears: the mint bids for the hours of its yearly capacity."""
    if record.currency.backing_per_unit > 0.0:
        budget = record.state_budget
        balance = record.book.balance(setup.state_agent, setup.currency_id)
        agent = mint_labour.mint_agent(setup)
        before = record.book.balance(agent, setup.currency_id)
        mint_labour.staff(setup, record, view, labour_bids, capacity_fine_kilograms(setup, record),
                          committed_cash=budget.wage_budget)
        funded = record.book.balance(agent, setup.currency_id) - before
        budget.goods_budget -= mint_staffing.goods_budget_cut(balance, budget.wage_budget, budget.goods_budget, funded)


def mint_orders(setup, record, area_map, order_book, hours_hired=None) -> Dict[str, float]:
    """Post the mint's bids and offers; returns the metal it holds by tile, for `settle_mint`.
    `hours_hired` is what the mint's staff were hired for this year, by trade; it limits the metal struck
    where the coin standard names a minting recipe."""
    spec = record.currency
    metal = spec.backing_good
    if not metal or spec.backing_per_unit <= 0.0 or metal not in area_map.goods():
        return {}
    _lose_worn_metal(record)
    held = stock_by_tile(record.book, metal)
    for tile, quantity in sorted(held.items()):
        if not mint_price.melting_pays(record.memory.prices.get(market_key(metal, area_map.area_of(metal, tile))),
                                       currency.mint_parity(spec)):
            continue
        offer = Offer(EDGE_MINT, metal, area_map.area_of(metal, tile), tile, quantity, currency.mint_parity(spec))
        order_book.setdefault((metal, offer.area), ([], []))[1].append(offer)
    strike_price = currency.mint_price(spec)
    coin_metal = min(yearly_monetisation(setup, record) * spec.backing_per_unit,
                     mint_labour.strike_limit_fine_kilograms(setup, spec, hours_hired or {}))
    for area in area_map.areas(metal):
        capacity = coin_metal * len(area.tiles) / max(1, len(setup.tiles))
        bid = Bid(EDGE_MINT, metal, area.area_id, area.anchor_tile, 0.0, capacity, strike_price, 0.0,
                  math.inf, MINT_PRIORITY, maximum_price=strike_price)
        order_book.setdefault((metal, area.area_id), ([], []))[0].append(bid)
    return held


def settle_mint(record, held_before: Dict[str, float], ledger=None) -> None:
    """After the goods markets: the mint tops the metal's sellers up to the mint price (`mint_price.py`, when the
    year's `ledger` is given); the coin value of the metal the mint took in, less the coin it paid out net for it, is owed to the issuer (seigniorage); then coin that crossed the border is matched with metal."""
    spec = record.currency
    if not spec.backing_good or spec.backing_per_unit <= 0.0:
        return
    if ledger is not None and currency.has_mint(spec):
        mint_price.pay_top_ups(record.book, ledger, spec.currency_id, spec.backing_good, currency.mint_price(spec))
    if currency.has_mint(spec) and spec.issuer is not None:
        taken_in = (math.fsum(stock_by_tile(record.book, spec.backing_good).values())
                    - math.fsum(held_before.values()))
        paid_out = record.book.edge_net(EDGE_MINT, spec.currency_id)
        owed = taken_in * currency.mint_parity(spec) - paid_out
        if owed > 0.0:
            record.book.transfer(Transfer(EDGE_MINT, spec.issuer, spec.currency_id, owed, "seigniorage"))
    _book_foreign_coin_metal(record)
