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

from . import currency
from .types import EDGE_MINT, EDGE_PRODUCTION, EDGE_WEAR, Bid, GoodsMove, Offer, Transfer

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


def _lose_worn_metal(record) -> None:
    """Metal beyond what the money in circulation holds is what wear and loss took out of it."""
    spec = record.currency
    held = stock_by_tile(record.book, spec.backing_good)
    total = math.fsum(held.values())
    embodied = record.book.money_supply(spec.currency_id) * spec.backing_per_unit
    if total <= embodied or total <= 0.0:
        return
    share = (total - embodied) / total
    record.book.move_many([GoodsMove(EDGE_MINT, EDGE_WEAR, spec.backing_good, tile, quantity * share,
                                     "metal of worn money")
                           for tile, quantity in sorted(held.items())])


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
    coin_metal = record.book.money_supply(spec.currency_id) * spec.backing_per_unit
    for area in area_map.areas(metal):
        capacity = MINT_YEARLY_STRIKE_SHARE * coin_metal * len(area.tiles) / max(1, len(setup.tiles))
        bid = Bid(EDGE_MINT, metal, area.area_id, area.anchor_tile, 0.0, capacity, strike_price, 0.0,
                  math.inf, MINT_PRIORITY, maximum_price=strike_price)
        order_book.setdefault((metal, area.area_id), ([], []))[0].append(bid)
    return held


def settle_mint(record, held_before: Dict[str, float]) -> None:
    """After the goods markets: the seller of metal to a struck-coin mint was paid only the mint price,
    so the charge on what the mint bought is coin owed to the issuer (seigniorage)."""
    spec = record.currency
    if not currency.has_mint(spec) or spec.mint_charge_share <= 0.0 or spec.issuer is None:
        return
    bought = math.fsum(max(0.0, quantity - held_before.get(tile, 0.0))
                       for tile, quantity in stock_by_tile(record.book, spec.backing_good).items())
    owed = bought * spec.mint_charge_share / spec.backing_per_unit
    if owed > 0.0:
        record.book.transfer(Transfer(EDGE_MINT, spec.issuer, spec.currency_id, owed, "seigniorage"))
