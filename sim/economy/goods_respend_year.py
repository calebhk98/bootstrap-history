"""The year's second round of household buying: after every market has cleared, a cohort rationed in some market bids
what it could not spend on the goods still offered (goods_respend.py), the markets clear again against the stock left,
and a cohort still rationed goes on until nothing more is bought. Money no offered good takes stays with the cohort.
"""
import math
from typing import Dict, List, Tuple

from sim.constants import declare

from . import goods_market, market_quote, settlement
from .entry import wanted_in_round
from .goods_market import quantity_at
from .goods_market_fills import sold_by_seller_tile
from .goods_respend import (bids_adding_demand, last_round_negligible, need_of_good, offers_left, rationed_money,
                            respend_bids)
from .types import Bid

Market = Tuple[str, str]

RESPEND_APPORTIONED_WANTED_SHARE = declare(
    "RESPEND_APPORTIONED_WANTED_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the round's wanted counted for the bids that add demand",
    source=None, confidence="D",
    why="A respend round's clearing gives the demand of all its bids together; the part that is new demand is taken "
        "pro rata to the adding bids' demand at one price, not computed bid by bid at the asks each faced.",
    retire="Complaint 964 exact wanted quantity per bid")


class LeftMarket:
    """A cleared market as the second round finds it: its bids and first-round result, the offers with what sold taken
    off, its last price, what has been delivered in it, what its buyers wanted (`wanted_in_round`, summed over the
    rounds), the bids that add demand in each round (`bids_adding_demand`) and the clearings of every round. What is unsold is what the last round to
    clear it left on offer."""

    def __init__(self, bids, result, offers, last_price, delivered, wanted, idle_years=0, bought=None):
        self.delivered = delivered     # goods moved in all rounds so far
        self.wanted = wanted           # what buyers asked for in all rounds so far
        self.idle_years = idle_years   # years the market lacked bids or offers, before this year
        self.results = [result]
        self.bought = bought or {}     # buyer -> (units received, money paid) in the first round's settlement
        self.bids = bids
        self.all_bids = list(bids)     # the first round's bids and the later rounds' that add demand
        self.last_offered = result.offered_at_price     # on offer at the last round's price
        self.last_delivered = delivered                 # moved in the last round
        self.result = result
        self.offers = offers
        self.last_price = last_price

    @property
    def unsold(self) -> float:
        """What the last round to clear this market left on offer."""
        return max(0.0, self.last_offered - self.last_delivered)


def rationed_in(bids, taken, households, fallback_price, need_by_buyer) -> Dict[str, Dict[str, float]]:
    """buyer -> need id -> money left unspent by the households' bids in one cleared market, where `taken` is buyer ->
    (units received, money paid) as its settlement moved them (`Settlement.bought_by_buyer`)."""
    by_buyer: Dict[str, List[Bid]] = {}
    for bid in bids:
        if bid.buyer in households:
            by_buyer.setdefault(bid.buyer, []).append(bid)
    rationed: Dict[str, Dict[str, float]] = {}
    for buyer, own in by_buyer.items():
        need_id = need_by_buyer(buyer).get(own[0].good)
        if need_id is None:
            continue
        units, money = taken.get(buyer, (0.0, 0.0))
        price = money / units if units > 0.0 else fallback_price
        if price is None or price <= 0.0:
            continue
        amount = rationed_money(own, units, money, price)
        if amount > 0.0:
            rationed.setdefault(buyer, {})[need_id] = rationed.get(buyer, {}).get(need_id, 0.0) + amount
    return rationed


def respend(setup, record, view, ledger, markets: Dict[Market, LeftMarket], basket_of) -> None:
    """Clear the households' leftover bids against the stock left in `markets`, in rounds, and settle them."""
    households = record.cohorts
    baskets: Dict[str, object] = {}
    needs: Dict[str, Dict[str, str]] = {}
    areas: Dict[str, Dict[str, str]] = {}

    need_of_basket: Dict[int, Dict[str, str]] = {}      # households of one basket share its need of each good
    areas_of_tile: Dict[tuple, Dict[str, str]] = {}      # and, on one tile, the area each good is bought in

    def need_by_buyer(buyer):
        if buyer not in needs:
            baskets[buyer] = basket = basket_of(households[buyer])
            if id(basket) not in need_of_basket:
                need_of_basket[id(basket)] = need_of_good(basket)
            needs[buyer] = need_of_basket[id(basket)]
        return needs[buyer]

    def areas_of(buyer):
        """good -> the market area this buyer's tile buys it in, for the goods its basket names."""
        if buyer not in areas:
            goods = need_by_buyer(buyer)
            tile = households[buyer].tile
            key = (tile, id(baskets[buyer]))
            if key not in areas_of_tile:
                areas_of_tile[key] = {good: view.area_of(good, tile) for good in goods}
            areas[buyer] = areas_of_tile[key]
        return areas[buyer]

    rationed: Dict[str, Dict[str, float]] = {}
    for key, market in sorted(markets.items()):
        if not market.bids:
            continue
        for buyer, by_need in rationed_in(market.bids, market.bought, households, market.result.price,
                                          need_by_buyer).items():
            for need_id, amount in by_need.items():
                rationed.setdefault(buyer, {})[need_id] = rationed.get(buyer, {}).get(need_id, 0.0) + amount
    paid_so_far = 0.0
    priced_cache: dict = {}
    for _round in range(len(markets) + 1):
        new_bids: Dict[Market, List[Bid]] = {}
        lowest_asks: Dict[Market, object] = {}
        asks_of_areas: Dict[int, Dict[str, float]] = {}      # the cheapest asks still offered, shared by buyers of one area map
        for buyer in sorted(rationed):
            cohort = households[buyer]
            basket_areas = areas_of(buyer)
            basket = baskets[buyer]
            asks = asks_of_areas.get(id(basket_areas))
            if asks is None:
                asks = asks_of_areas[id(basket_areas)] = {}
                for good, area in basket_areas.items():
                    key = (good, area)
                    if key not in lowest_asks:
                        ask = markets.get(key)
                        lowest_asks[key] = None if ask is None else market_quote.lowest_unfilled_ask(ask.offers)
                    if (price := lowest_asks[key]) is not None:
                        asks[good] = price
            by_need = rationed[buyer]
            cash = record.book.balance(buyer, setup.currency_id)
            total = sum(by_need.values())
            if total > cash > 0.0:
                by_need = {need_id: amount * cash / total for need_id, amount in by_need.items()}
            elif cash <= 0.0:
                continue
            for bid in respend_bids(buyer, cohort.tile, basket, by_need, asks, basket_areas.__getitem__, priced_cache):
                new_bids.setdefault((bid.good, bid.area), []).append(bid)
        rationed = {}
        paid_this_round = 0.0
        for key in sorted(new_bids):
            market = markets[key]
            bids = new_bids[key]
            result = goods_market.clear(bids, market.offers, key[0], key[1], setup.currency_id, market.last_price)
            adding = bids_adding_demand(market.all_bids, bids)
            market.wanted += _wanted_adding(adding, bids, market.offers, result)
            market.results.append(result)
            market.all_bids.extend(adding)
            moved, bought = _settle(record, ledger, result)
            market.delivered += moved
            market.last_offered = result.offered_at_price
            market.last_delivered = moved
            market.offers = offers_left(market.offers, sold_by_seller_tile(result.fills))
            paid_this_round += math.fsum(money for _units, money in bought.values())
            fallback = market_quote.lowest_unfilled_ask(market.offers)
            for buyer, by_need in rationed_in(bids, bought, households, fallback, need_by_buyer).items():
                for need_id, amount in by_need.items():
                    rationed.setdefault(buyer, {})[need_id] = rationed.get(buyer, {}).get(need_id, 0.0) + amount
        paid_so_far += paid_this_round
        if last_round_negligible(paid_this_round, paid_so_far) or not rationed:
            break


def _wanted_adding(adding, bids, offers, result) -> float:
    """What a respend round's buyers asked for, less what buyers already counted in the market asked again: the round's
    wanted quantity in the share the adding bids hold of the bids' demand at the price `wanted_in_round` reads demand at.
    Temporary heuristic: pro rata at one price, not computed bid by bid at the asks each faced (retire: Complaint 964)."""
    wanted = wanted_in_round(bids, offers, result)
    if len(adding) == len(bids):
        return wanted
    price = market_quote.lowest_unfilled_ask(offers)
    if price is None:
        price = market_quote.best_unfilled_bid(bids)
    if price is None:
        return 0.0
    total = math.fsum(quantity_at(bid, price) for bid in bids)
    if total <= 0.0:
        return 0.0
    return RESPEND_APPORTIONED_WANTED_SHARE * wanted * math.fsum(quantity_at(bid, price) for bid in adding) / total


def _settle(record, ledger, result) -> Tuple[float, Dict[str, Tuple[float, float]]]:
    """Settle a round's result and return the goods it delivered and what each buyer received and paid."""
    delivered, bought = 0.0, {}
    if result.quantity > 0.0:
        done = settlement.settle_goods(record.book, result, ledger.import_accounts, ledger.export_accounts)
        bought = done.bought_by_buyer()
        delivered = done.delivered
        ledger.note_settlement(done, "sales")
    ledger.note_clearing(result, delivered)
    return delivered, bought
