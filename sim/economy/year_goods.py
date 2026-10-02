"""The year's goods markets: every agent's orders, cleared one good at a time from raw materials up.

A good clears after the goods it is made from, so its producers make it from inputs bought this year
and sell it the same year (cycles in the recipes draw on stock). Producers make their output when the
first of their goods comes up, the state takes its tax in kind from what was grown, and then each
market area of the good clears and settles.
"""
from typing import Dict, List, Tuple

from . import goods_market, households, merchants, producers, settlement, taxes
from .market_memory import market_key
from .protocols import AgentOrders
from .recipes import input_depth_order
from .taxes_bases import YearFacts
from .types import Bid, Offer
from .year_ledger import YearLedger

OrderBook = Dict[Tuple[str, str], Tuple[List[Bid], List[Offer]]]


def add_orders(book: OrderBook, orders: AgentOrders) -> None:
    for bid in orders.bids:
        book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
    for offer in orders.offers:
        book.setdefault((offer.good, offer.area), ([], []))[1].append(offer)


def cohort_orders(setup, record, view, ledger: YearLedger, order_book: OrderBook) -> List:
    """Households' bids for the year; returns their savings offers for the credit market."""
    funds = []
    priced_by_tile = {}
    money = setup.currency_id
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        priced = priced_by_tile.get(cohort.tile)
        if priced is None:
            priced = priced_by_tile[cohort.tile] = households.need_prices(setup.basket, view, cohort.tile)
        income = ledger.wages_in.get(cohort.agent_id, 0.0) + record.property_income.get(cohort.agent_id, 0.0)
        orders = households.goods_orders(cohort, view, record.book.balance(cohort.agent_id, money), income,
                                         setup.basket, setup.specs, priced)
        add_orders(order_book, orders)
        funds.extend(orders.funds_offers)
    return funds


def merchant_orders(setup, record, view, area_map, carriage, order_book: OrderBook) -> None:
    money = setup.currency_id
    rate = view.interest_rate(money)
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        held = _held_stock(record.book, merchant.agent_id)
        orders = merchants.orders(merchant, view, carriage, area_map, record.book.balance(merchant.agent_id, money),
                                  held, setup.specs, rate)
        add_orders(order_book, orders)


def state_orders(setup, record, view, area_map, order_book: OrderBook, keep) -> None:
    """The state offers what it holds beyond what its own lines will draw, at what holding it would net."""
    rate = view.interest_rate(setup.currency_id)
    from .inventory import holding_reservation
    offers = []
    for (good, tile), quantity in sorted(_held_stock(record.book, setup.state_agent).items()):
        surplus = quantity - keep.get(good, 0.0)
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


def clear_goods(setup, record, view, area_map, order_book: OrderBook, plans, ledger: YearLedger) -> None:
    """Produce and clear every good in input-depth order."""
    by_output: Dict[str, List[str]] = {}
    for producer_id, producer in sorted(record.producers.items()):
        for good in setup.recipes[producer.recipe_id].outputs:
            by_output.setdefault(good, []).append(producer_id)
    order = input_depth_order(setup.recipes)
    listed = set(order)
    order += sorted({good for good, _area in order_book} - listed)
    done = set()
    in_kind = [form for form in setup.tax_forms if form.paid_in]
    for good in order:
        for producer_id in by_output.get(good, ()):
            if producer_id not in done:
                done.add(producer_id)
                _produce_and_offer(setup, record, view, producer_id, plans.get(producer_id), in_kind,
                                   order_book, ledger)
        areas = sorted(area for item, area in order_book if item == good)
        for area in areas:
            bids, offers = order_book.pop((good, area))
            key = market_key(good, area)
            result = goods_market.clear(bids, offers, good, area, setup.currency_id, record.memory.prices.get(key))
            if result.quantity > 0.0:
                done_settlement = settlement.settle_goods(record.book, result)
                ledger.note_postings(done_settlement.postings, "sales")
                for shortfall in done_settlement.shortfalls:
                    ledger.unpaid[shortfall.agent] = ledger.unpaid.get(shortfall.agent, 0.0) + shortfall.unpaid_amount
            ledger.note_clearing(result)
            if result.price > 0.0 and (result.quantity > 0.0 or key not in record.memory.prices):
                record.memory.prices[key] = result.price
            record.volumes[key] = result.quantity


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
    shortfall = max(0.0, producer.cash_target - cash)
    keep = {good: recipe.inputs.get(good, 0.0) * producer.capacity_runs for good in recipe.outputs}
    offers = producers.offers(producer, recipe, view, stock, shortfall, view.interest_rate(money), setup.specs, keep)
    add_orders(order_book, AgentOrders(offers=tuple(offers)))


def _tax_in_kind(setup, record, producer, recipe, forms, ledger) -> None:
    if not forms:
        return
    output = {(producer.agent_id, good): ledger.output.get((producer.agent_id, good), 0.0) for good in recipe.outputs}
    held = {(producer.agent_id, good): record.book.stock(producer.agent_id, good, producer.tile)
            for good in recipe.outputs}
    facts = YearFacts(currency=setup.currency_id, output=output, producer_tile={producer.agent_id: producer.tile},
                      held_goods=held)
    _transfers, moves, _assessments = taxes.assess(forms, facts, setup.state_agent, {}, setup.state_capacity)
    record.book.move_many(moves)
