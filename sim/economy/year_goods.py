"""The year's goods markets: every agent's orders, cleared one good at a time from raw materials up.

A good clears after the goods it is made from, so its producers make it from inputs bought this year
and sell it the same year (cycles in the recipes draw on stock). Producers make their output when the
first of their goods comes up, the state takes its tax in kind from what was grown, and then each
market area of the good clears and settles.
"""
import dataclasses
import math
from typing import Dict, List, Optional, Tuple

from . import currency, mint_price, market_curves, market_quote, producers, seller_cash, taxes
from . import year_bids
from .year_bids_by_market import BidsByMarket
from . import goods_good_clear, goods_memory_notes, goods_production, goods_settle, goods_order_book, goods_respend_year, year_goods_offers
from .goods_table_context import ClearingContext
from .year_goods_offer_rows import OfferRows
from .home_scope import on_home_tile
from .household_work_year import cohort_basket
from .goods_market_rows import bids_only_quote, wanted_at_rows
from .market_memory import market_key
from .market_memory_asks import memory_reference_volume, price_after_resumed_trade, wanted_at
from .market_memory_asks import REPRESENTATIVE_TRADE_SHARE
from .market_memory_offers import price_after_thin_trade, price_toward_quote
from .notional import making_costs
from .protocols import AgentOrders
from .recipes import input_depth_order
from .taxes_bases import YearFacts
from .types import Bid, Offer
from .entry import unmet_quantity, wanted_in_round
from .year_arrays_costs import OfferCosts, refreshed
from .year_ledger import YearLedger
from .rates import own_rate
from .goods_memory_notes import PRICE_MEMORY_FLOOR_SHARE
from .setup import opening_price_today

OrderBook = Dict[Tuple[str, str], Tuple[List[Bid], List[Offer]]]


def add_orders(order_book, orders: AgentOrders) -> None:
    """The agent's goods bids and offers added to the book of orders (a `GoodsOrderBook`, or a `{(good, area): (bids, offers)}` dict)."""
    if isinstance(order_book, goods_order_book.GoodsOrderBook):
        order_book.add_orders(orders)
        return
    for bid in orders.bids:
        order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
    for offer in orders.offers:
        order_book.setdefault((offer.good, offer.area), ([], []))[1].append(offer)


def with_floor_and_budget(bid: Bid, floor_quantity: float, budget: float) -> Bid:
    """`bid` with a new floor and budget: the bid `dataclasses.replace` makes, built directly, since the opening's
    income search makes millions of them."""
    return Bid(bid.buyer, bid.good, bid.area, bid.tile, floor_quantity, bid.flexible_quantity, bid.reference_price,
               bid.elasticity, budget, bid.priority, bid.maximum_price)


def less_what_it_grew(orders: AgentOrders, cohort, basket, grown_units) -> AgentOrders:
    """Floors already met from the household's own plot are not bought: each floor bid of a need is
    cut by the share of that need's floor the cohort grew."""
    if not grown_units:
        return orders
    need_of_good = {}
    floor_of_need = {}
    for need in basket.needs:
        floor_of_need[need.need_id] = need.subsistence_per_person * cohort.people
        for good, _effect in need.goods:
            need_of_good.setdefault(good, need.need_id)
    bids = []
    for bid in orders.bids:
        need_id = need_of_good.get(bid.good)
        floor_units = floor_of_need.get(need_id, 0.0)
        met = min(1.0, grown_units.get(need_id, 0.0) / floor_units) if floor_units > 0.0 else 0.0
        if met > 0.0 and bid.floor_quantity > 0.0:
            cut = bid.floor_quantity * met
            share_kept = 1.0 - cut / (bid.floor_quantity + bid.flexible_quantity)
            bid = with_floor_and_budget(bid, bid.floor_quantity - cut, bid.budget * max(0.0, share_kept))
        bids.append(bid)
    return dataclasses.replace(orders, bids=tuple(bids))


def clear_goods(setup, record, view, area_map, order_book, plans, ledger: YearLedger,
                watched_tiles=(), arrays=None) -> None:
    """Produce and clear every good in input-depth order. The book of each market area that holds the port, the
    capital or a watched tile is kept (market_curves.py). With the year's arrays, a good's markets that have bids and
    offers are re-priced, searched and cleared together from the order tables (goods_good_clear.py)."""
    orders = goods_order_book.as_book(order_book, record)
    costs = offering = None
    ledger.fill_watchers = frozenset(getattr(record, "merchants", ())) | {getattr(setup, "state_agent", None)}     # the readers of the buy fills
    if arrays is not None:
        arrays = refreshed(arrays, setup, record, view)
        costs = OfferCosts.build(arrays, own_rate(view, setup.currency_id))
        offering = (arrays, costs) if year_goods_offers.usable() else None
    context = ClearingContext(setup, record, view, orders, arrays, costs)
    by_output: Dict[str, List[str]] = {}
    for producer_id, producer in sorted(record.producers.items()):
        for good in setup.recipes[producer.recipe_id].outputs:
            by_output.setdefault(good, []).append(producer_id)
    order = input_depth_order(setup.recipes)
    listed = set(order)
    order += sorted(orders.goods_with_orders() - listed)
    done = set()
    left_markets = {}
    in_kind = [form for form in setup.tax_forms if form.paid_in]
    metal = record.currency.backing_good if currency.has_mint(record.currency) else None        # the good whose markets the mint reads
    plant_makers: Dict[str, list] = {}       # a good -> the producers whose plant is built from it
    for producer_id, producer in record.producers.items():
        for plant_good in setup.recipes[producer.recipe_id].plant_goods:
            plant_makers.setdefault(plant_good, []).append(producer_id)
    memory_names = orders.memory_tables.goods_markets.name_list
    for good in order:
        turn = [producer_id for producer_id in by_output.get(good, ()) if producer_id not in done]
        done.update(turn)
        _produce_and_offer(setup, record, view, turn, plans, in_kind, orders, ledger, offering)
        good_id = record.book.good_ids.find(good)
        cleared = goods_good_clear.clear_good(context, good, good_id) if good_id is not None else []
        kept = market_curves.kept_areas(area_map, setup.port_tile, (setup.capital_tile, *watched_tiles), good)
        answer = goods_settle.settle_good(record, ledger, cleared, good, plant_makers)
        goods_settle.note_clearings(ledger, cleared, answer, memory_names, metal)
        idle = goods_settle.idle_years(record.memory, cleared) if cleared else []
        last_prices = goods_settle.last_prices(record.memory, cleared)
        for each, entry, idle_years, last_price in zip(cleared, answer, idle, last_prices):
            key = memory_names[each.market]
            delivered, bought = entry[0], entry[1]
            left_markets[(good, each.area)] = goods_respend_year.LeftMarket(
                each.bids, each.result, each.offers_left, last_price, delivered,
                each.wanted if each.wanted is not None else wanted_in_round(each.bids, each.offers, each.result), idle_years, bought,
                each.rows)
            if each.area in kept:
                record.goods.curves[key] = market_curves.summarize(*each.objects())
    goods_respend_year.respend(setup, record, view, ledger, left_markets,
                               lambda cohort: cohort_basket(setup, record, cohort), orders)
    block = ledger.year_bids = year_bids.build(left_markets)     # demand over the same rounds as the traded quantity, as one table
    ledger.bids_by_market = BidsByMarket(block, left_markets)
    _remember_markets(setup, record, left_markets, ledger, orders)
    _record_year_markets(record, ledger, left_markets)


def _remember_markets(setup, record, left_markets, ledger: YearLedger, orders=None) -> None:
    """Each market's memory, once, after every round: the quantity delivered over its clearings and the price weighted by
    quantity (`clearing_totals.market_totals`), so a market that traded only in the respend is remembered as traded.
    All signals are worked out from last year's memory (read as columns) before any of it moves; the writes are one kernel
    call over the markets in sorted (good, area) order (`goods_memory_notes`)."""
    quantity, cleared = ledger.market_totals()
    memory = record.memory
    costs = None                                  # what each good costs to make, worked out when first needed
    ordered = sorted(left_markets.items())
    keys = [market_key(good, area) for (good, area), _market in ordered]
    rows = goods_memory_notes.rows_of(memory, keys)
    was_quote, usual_volumes = goods_memory_notes.last_year_columns(memory, rows)
    opening_of_good = {}
    signals, kind_numbers, from_trade, prices, delivered, openings = [], [], [], [], [], []
    for place, ((good, area), market) in enumerate(ordered):
        old, total = market.last_price, quantity[(good, area)]
        quote_kind = None
        received = _received_price(setup, record, good, market, ledger) if total > 0.0 else None
        if received is not None:
            usual = usual_volumes[place]
            reference = memory_reference_volume(usual, _wanted_at(market, old, orders))
            signal = price_after_trade(old, was_quote[place], received, total, reference, market.idle_years)
            if total < REPRESENTATIVE_TRADE_SHARE * usual:
                if costs is None:
                    costs = making_costs(setup, record)
                signal = price_after_thin_trade(signal, costs.get(good), total, usual)
        else:
            quote = market.result.quote
            if market.bids and not market.offers:
                if costs is None:
                    costs = making_costs(setup, record)
                quote = (bids_only_quote(orders.bid_lists(), market.rows.bid_rows, costs.get(good)) if market.rows is not None else
                         market_quote.no_trade_quote(market.bids, market.offers, costs.get(good)))
            signal = price_toward_quote(old, quote.price) if quote is not None else None
            if signal is not None:
                quote_kind = quote.kind
        if good not in opening_of_good:
            opening_of_good[good] = opening_price_today(setup, memory, good)
        signals.append(signal)
        kind_numbers.append(goods_memory_notes.kind_number(memory, quote_kind))
        from_trade.append(received is not None)
        prices.append(cleared[(good, area)])
        delivered.append(market.delivered)
        openings.append(opening_of_good[good])
    goods_memory_notes.write_markets(memory, rows, signals, kind_numbers, from_trade, prices, delivered, openings)


def _wanted_at(market, price, orders) -> float:
    """What the market's own buyers would take at the price over all rounds: the first round's bids from the tables' columns
    where the market is on them, plus the later rounds' bids that add demand."""
    if market.rows is None:
        return wanted_at(market.all_bids, price)
    return wanted_at_rows(orders.bid_lists(), market.rows.bid_rows, price, added=market.added)


def price_floor(setup, memory, good, signal: float) -> float:
    """The least a remembered price may fall to: a sliver of the good's opening price in today's money (of the signal itself
    for a good with no opening price)."""
    opening = opening_price_today(setup, memory, good)
    return (signal if opening is None else opening) * PRICE_MEMORY_FLOOR_SHARE


def _record_year_markets(record, ledger: YearLedger, left_markets) -> None:
    """The year's volumes, unsold and unmet of every market, after all rounds; a market with no orders this year has
    none, and its usual volume moves toward zero (`goods_memory_notes.write_volumes`)."""
    record.goods.volumes.clear()
    record.goods.unsold.clear()
    record.goods.unmet.clear()
    ordered = sorted(left_markets.items())
    for (good, area), market in ordered:
        key = market_key(good, area)
        unmet = unmet_quantity(market.wanted, market.delivered)
        record.goods.volumes[key] = market.delivered
        record.goods.unsold[key] = market.unsold
        record.goods.unmet[key] = unmet
        if unmet > 0.0:
            ledger.unmet_demand[(good, area)] = unmet
    memory = record.memory
    goods_memory_notes.write_volumes(memory, goods_memory_notes.rows_of(memory, [market_key(good, area) for (good, area), _market in ordered]),
                                     [market.delivered for _key, market in ordered])


def _received_price(setup, record, good, market, ledger: YearLedger) -> Optional[float]:
    """The price a market's sellers got per unit over its clearings, weighted by quantity: the settled price, plus the
    mint's top-up where it bought coin metal; None when no clearing traded. The first round's clearing is a result; the respend
    rounds' are (quantity, price) rows (`market.later`), which carry no fills and so no top-up."""
    spec = record.currency
    traded = [result for result in market.results if result.quantity > 0.0]
    later = [(quantity, price) for quantity, price, _demand, _offered in market.later if quantity > 0.0]
    quantity = math.fsum([result.quantity for result in traded] + [units for units, _price in later])
    if quantity <= 0.0:
        return None
    if not currency.has_mint(spec) or good != spec.backing_good:
        return math.fsum([result.quantity * result.price for result in traded] + [units * price for units, price in later]) / quantity
    return math.fsum([result.quantity * mint_price.received_price(currency.mint_price(spec), result, ledger.settled_to_mint(result))
                      for result in traded] + [units * price for units, price in later]) / quantity


def price_after_trade(old, old_was_quote, cleared, quantity, reference_volume, quiet_years):
    """The price a market remembers after a year in which it traded: `remembered_price` and the resumed-trade rule
    against the old price, unless the old price was a quote (a bid ceiling, an ask, a cost): no one paid it, so the
    trade replaces it whole rather than being weighed against it. A sliver cleared above a quote is the exception: thin
    supply meets the highest bid, so a sliver can only overstate the price and moves the quote in proportion to its share."""
    if old_was_quote and old is not None and cleared > old:
        return remembered_price(old, cleared, quantity, reference_volume)
    paid = None if old_was_quote else old
    return price_after_resumed_trade(paid, remembered_price(paid, cleared, quantity, reference_volume), quiet_years)


def remembered_price(old, cleared, quantity, usual_volume):
    """The price a market remembers after trading `quantity` at `cleared`: moved from the old price in
    proportion to the trade against `usual_volume` (the caller passes the larger of the market's usual
    volume and what buyers wanted at the old price), so a sliver of trade cleared at a price nobody
    normally pays does not become the price everyone plans from. An `old` that is None (nothing remembered, or only a
    quote no one paid) is replaced by the trade whole."""
    if old is None or usual_volume <= 0.0:
        return cleared
    return old + min(1.0, quantity / usual_volume) * (cleared - old)


def _produce_and_offer(setup, record, view, producer_ids, plans, in_kind, order_book, ledger, offering=None) -> None:
    """The producers whose turn it is make their output (their moves booked together), the state takes its tax in kind from
    what they made, and each offers what it holds. The producers do not touch one another's holdings, so booking in a batch
    is booking one at a time."""
    made = goods_production.produce(setup, record, producer_ids, plans, ledger)
    _tax_in_kind(setup, record, made, in_kind, ledger)
    money = setup.currency_id
    rate = own_rate(view, money) if producer_ids else None
    held_outputs, cash_held, running = goods_production.turn_figures(setup, record, ledger, producer_ids)
    pending = []           # (producer, its offers, or None for the quick ones below, those as (good, quantity, price, spoilage))
    expected, spoilage, quantity, rows, shortfalls, pair_ptr = [], [], [], [], [], [0]
    for place, producer_id in enumerate(producer_ids):
        producer = record.producers[producer_id]
        recipe = setup.recipes[producer.recipe_id]
        stock = held_outputs[place]
        shortfall = seller_cash.shortfall_to_raise(producer.cash_target, cash_held[place], running[place])
        keep = {good: recipe.inputs.get(good, 0.0) * producer.capacity_runs for good in recipe.outputs}
        held = _quick_outputs(setup, offering, producer, recipe, stock, keep) if offering is not None else None
        if held is None:
            pending.append((producer, producers.offers(producer, recipe, view, stock, shortfall, rate, setup.specs, keep), None))
            continue
        for _good, units, price, loss in held:
            expected.append(price)
            spoilage.append(loss)
            quantity.append(units)
        pair_ptr.append(len(expected))
        rows.append(offering[0].producers.row[producer.agent_id])
        shortfalls.append(shortfall)
        pending.append((producer, None, held))
    reservations = (year_goods_offers.reservations_for(offering[0], offering[1], rows, pair_ptr, expected, spoilage, quantity,
                                                       shortfalls, rate).tolist() if rows else [])
    offer_rows = OfferRows(order_book, view)
    taken = 0
    for producer, offers, held in pending:
        if held is not None:
            for good, quantity, _price, _loss in held:
                offer_rows.add(producer, good, quantity, reservations[taken])
                taken += 1
            continue
        offer_rows.write()               # keep the producers' offers in the order they were made
        add_orders(order_book, AgentOrders(offers=tuple(offers)))
    offer_rows.write()


def _quick_outputs(setup, offering, producer, recipe, stock, keep):
    """The (good, units to offer, price expected, spoilage) of a producer's outputs when `producers.offers` would offer
    them at the reservation holding them gives (year_goods_offers.py); None when it would not: an output with no price
    expected."""
    arrays, costs = offering
    row = arrays.producers.row.get(producer.agent_id)
    if row is None:
        return None
    recipe_row = arrays.producers.recipe_row[row]
    held = []
    for good in sorted(recipe.outputs):
        quantity = stock.get(good, 0.0) - keep.get(good, 0.0)
        if quantity <= 0.0:
            continue
        price = costs.expected[row, costs.slot_of[recipe_row, arrays.matrices.goods.row[good]]]
        if price != price:
            return None
        spec = setup.specs.get(good)
        held.append((good, quantity, price, spec.spoilage_per_year if spec is not None else 0.0))
    return held


def _tax_in_kind(setup, record, producer_ids, forms, ledger) -> None:
    """The state's share, in kind, of what the producers just made on the home tiles. A harvest form assesses only those
    that made the good it is paid in, so the others are left out of its facts."""
    if not forms:
        return
    taxed = {form.paid_in for form in forms} if all(form.basis == "harvest" for form in forms) else None
    output, held, tiles = {}, {}, {}
    for producer_id in producer_ids:
        producer = record.producers[producer_id]
        recipe = setup.recipes[producer.recipe_id]
        if (taxed is not None and taxed.isdisjoint(recipe.outputs)) or not on_home_tile(setup, producer.tile):
            continue
        tiles[producer_id] = producer.tile
        for good in recipe.outputs:
            output[(producer_id, good)] = ledger.output.get((producer_id, good), 0.0)
            held[(producer_id, good)] = record.book.stock(producer_id, good, producer.tile)
    if not output:
        return
    facts = YearFacts(currency=setup.currency_id, output=output, producer_tile=tiles, held_goods=held)
    _transfers, moves, _assessments = taxes.assess(forms, facts, setup.state_agent, {}, ledger.state_capacity, setup.hiding)
    record.book.move_many(moves)
