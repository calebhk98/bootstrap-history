"""The answer of goods_respend_kernel.respend_rounds written back: each market's results, bids that add demand, offers left
and totals; the settled pairs posted on the book per good and noted in the year ledger summed per agent.

A respend round's result carries no fills and no pairing: only households bid in these rounds, and nothing reads a household's
fills or a pairing that has no mint among its buyers.
"""
from typing import Dict, List

import numpy

from .goods_respend import RESPEND_PRIORITY
from .types import Bid, ClearingResult, Offer


def summed(keys: numpy.ndarray, values: numpy.ndarray):
    """The distinct `keys` ascending and the sum of `values` of each, added in the order given."""
    distinct, inverse = numpy.unique(keys, return_inverse=True)
    return distinct, numpy.bincount(inverse, weights=values, minlength=len(distinct))


def write_markets(setup, ledger, markets, packed, out) -> None:
    """Results, bids that add demand, offers and totals of every market that cleared in a round."""
    (_overflow, bid_count, clear_count, _pair_count, _bid_round, bid_market, bid_buyer, bid_flexible, bid_reference,
     bid_budget, bid_maximum, bid_adding, clear_market, _clear_round, clear_quantity, clear_price, clear_has_price,
     clear_demand, clear_offered, clear_delivered, _pm, _pb, _po, _pg, _pmo, _pi, _pe, market_wanted, market_delivered,
     market_offered, market_last_delivered, market_cleared) = out
    keys = packed.market_keys
    substitution = [packed.baskets[basket].substitution for basket in packed.arguments["buyer_basket"]]
    for row in range(bid_count):
        if bid_adding[row]:
            good, area = keys[bid_market[row]]
            buyer = bid_buyer[row]
            markets[(good, area)].added_bids.append(Bid(
                packed.buyers[buyer], good, area, packed.buyer_tile[buyer], 0.0, float(bid_flexible[row]),
                float(bid_reference[row]), substitution[buyer], float(bid_budget[row]), RESPEND_PRIORITY,
                maximum_price=float(bid_maximum[row])))
    for row in range(clear_count):
        good, area = keys[clear_market[row]]
        result = ClearingResult(good, area, setup.currency_id, float(clear_price[row]) if clear_has_price[row] else None,
                                float(clear_quantity[row]), float(clear_demand[row]), float(clear_offered[row]), ())
        markets[(good, area)].results.append(result)
        ledger.note_clearing(result, float(clear_delivered[row]))
    for index in numpy.nonzero(market_cleared)[0].tolist():
        market = markets[keys[index]]
        market.delivered += float(market_delivered[index])
        market.wanted += float(market_wanted[index])
        market.last_offered = float(market_offered[index])
        market.last_delivered = float(market_last_delivered[index])
        _leave_offers(market, packed, index)


def _leave_offers(market, packed, index: int) -> None:
    """Set the market's offers to what the rounds left: by the units of each offer left on the tables, else rebuilt as objects."""
    if market.rows is None:
        market.offers = _offers_left(market.offers, packed, index)
        return
    pointers = packed.arguments["offer_ptr"]
    first, last = pointers[index], pointers[index + 1]
    left = {int(packed.offer_origin[first + position]): float(packed.arguments["offer_quantity"][first + position])
            for position in range(last - first)}
    market.leave_units([left.get(place, 0.0) for place in range(len(market.rows.left_rows))])


def _offers_left(offers: List[Offer], packed, index: int) -> List[Offer]:
    """The market's offers, in their original order, with the quantity the rounds left; those with none are dropped."""
    pointers = packed.arguments["offer_ptr"]
    first, last = pointers[index], pointers[index + 1]
    left: Dict[int, float] = {int(packed.offer_origin[first + position]): float(packed.arguments["offer_quantity"][first + position])
                              for position in range(last - first)}
    kept = []
    for place, offer in enumerate(offers):
        quantity = left.get(place, 0.0)
        if quantity > 0.0:
            kept.append(offer if quantity == offer.quantity else Offer(offer.seller, offer.good, offer.area, offer.tile,
                                                                       quantity, offer.reservation_price))
    return kept


def write_settlement(setup, record, ledger, packed, out) -> None:
    """Post the pairs the rounds settled on the book (one posting per good) and note them in the ledger summed per agent."""
    pair_count = out[3]
    if not pair_count:
        return
    pair_market, pair_buyer, pair_offer, pair_goods, pair_money, pair_import, pair_export = out[20:27]
    market = pair_market[:pair_count]
    buyer_row = pair_buyer[:pair_count]
    offer = pair_offer[:pair_count]
    goods_moved = pair_goods[:pair_count]
    money = pair_money[:pair_count]
    item = packed.arguments["market_good"][market]
    buyer_agent = packed.arguments["buyer_agent"][buyer_row]
    seller_agent = packed.arguments["offer_agent"][offer]
    agents, good_names = packed.agents, packed.goods
    _note(ledger, packed, item, buyer_agent, seller_agent, goods_moved, money, pair_import[:pair_count],
          pair_export[:pair_count], len(good_names))
    for good in numpy.unique(item).tolist():
        mine = item == good
        buyers, sellers, units, paid_money = buyer_agent[mine], seller_agent[mine], goods_moved[mine], money[mine]
        people = numpy.unique(numpy.concatenate((buyers, sellers)))
        paid = numpy.bincount(numpy.searchsorted(people, buyers), weights=paid_money, minlength=len(people))
        received = numpy.bincount(numpy.searchsorted(people, sellers), weights=paid_money, minlength=len(people))
        moves: Dict[tuple, List[float]] = {}
        seller_keys, given = summed(packed.arguments["offer_key"][offer[mine]], units)
        for key, amount in zip(seller_keys.tolist(), given.tolist()):
            moves.setdefault((agents[packed.keys[key][0]], packed.keys[key][2]), [0.0, 0.0])[0] += amount
        rows, taken = summed(buyer_row[mine], units)
        for row, amount in zip(rows.tolist(), taken.tolist()):
            moves.setdefault((packed.buyers[row], packed.buyer_tile[row]), [0.0, 0.0])[1] += amount
        name = good_names[good]
        record.book.post_settled(setup.currency_id, "sale of %s" % name, name, [agents[each] for each in people.tolist()],
                                 paid.tolist(), received.tolist(), list(moves), [each[0] for each in moves.values()],
                                 [each[1] for each in moves.values()])


def _note(ledger, packed, item, buyer_agent, seller_agent, goods_moved, money, importer, exporter, good_count) -> None:
    """`YearLedger.note_settlement` of every pair, summed: money paid and received, goods received and sold by good, and the
    foreign-money figures. Buyers are households, so no plant purchase is noted."""
    agents, goods = packed.agents, packed.goods
    people, paid = summed(buyer_agent, money)
    seller_people, income = summed(seller_agent, money)
    out = {agents[agent]: amount for agent, amount in zip(people.tolist(), paid.tolist()) if amount > 0.0}
    income_by = {agents[agent]: amount for agent, amount in zip(seller_people.tolist(), income.tolist()) if amount > 0.0}
    got_keys, got = summed(buyer_agent * good_count + item, goods_moved)
    sold_keys, sold = summed(seller_agent * good_count + item, goods_moved)
    received_goods = [((agents[key // good_count], goods[key % good_count]), amount)
                      for key, amount in zip(got_keys.tolist(), got.tolist())]
    sold_goods = [((agents[key // good_count], goods[key % good_count]), amount)
                  for key, amount in zip(sold_keys.tolist(), sold.tolist()) if amount > 0.0]
    foreign = []
    for who, side in ((importer, "imports"), (exporter, "exports")):
        have = who >= 0
        if have.any():
            keys, amounts = summed(who[have] * good_count + item[have], money[have])
            foreign.extend((side, (agents[key // good_count], goods[key % good_count]), amount)
                           for key, amount in zip(keys.tolist(), amounts.tolist()) if amount > 0.0)
    ledger.note_summed_sales(out, income_by, received_goods, sold_goods, foreign)
