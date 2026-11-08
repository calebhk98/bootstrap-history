"""The year's goods markets: every agent's orders, cleared one good at a time from raw materials up.

A good clears after the goods it is made from, so its producers make it from inputs bought this year
and sell it the same year (cycles in the recipes draw on stock). Producers make their output when the
first of their goods comes up, the state takes its tax in kind from what was grown, and then each
market area of the good clears and settles.
"""
import dataclasses
import math
from typing import Dict, List, Optional, Tuple

from . import (currency, mint_price, land_bid_year, carriage_fleet_book, carriage_wear, households, market_curves, market_quote, merchants, merchants_book, producers, seller_cash, seller_offers, settlement,
               state_budget, state_store, taxes, tool_wear, unsold_search)
from . import goods_good_clear, goods_order_book, goods_respend_year, households_cohort, year_goods_offers, households_orders_pack
from .goods_table_context import ClearingContext
from .home_scope import on_home_tile
from .inventory import held_stock, holding_reservation
from .household_work_year import basket_key, cohort_basket
from .opening_bid_memory import BidMemory
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
from .setup import opening_price_today

OrderBook = Dict[Tuple[str, str], Tuple[List[Bid], List[Offer]]]
# A good sold only at a token price would otherwise be remembered at a thousandth of last year's price
# every year until it underflows; nothing is remembered below this share of its opening price.
PRICE_MEMORY_FLOOR_SHARE = 1e-9


def add_orders(book, orders: AgentOrders) -> None:
    if isinstance(book, goods_order_book.GoodsOrderBook):
        book.add_orders(orders)
        return
    for bid in orders.bids:
        book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
    for offer in orders.offers:
        book.setdefault((offer.good, offer.area), ([], []))[1].append(offer)


def cohort_orders(setup, record, view, ledger: YearLedger, order_book: OrderBook, own_options=None) -> List:
    """Households' bids for the year; returns their savings offers for the credit market. Every cohort whose basket the kernel covers
    is ordered in one call (`households_orders_pack`); the rest through `households.goods_orders`."""
    funds = []
    memory = BidMemory()     # the priced needs and store weights cohorts of one basket share
    money = setup.currency_id
    cohorts = sorted(record.cohorts.values(), key=lambda each: each.agent_id)
    smooth_rise = not record.settling
    tool_bids_of, entries, plain = {}, [], {}
    for cohort in cohorts:
        basket = memory.basket(setup, record, cohort)
        priced = memory.priced(setup, record, view, cohort, basket)
        income = ledger.wages_in.get(cohort.agent_id, 0.0) + record.capital_markets.property_income.get(cohort.agent_id, 0.0)
        cash = record.book.balance(cohort.agent_id, money)
        tool_bids = tool_wear.tool_bids(
            cohort.agent_id, cohort.tile, lambda good: view.area_of(good, cohort.tile), lambda good: view.offered_price(good, view.area_of(good, cohort.tile)),
            lambda good: view.stock(cohort.agent_id, good, cohort.tile), setup.recipes, ledger.own_plot_hours.get(cohort.agent_id, {}),
            setup.specs, cash)
        tool_bids_of[cohort.agent_id] = tool_bids
        spendable = cash - sum(bid.budget for bid in tool_bids)
        grown_units = ledger.grown_units.get(cohort.agent_id)
        if not priced or cohort.people <= 0.0:
            plain[cohort.agent_id] = AgentOrders()
        elif households_orders_pack.covered(priced):
            entries.append((cohort, basket, priced, spendable, income, grown_units))
        else:
            plain[cohort.agent_id] = less_what_it_grew(households.goods_orders(
                cohort, view, spendable, income, basket, setup.specs, priced, smooth_rise=smooth_rise, shared_store=memory.stores(record, cohort)),
                cohort, basket, grown_units)
    made = households_orders_pack.kernel_orders(
        view, setup.specs, entries, smooth_rise, lambda cohort: basket_key(record, cohort), lambda cohort: memory.stores(record, cohort))
    made.update(plain)
    for cohort in cohorts:
        orders = made[cohort.agent_id]
        tool_bids = tool_bids_of[cohort.agent_id]
        add_orders(order_book, AgentOrders(bids=tuple(tool_bids)))
        households_cohort.change_cohort(
            record.cohorts, cohort.agent_id, planned_spending=sum(bid.budget for bid in tool_bids) + sum(bid.budget for bid in orders.bids))
        if own_options:
            savings = sum(offer.amount for offer in orders.funds_offers)     # only what it would otherwise lend
            orders = land_bid_year.with_land_bids(orders, land_bid_year.land_bids(
                setup, record, view, cohort, own_options, ledger.spare_hours.get(cohort.agent_id, 0.0), savings))
        add_orders(order_book, orders)
        funds.extend(orders.funds_offers)
    return funds


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


def merchant_orders(setup, record, view, area_map, carriage, order_book: OrderBook) -> None:
    money = setup.currency_id
    rate = own_rate(view, money)
    ordered = sorted(record.merchants.values(), key=lambda each: each.agent_id)
    route = merchants_book.route_pass(view, carriage, area_map, setup.specs) if ordered else None
    shares = merchants_book.DenseShares(route.book) if ordered else None
    carrier_bids, carrier_budget = (carriage_fleet_book.bids(setup, record, view, area_map,
                                                       {each.agent_id: record.book.balance(each.agent_id, money) for each in ordered})
                                    if carriage_wear.wears(setup) else ([], {}))
    add_orders(order_book, AgentOrders(bids=tuple(carrier_bids)))     # replacements for the carriers last year's shipments wore
    first = view.year % len(ordered) if ordered else 0          # who sizes first rotates, so no merchant always gets first pick
    for merchant in ordered[first:] + ordered[:first]:
        held = held_stock(record.book, merchant.agent_id)
        orders = merchants.orders(merchant, view, carriage, area_map, record.book.balance(merchant.agent_id, money) - carrier_budget.get(merchant.agent_id, 0.0),
                                  held, setup.specs, rate, shares, route)
        add_orders(order_book, orders)


def state_orders(setup, record, view, area_map, order_book: OrderBook, keep) -> None:
    """The state offers what it holds beyond what its own lines will draw, at what holding it would net."""
    bids, store_offers, kept = state_store.orders(setup, record, view)
    state_budget.goods_bids(setup, record, view, area_map, order_book, kept)
    for bid in bids:
        order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
    add_orders(order_book, AgentOrders(offers=tuple(store_offers)))
    rate = own_rate(view, setup.currency_id)
    offers = []
    for (good, tile), quantity in sorted(held_stock(record.book, setup.state_agent).items()):
        surplus = quantity - keep.get(good, 0.0) - (kept.get(good, 0.0) if tile == setup.capital_tile else 0.0)
        if surplus <= 0.0 or good not in area_map.goods():
            continue
        area = area_map.area_of(good, tile)
        expected = view.offered_price(good, area)      # what a buyer can see to buy at, not a bid ceiling or a cost quote
        if expected is None:
            continue
        spoilage = setup.specs[good].spoilage_per_year if good in setup.specs else 0.0
        offers.append(Offer(setup.state_agent, good, area, tile, surplus,
                            holding_reservation(expected, rate, spoilage, 0.0)))
    add_orders(order_book, AgentOrders(offers=tuple(offers)))


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
    plant_goods = {producer_id: set(setup.recipes[producer.recipe_id].plant_goods)
                   for producer_id, producer in record.producers.items()}
    memory_names = orders.memory_tables.goods_markets.name_list
    for good in order:
        turn = [producer_id for producer_id in by_output.get(good, ()) if producer_id not in done]
        done.update(turn)
        _produce_and_offer(setup, record, view, turn, plans, in_kind, orders, ledger, offering)
        good_id = record.book.good_ids.find(good)
        cleared = goods_good_clear.clear_good(context, good, good_id) if good_id is not None else []
        kept = market_curves.kept_areas(area_map, setup.port_tile, (setup.capital_tile, *watched_tiles), good)
        traded = [each.result for each in cleared if each.result.quantity > 0.0]
        settled = iter(settlement.settle_goods_many(record.book, traded, ledger.import_accounts, ledger.export_accounts))
        for each in cleared:
            key = memory_names[each.market]
            delivered, bought = 0.0, {}
            if each.result.quantity > 0.0:
                done_settlement = next(settled)
                bought = done_settlement.bought_by_buyer()
                delivered = done_settlement.delivered
                ledger.note_settlement(done_settlement, "sales", plant_goods)
            ledger.note_clearing(each.result, delivered)
            idle_years = goods_good_clear.note_idle_years(record.memory, key, each)
            left_markets[(good, each.area)] = goods_respend_year.LeftMarket(
                each.bids, each.result, each.offers_left,
                record.memory.prices.get(key), delivered, wanted_in_round(each.bids, each.offers, each.result), idle_years, bought)
            if each.area in kept:
                record.goods.curves[key] = market_curves.summarize(each.bids, each.offers)
    goods_respend_year.respend(setup, record, view, ledger, left_markets,
                               lambda cohort: cohort_basket(setup, record, cohort))
    for market_id, market in left_markets.items():
        ledger.bids_by_market[market_id] = market.all_bids     # demand over the same rounds as the traded quantity
    _remember_markets(setup, record, left_markets, ledger)
    _record_year_markets(record, ledger, left_markets)


def _remember_markets(setup, record, left_markets, ledger: YearLedger) -> None:
    """Each market's memory, once, after every round: the quantity delivered over its clearings and the price weighted by
    quantity (`clearing_totals.market_totals`), so a market that traded only in the respend is remembered as traded.
    All signals are worked out from last year's memory before any of it moves."""
    quantity, cleared = ledger.market_totals()
    memory = record.memory
    costs = None                                  # what each good costs to make, worked out when first needed
    updates = []
    for (good, area), market in sorted(left_markets.items()):
        key = market_key(good, area)
        old, total = market.last_price, quantity[(good, area)]
        quote_kind = None
        received = _received_price(setup, record, good, market.results, ledger) if total > 0.0 else None
        if received is not None:
            usual = memory.volume_weights.get(key, 0.0)
            reference = memory_reference_volume(usual, wanted_at(market.all_bids, old))
            signal = price_after_trade(old, key in memory.quote_kinds, received,
                                       total, reference, market.idle_years)
            if total < REPRESENTATIVE_TRADE_SHARE * usual:
                if costs is None:
                    costs = making_costs(setup, record)
                signal = price_after_thin_trade(signal, costs.get(good), total, usual)
        else:
            quote = market.result.quote
            if market.bids and not market.offers:
                if costs is None:
                    costs = making_costs(setup, record)
                quote = market_quote.no_trade_quote(market.bids, market.offers, costs.get(good))
            signal = price_toward_quote(old, quote.price) if quote is not None else None
            if signal is not None:
                quote_kind = quote.kind
        updates.append((key, good, signal, quote_kind, cleared[(good, area)], market.delivered, received is not None))
    traded = set()
    for key, good, signal, quote_kind, price, delivered, from_trade in updates:
        if from_trade:
            memory.drop_quote_kind(key)               # the price now comes from a clearing, whatever settled of it
        if quote_kind is not None:
            memory.set_quote_kind(key, quote_kind)
        if signal is not None and signal > 0.0:
            memory.set_price(key, max(signal, price_floor(setup, memory, good, signal)))
            memory.note_usual_price(key)
        memory.note_cleared(key, price, delivered)
        if delivered > 0.0:
            memory.drop_quote_kind(key)
            traded.add(key)
    memory.note_trading(traded)


def price_floor(setup, memory, good, signal: float) -> float:
    """The least a remembered price may fall to: a sliver of the good's opening price in today's money (of the signal itself
    for a good with no opening price)."""
    opening = opening_price_today(setup, memory, good)
    return (signal if opening is None else opening) * PRICE_MEMORY_FLOOR_SHARE


def _record_year_markets(record, ledger: YearLedger, left_markets) -> None:
    """The year's volumes, unsold and unmet of every market, after all rounds; a market with no orders this year has
    none, and its usual volume moves toward zero."""
    record.goods.volumes.clear()
    record.goods.unsold.clear()
    record.goods.unmet.clear()
    for (good, area), market in sorted(left_markets.items()):
        key = market_key(good, area)
        unmet = unmet_quantity(market.wanted, market.delivered)
        record.goods.volumes[key] = market.delivered
        record.goods.unsold[key] = market.unsold
        record.goods.unmet[key] = unmet
        if unmet > 0.0:
            ledger.unmet_demand[(good, area)] = unmet
        record.memory.note_volume(key, market.delivered)
    for key in sorted(set(record.memory.volume_weights) - set(record.goods.volumes)):
        record.memory.note_volume(key, 0.0)


def _received_price(setup, record, good, results, ledger: YearLedger) -> Optional[float]:
    """The price a market's sellers got per unit over its clearings, weighted by quantity: the settled price, plus the
    mint's top-up where it bought coin metal; None when no clearing traded."""
    spec = record.currency
    traded = [result for result in results if result.quantity > 0.0]
    quantity = math.fsum(result.quantity for result in traded)
    if quantity <= 0.0:
        return None
    if not currency.has_mint(spec) or good != spec.backing_good:
        return math.fsum(result.quantity * result.price for result in traded) / quantity
    return math.fsum(result.quantity * mint_price.received_price(currency.mint_price(spec), result, ledger.settled_to_mint(result))
                     for result in traded) / quantity


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
    book = record.book
    made = []
    moves_made = []
    for producer_id in producer_ids:
        plan = plans.get(producer_id)
        if plan is not None and plan.runs > 0.0:
            producer = record.producers[producer_id]
            recipe = setup.recipes[producer.recipe_id]
            held = {good: book.stock(producer_id, good, producer.tile) for good in recipe.inputs}
            _runs, moves = producers.produce(producer, recipe, held, ledger.hours_hired.get(producer_id, {}), plan.runs)
            moves_made.extend(moves)
            ledger.note_output(producer_id, moves)
            made.append(producer_id)
    book.move_many(moves_made)
    _tax_in_kind(setup, record, made, in_kind, ledger)
    money = setup.currency_id
    rate = own_rate(view, money) if producer_ids else None
    pending = []           # (producer, its offers, or None for the quick ones below, those as (good, quantity, price, spoilage))
    expected, spoilage, quantity, rows, shortfalls, pair_ptr = [], [], [], [], [], [0]
    for producer_id in producer_ids:
        producer = record.producers[producer_id]
        recipe = setup.recipes[producer.recipe_id]
        stock = {good: book.stock(producer_id, good, producer.tile) for good in recipe.outputs}
        cash = book.balance(producer_id, money)
        shortfall = seller_cash.shortfall_to_raise(producer.cash_target, cash, ledger.running_costs(producer_id))
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
    taken = 0
    for producer, offers, held in pending:
        if held is not None:
            offers = []
            for good, quantity, _price, _loss in held:
                offers.append(Offer(producer.agent_id, good, view.area_of(good, producer.tile), producer.tile, quantity,
                                    reservations[taken]))
                taken += 1
        add_orders(order_book, AgentOrders(offers=tuple(offers)))


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
