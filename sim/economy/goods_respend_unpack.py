"""The answer of goods_respend_kernel.respend_rounds written back: each market's results, bids that add demand, offers left
and totals; the settled pairs posted on the book per good and noted in the year ledger summed per agent.

A respend round's result carries no fills and no pairing: only households bid in these rounds, and nothing reads a household's
fills or a pairing that has no mint among its buyers.
"""
from typing import Dict, List

import numpy

from .goods_added_bids import AddedBids
from .types import Offer


def summed(keys: numpy.ndarray, values: numpy.ndarray):
    """The distinct `keys` ascending and the sum of `values` of each, added in the order given."""
    distinct, inverse = numpy.unique(keys, return_inverse=True)
    return distinct, numpy.bincount(inverse, weights=values, minlength=len(distinct))


def write_markets(setup, ledger, markets, packed, out) -> None:
    """Rounds, bids that add demand, offers and totals of every market that cleared in a round. A round is a row of its market's
    `later` (quantity, price, demand, offered) and of the ledger's rounds; a bid that adds demand is a row of the market's `AddedBids`."""
    (_overflow, bid_count, clear_count, _pair_count, _bid_round, bid_market, bid_buyer, bid_flexible, bid_reference,
     bid_budget, bid_maximum, bid_adding, clear_market, _clear_round, clear_quantity, clear_price, clear_has_price,
     clear_demand, clear_offered, clear_delivered, _pm, _pb, _po, _pg, _pmo, _pi, _pe, market_wanted, market_delivered,
     market_offered, market_last_delivered, market_cleared) = out
    keys = packed.market_keys
    _add_bids(markets, packed, keys, numpy.nonzero(bid_adding[:bid_count])[0], bid_market, bid_buyer, bid_flexible, bid_reference,
              bid_budget, bid_maximum)
    if clear_count:
        prices = numpy.where(clear_has_price[:clear_count], clear_price[:clear_count], numpy.nan)
        for market, quantity, price, demand, offered in zip(clear_market[:clear_count].tolist(), clear_quantity[:clear_count].tolist(),
                                                           prices.tolist(), clear_demand[:clear_count].tolist(),
                                                           clear_offered[:clear_count].tolist()):
            markets[keys[market]].later.append((quantity, None if price != price else price, demand, offered))
        note_rounds(ledger, keys, clear_market[:clear_count], clear_quantity[:clear_count], prices, clear_delivered[:clear_count])
    cleared = numpy.nonzero(market_cleared)[0]
    _add_rounds(markets, keys, cleared, market_delivered[cleared], market_wanted[cleared], market_offered[cleared], market_last_delivered[cleared])
    for index in cleared.tolist():
        _leave_offers(markets[keys[index]], packed, index)


def _add_rounds(markets, keys, cleared: numpy.ndarray, delivered, wanted, offered, last_delivered) -> None:
    """The rounds' totals added to the cleared markets' figures: one scatter into the year's table (`YearMarkets.add_rounds`) when
    the markets share it, market by market when each holds a table of its own (a market made alone)."""
    lefts = [markets[keys[index]] for index in cleared.tolist()]
    if not lefts:
        return
    shared = lefts[0].year_markets
    if all(each.year_markets is shared for each in lefts):
        shared.add_rounds(numpy.array([each.row for each in lefts], dtype=numpy.int64), delivered, wanted, offered, last_delivered)
        return
    for each, units, asked, on_offer, moved in zip(lefts, delivered.tolist(), wanted.tolist(), offered.tolist(), last_delivered.tolist()):
        each.delivered += units
        each.wanted += asked
        each.last_offered = on_offer
        each.last_delivered = moved


def _add_bids(markets, packed, keys, adding, bid_market, bid_buyer, bid_flexible, bid_reference, bid_budget, bid_maximum) -> None:
    """The bids that add demand, handed to their markets as column slices (rows of one market stay in the kernel's order)."""
    if not len(adding):
        return
    order = adding[numpy.argsort(bid_market[adding], kind="stable")]
    market_of_row = bid_market[order]
    cuts = numpy.nonzero(numpy.diff(market_of_row))[0] + 1
    elasticity = numpy.array([packed.baskets[basket].substitution for basket in packed.arguments["buyer_basket"]])
    for first, last in zip([0, *cuts.tolist()], [*cuts.tolist(), len(order)]):
        rows = order[first:last]
        good, area = keys[market_of_row[first]]
        buyers = bid_buyer[rows]
        markets[(good, area)].add_bids(AddedBids(
            good, area, [packed.buyers[each] for each in buyers.tolist()], [packed.buyer_tile[each] for each in buyers.tolist()],
            bid_flexible[rows].tolist(), bid_reference[rows].tolist(), elasticity[buyers].tolist(), bid_budget[rows].tolist(),
            bid_maximum[rows].tolist()))


def note_rounds(ledger, keys, clear_market, quantity, price, moved) -> None:
    """`YearLedger.note_clearing` of each round, the rounds added in one call: the market number of each (numbered when new), the
    quantity and price cleared and the goods moved. A household's fills are not kept in the rounds."""
    tables = ledger.tables
    numbers = tables.markets.goods_numbers
    market_numbers = {}
    for index in numpy.unique(clear_market).tolist():
        good, area = keys[index]
        number = numbers.get(good + "|" + area)
        market_numbers[index] = tables.market_number(good, area) if number is None else number
    ledger.note_round_rows(numpy.array([market_numbers[index] for index in clear_market.tolist()], dtype=numpy.int64),
                           numpy.asarray(quantity, dtype=float), numpy.asarray(price, dtype=float), numpy.asarray(moved, dtype=float))


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
