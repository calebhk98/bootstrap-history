"""The mint as a market participant, holding a real stock of the metal (or good) its money is made of.

The stock is the metal embodied in the money in circulation: it is seeded with the opening money's
metal, grows only by what the mint buys (striking), and falls by what it sells (melting). It sells
only what it holds and strikes only what it buys. A struck coin pays the seller the mint price (parity
less the issuer's charge) and the charge goes to the issuer as seigniorage; weighed metal and commodity
money are exchanged at parity both ways with no issuer. Fiat has no metal and no mint orders.
"""
import math
from typing import Dict

from sim.constants import declare

from . import currency, metal_stock
from .types import EDGE_EXTERNAL, EDGE_MINT, EDGE_PRODUCTION, EDGE_WEAR, Bid, GoodsMove, Offer, Transfer

MINT_PRIORITY = 9          # the mint is served after every other buyer at the same price

MINT_YEARLY_STRIKE_SHARE = declare(
    "MINT_YEARLY_STRIKE_SHARE", 1.0, kind="temporary_heuristic", unit="share of the metal in circulation per year",
    why="most metal the mint will strike in a year, as a share of the metal already in circulating money: "
        "stands in for mint capacity (furnaces, dies, labour), which is not modelled. A mint ledger of "
        "output by year (mint accounts, die counts) would fix it.")


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
    """Most money the mint turns metal or a commodity into in a year.

    A struck coin's mint strikes up to its capacity (MINT_YEARLY_STRIKE_SHARE of the money in
    circulation), and the price level then decides whether striking pays. Money with no issuer (weighed
    metal, a commodity such as cacao) is only metal or beans held as cash: holders take into money what
    they want to add to their cash balances, plus what wears out or spoils, and no more. Otherwise growing
    the money commodity would always sell at parity, and it would take land from food without limit
    (Complaints/reports/economy-research-commodity-money.md)."""
    spec = record.currency
    supply = record.book.money_supply(spec.currency_id)
    if currency.has_mint(spec):
        return MINT_YEARLY_STRIKE_SHARE * supply
    wanted = (math.fsum(cohort.cash_target for cohort in getattr(record, "cohorts", {}).values())
              + math.fsum(producer.cash_target for producer in getattr(record, "producers", {}).values())
              + math.fsum(merchant.capital_base for merchant in getattr(record, "merchants", {}).values()))
    return max(0.0, wanted - supply) + _loss_share(setup, spec) * supply


def _loss_share(setup, spec) -> float:
    """Share of money lost in a year: weighed metal as metal, a commodity as the good spoils."""
    if spec.regime == "weighed_metal":
        return metal_stock.METAL_GOODS_LOSS_PER_YEAR
    backing = getattr(setup, "specs", {}).get(spec.backing_good)
    return backing.spoilage_per_year if backing is not None else 0.0


def mint_orders(setup, record, area_map, order_book) -> Dict[str, float]:
    """Post the mint's bids and offers; returns the metal it holds by tile, for `settle_mint`."""
    spec = record.currency
    metal = spec.backing_good
    if not metal or spec.backing_per_unit <= 0.0 or metal not in area_map.goods():
        return {}
    _lose_worn_metal(record)
    held = stock_by_tile(record.book, metal)
    for tile, quantity in sorted(held.items()):
        offer = Offer(EDGE_MINT, metal, area_map.area_of(metal, tile), tile, quantity, currency.mint_parity(spec))
        order_book.setdefault((metal, offer.area), ([], []))[1].append(offer)
    strike_price = currency.mint_price(spec)
    coin_metal = yearly_monetisation(setup, record) * spec.backing_per_unit
    for area in area_map.areas(metal):
        capacity = coin_metal * len(area.tiles) / max(1, len(setup.tiles))
        bid = Bid(EDGE_MINT, metal, area.area_id, area.anchor_tile, 0.0, capacity, strike_price, 0.0,
                  math.inf, MINT_PRIORITY, maximum_price=strike_price)
        order_book.setdefault((metal, area.area_id), ([], []))[0].append(bid)
    return held


def settle_mint(record, held_before: Dict[str, float]) -> None:
    """After the goods markets: the coin value of the metal the mint took in, less the coin it paid out net
    for it, is owed to the issuer (seigniorage); then coin that crossed the border is matched with metal."""
    spec = record.currency
    if not spec.backing_good or spec.backing_per_unit <= 0.0:
        return
    if currency.has_mint(spec) and spec.issuer is not None:
        taken_in = (math.fsum(stock_by_tile(record.book, spec.backing_good).values())
                    - math.fsum(held_before.values()))
        paid_out = record.book.edge_net(EDGE_MINT, spec.currency_id)
        owed = taken_in * currency.mint_parity(spec) - paid_out
        if owed > 0.0:
            record.book.transfer(Transfer(EDGE_MINT, spec.issuer, spec.currency_id, owed, "seigniorage"))
    _book_foreign_coin_metal(record)
