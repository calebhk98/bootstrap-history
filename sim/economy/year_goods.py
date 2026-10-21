"""The year's goods markets: every agent's orders, cleared one good at a time from raw materials up.

A good clears after the goods it is made from, so its producers make it from inputs bought this year
and sell it the same year (cycles in the recipes draw on stock). Producers make their output when the
first of their goods comes up, the state takes its tax in kind from what was grown, and then each
market area of the good clears and settles.
"""
import dataclasses
import math
from typing import Dict, List, Tuple

from . import (carriage_fleet_book, carriage_wear, goods_market, households, market_curves, market_quote, merchants, producers, seller_cash, seller_offers, settlement,
               state_budget, state_store, taxes, tool_wear, unsold_search)
from .market_memory import market_key
from .market_memory_asks import memory_reference_volume, note_bids, note_offers, price_after_resumed_trade, wanted_at
from .market_memory_asks import REPRESENTATIVE_TRADE_SHARE
from .market_memory_offers import price_after_thin_trade, price_toward_quote
from .notional import making_costs
from .protocols import AgentOrders
from .recipes import input_depth_order
from .taxes_bases import YearFacts
from .types import Bid, GoodsMove, Offer
from .entry import unmet_quantity
from .year_ledger import YearLedger

OrderBook = Dict[Tuple[str, str], Tuple[List[Bid], List[Offer]]]
# A good sold only at a token price would otherwise be remembered at a thousandth of last year's price
# every year until it underflows; nothing is remembered below this share of its opening price.
PRICE_MEMORY_FLOOR_SHARE = 1e-9


def add_orders(book: OrderBook, orders: AgentOrders) -> None:
    for bid in orders.bids:
        book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
    for offer in orders.offers:
        book.setdefault((offer.good, offer.area), ([], []))[1].append(offer)


def cohort_orders(setup, record, view, ledger: YearLedger, order_book: OrderBook) -> List:
    """Households' bids for the year; returns their savings offers for the credit market."""
    funds = []
    priced_by_tile = {}
    store_by_tile = {}
    money = setup.currency_id
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        priced = priced_by_tile.get(cohort.tile)
        if priced is None:
            priced = priced_by_tile[cohort.tile] = households.need_prices(setup.basket_for(cohort.tile), view, cohort.tile)
        income = ledger.wages_in.get(cohort.agent_id, 0.0) + record.property_income.get(cohort.agent_id, 0.0)
        cash = record.book.balance(cohort.agent_id, money)
        tool_bids = tool_wear.tool_bids(
            cohort.agent_id, cohort.tile, lambda good: view.area_of(good, cohort.tile), lambda good: view.price(good, view.area_of(good, cohort.tile)),
            lambda good: view.stock(cohort.agent_id, good, cohort.tile), setup.recipes, ledger.own_plot_hours.get(cohort.agent_id, {}),
            setup.specs, cash)
        add_orders(order_book, AgentOrders(bids=tuple(tool_bids)))
        orders = households.goods_orders(cohort, view, cash - sum(bid.budget for bid in tool_bids), income,
                                         setup.basket_for(cohort.tile), setup.specs, priced,
                                         smooth_rise=not record.settling, shared_store=store_by_tile)
        add_orders(order_book, _less_what_it_grew(orders, cohort, setup.basket_for(cohort.tile), ledger.grown_units.get(cohort.agent_id)))
        funds.extend(orders.funds_offers)
    return funds


def _less_what_it_grew(orders: AgentOrders, cohort, basket, grown_units) -> AgentOrders:
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
            bid = dataclasses.replace(bid, floor_quantity=bid.floor_quantity - cut,
                                      budget=bid.budget * max(0.0, share_kept))
        bids.append(bid)
    return dataclasses.replace(orders, bids=tuple(bids))


def merchant_orders(setup, record, view, area_map, carriage, order_book: OrderBook) -> None:
    money = setup.currency_id
    rate = view.interest_rate(money)
    shares = merchants.RouteShares()
    ordered = sorted(record.merchants.values(), key=lambda each: each.agent_id)
    carrier_bids, carrier_budget = (carriage_fleet_book.bids(setup, record, view, area_map,
                                                       {each.agent_id: record.book.balance(each.agent_id, money) for each in ordered})
                                    if carriage_wear.wears(setup) else ([], {}))
    add_orders(order_book, AgentOrders(bids=tuple(carrier_bids)))     # replacements for the carriers last year's shipments wore
    first = view.year % len(ordered) if ordered else 0          # who sizes first rotates, so no merchant always gets first pick
    for merchant in ordered[first:] + ordered[:first]:
        held = _held_stock(record.book, merchant.agent_id)
        orders = merchants.orders(merchant, view, carriage, area_map, record.book.balance(merchant.agent_id, money) - carrier_budget.get(merchant.agent_id, 0.0),
                                  held, setup.specs, rate, shares)
        add_orders(order_book, orders)


def state_orders(setup, record, view, area_map, order_book: OrderBook, keep) -> None:
    """The state offers what it holds beyond what its own lines will draw, at what holding it would net."""
    bids, store_offers, kept = state_store.orders(setup, record, view)
    state_budget.goods_bids(setup, record, view, area_map, order_book, kept)
    for bid in bids:
        order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
    add_orders(order_book, AgentOrders(offers=tuple(store_offers)))
    rate = view.interest_rate(setup.currency_id)
    from .inventory import holding_reservation
    offers = []
    for (good, tile), quantity in sorted(_held_stock(record.book, setup.state_agent).items()):
        surplus = quantity - keep.get(good, 0.0) - (kept.get(good, 0.0) if tile == setup.capital_tile else 0.0)
        if surplus <= 0.0 or good not in area_map.goods():
            continue
        area = area_map.area_of(good, tile)
        expected = view.price(good, area) or 0.0
        spoilage = setup.specs[good].spoilage_per_year if good in setup.specs else 0.0
        offers.append(Offer(setup.state_agent, good, area, tile, surplus,
                            holding_reservation(expected, rate, spoilage, 0.0)))
    add_orders(order_book, AgentOrders(offers=tuple(offers)))


def _held_stock(book, agent) -> Dict[Tuple[str, str], float]:
    held = {}
    for good, tiles in book.holdings(agent)["goods"].items():
        for tile, quantity in tiles.items():
            if quantity > 0.0:
                held[(good, tile)] = quantity
    return held


def clear_goods(setup, record, view, area_map, order_book: OrderBook, plans, ledger: YearLedger,
                watched_tiles=()) -> None:
    """Produce and clear every good in input-depth order. The book of each market area that holds the port, the
    capital or a watched tile is kept (market_curves.py)."""
    by_output: Dict[str, List[str]] = {}
    for producer_id, producer in sorted(record.producers.items()):
        for good in setup.recipes[producer.recipe_id].outputs:
            by_output.setdefault(good, []).append(producer_id)
    order = input_depth_order(setup.recipes)
    listed = set(order)
    order += sorted({good for good, _area in order_book} - listed)
    done, cleared, traded = set(), set(), set()
    costs = None                                  # what each good costs to make, worked out when first needed
    in_kind = [form for form in setup.tax_forms if form.paid_in]
    plant_goods = {producer_id: set(setup.recipes[producer.recipe_id].plant_goods)
                   for producer_id, producer in record.producers.items()}
    for good in order:
        for producer_id in by_output.get(good, ()):
            if producer_id not in done:
                done.add(producer_id)
                _produce_and_offer(setup, record, view, producer_id, plans.get(producer_id), in_kind,
                                   order_book, ledger)
        areas = sorted(area for item, area in order_book if item == good)
        kept = market_curves.kept_areas(area_map, setup.port_tile, (setup.capital_tile, *watched_tiles), good)
        for area in areas:
            bids, offers = order_book.pop((good, area))
            key = market_key(good, area)
            unit_costs: Dict = {}
            chosen = seller_offers.strategic_offers(setup, record, view, bids, offers, record.memory.prices.get(key),
                                                    unit_costs)
            offers, result = unsold_search.clear_with_search(setup, record, view, bids, offers, chosen, good, area,
                                                             setup.currency_id, record.memory.prices.get(key),
                                                             unit_costs)
            delivered = 0.0
            if result.quantity > 0.0:
                done_settlement = settlement.settle_goods(record.book, result)
                delivered = sum(move.quantity for move in done_settlement.postings if isinstance(move, GoodsMove))
                ledger.note_postings(done_settlement.postings, "sales")
                ledger.note_plant_purchases(done_settlement.postings, result.price, plant_goods)
                for shortfall in done_settlement.shortfalls:
                    ledger.unpaid[shortfall.agent] = ledger.unpaid.get(shortfall.agent, 0.0) + shortfall.unpaid_amount
            ledger.note_clearing(result)
            ledger.bids_by_market[(good, area)] = bids
            if area in kept:
                record.curves[key] = market_curves.summarize(bids, offers)
            unmet = unmet_quantity(bids, result.price, result.quantity)
            if unmet > 0.0:
                ledger.unmet_demand[(good, area)] = unmet
            old = record.memory.prices.get(key)
            quiet_years = note_bids(record.memory, key, bids, offers)
            dry_years = note_offers(record.memory, key, bids, offers)
            if result.quantity > 0.0:
                usual = record.memory.volume_weights.get(key, 0.0)
                reference = memory_reference_volume(usual, wanted_at(bids, old))
                signal = remembered_price(old, result.price, result.quantity, reference)
                signal = price_after_resumed_trade(old, signal, quiet_years + dry_years)
                if result.quantity < REPRESENTATIVE_TRADE_SHARE * usual:
                    if costs is None:
                        costs = making_costs(setup, record)
                    signal = price_after_thin_trade(signal, costs.get(good), result.quantity, usual)
            else:
                quote = result.quote
                if bids and not any(offer.quantity > 0.0 for offer in offers):
                    if costs is None:
                        costs = making_costs(setup, record)
                    quote = market_quote.no_trade_quote(bids, offers, costs.get(good))
                signal = price_toward_quote(old, quote.price) if quote is not None else None
                if signal is not None:
                    record.memory.quote_kinds[key] = quote.kind
            if signal is not None and signal > 0.0:
                floor = setup.opening_prices.get(good, signal) * PRICE_MEMORY_FLOOR_SHARE
                record.memory.prices[key] = max(signal, floor)
                record.memory.note_usual_price(key)
            record.volumes[key] = delivered
            record.unsold[key] = max(0.0, result.offered_at_price - result.quantity)
            record.unmet[key] = unmet
            record.memory.note_volume(key, delivered)
            record.memory.note_cleared(key, result.price, delivered)
            if delivered > 0.0:
                record.memory.quote_kinds.pop(key, None)
            cleared.add(key)
            if delivered > 0.0:
                traded.add(key)
    for key in sorted(set(record.memory.volume_weights) - cleared):
        record.memory.note_volume(key, 0.0)
    record.memory.note_trading(traded)


def remembered_price(old, cleared, quantity, usual_volume):
    """The price a market remembers after trading `quantity` at `cleared`: moved from the old price in
    proportion to the trade against `usual_volume` (the caller passes the larger of the market's usual
    volume and what buyers wanted at the old price), so a sliver of trade cleared at a price nobody
    normally pays does not become the price everyone plans from."""
    if old is None or usual_volume <= 0.0:
        return cleared
    return old + min(1.0, quantity / usual_volume) * (cleared - old)


def _produce_and_offer(setup, record, view, producer_id, plan, in_kind, order_book, ledger) -> None:
    producer = record.producers[producer_id]
    recipe = setup.recipes[producer.recipe_id]
    book = record.book
    if plan is not None and plan.runs > 0.0:
        held = {good: book.stock(producer_id, good, producer.tile) for good in recipe.inputs}
        hours = ledger.hours_hired.get(producer_id, {})
        _runs, moves = producers.produce(producer, recipe, held, hours, plan.runs)
        book.move_many(moves)
        ledger.note_output(producer_id, moves)
        _tax_in_kind(setup, record, producer, recipe, in_kind, ledger)
    stock = {good: book.stock(producer_id, good, producer.tile) for good in recipe.outputs}
    money = setup.currency_id
    cash = book.balance(producer_id, money)
    shortfall = seller_cash.shortfall_to_raise(producer.cash_target, cash, ledger.running_costs(producer_id))
    keep = {good: recipe.inputs.get(good, 0.0) * producer.capacity_runs for good in recipe.outputs}
    offers = producers.offers(producer, recipe, view, stock, shortfall, view.interest_rate(money), setup.specs, keep)
    add_orders(order_book, AgentOrders(offers=tuple(offers)))


def _tax_in_kind(setup, record, producer, recipe, forms, ledger) -> None:
    if not forms or setup.country_of(producer.tile) != setup.civ_id:
        return
    output = {(producer.agent_id, good): ledger.output.get((producer.agent_id, good), 0.0) for good in recipe.outputs}
    held = {(producer.agent_id, good): record.book.stock(producer.agent_id, good, producer.tile)
            for good in recipe.outputs}
    facts = YearFacts(currency=setup.currency_id, output=output, producer_tile={producer.agent_id: producer.tile},
                      held_goods=held)
    _transfers, moves, _assessments = taxes.assess(forms, facts, setup.state_agent, {}, setup.state_capacity)
    record.book.move_many(moves)
