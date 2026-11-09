"""The year's goods orders of households, the state and merchants, written to the book of orders as rows (`order_rows.OrderRows`).

`cohort_orders`, `state_orders` and `merchant_orders` make the households', the state's and the merchants' orders, in arrival order, with no `Bid` or `Offer` handed to the book: each source adds names and figures
to an `OrderRows` and writes it once (the households' kernel rows are appended as before). Rules still written over objects
(`households.goods_orders` for a basket the kernel does not cover, `households_store`, `merchants.orders`) make their objects inside
the rule and are unpacked into rows at this edge."""
from typing import List

from . import household_work_year
from . import carriage_fleet_book, carriage_wear, households_cohort, land_bid, households_orders_pack, land_bid_year, merchants
from . import merchants_book, merchants_plan, state_budget, state_store, tool_wear
from .cohort_order_figures import order_figures
from .cohort_store import table_of
from .goods_order_tables import CARRIER, HOUSEHOLD, MERCHANT, STATE
from .inventory import held_stock, holding_reservation
from .opening_bid_memory import BidMemory
from .order_rows import OrderRows
from .protocols import AgentOrders
from .rates import own_rate


def cohort_orders(setup, record, view, ledger, order_book, own_options=None) -> List:
    """Households' bids for the year; returns their savings offers for the credit market. Every cohort is ordered in one call
    (`households_orders_pack`) from the figures read off the cohort table's columns; no `Cohort` is built."""
    funds = []
    memory = BidMemory()     # the priced needs and store weights cohorts of one basket share
    money = setup.currency_id
    store = table_of(record.cohorts)
    cohorts = order_figures(store, store.order())
    memory.know([each.agent_id for each in cohorts], household_work_year.signatures_of_figures(record, cohorts))
    smooth_rise = not record.settling
    tool_bids_of, entries, plain = {}, [], {}
    cash_of = record.book.balance_by_agent([cohort.agent_id for cohort in cohorts], money)       # nothing posts while the orders are made
    for cohort in cohorts:
        basket = memory.basket(setup, record, cohort)
        priced = memory.priced(setup, record, view, cohort, basket)
        income = ledger.wages_in.get(cohort.agent_id, 0.0) + record.capital_markets.property_income.get(cohort.agent_id, 0.0)
        cash = cash_of[cohort.agent_id]
        plot_hours = ledger.own_plot_hours.get(cohort.agent_id)
        tool_bids = tool_wear.tool_bids(
            cohort.agent_id, cohort.tile, lambda good: view.area_of(good, cohort.tile), lambda good: view.offered_price(good, view.area_of(good, cohort.tile)),
            lambda good: view.stock(cohort.agent_id, good, cohort.tile), setup.recipes, plot_hours, setup.specs, cash) if plot_hours else []
        tool_bids_of[cohort.agent_id] = tool_bids
        spendable = cash - sum(bid.budget for bid in tool_bids)
        grown_units = ledger.grown_units.get(cohort.agent_id)
        if not priced or cohort.people <= 0.0:
            plain[cohort.agent_id] = AgentOrders()
        else:
            entries.append((cohort, basket, priced, spendable, income, grown_units))
    made, bid_rows, planned = households_orders_pack.kernel_orders(
        view, setup.specs, entries, smooth_rise, lambda cohort: memory.key(record, cohort), lambda cohort: memory.stores(record, cohort),
        order_book)
    made.update(plain)
    rows = OrderRows(order_book, HOUSEHOLD)
    land_goods, margins = land_bid.land_goods(setup.specs, setup.recipes), {}      # the ground goods, and the best crop margin by tile, are the same for every cohort
    planned_of = {}          # the money each cohort placed in bids, written to the table once all are known
    for cohort in cohorts:
        orders = made[cohort.agent_id]
        tool_bids = tool_bids_of[cohort.agent_id]
        rows.bids_from(tool_bids)
        planned_of[cohort.agent_id] = sum(bid.budget for bid in tool_bids) + (
            planned[cohort.agent_id] if cohort.agent_id in planned else sum(bid.budget for bid in orders.bids))
        if own_options:
            savings = sum(offer.amount for offer in orders.funds_offers)     # only what it would otherwise lend
            orders = land_bid_year.with_land_bids(orders, land_bid_year.land_bids(
                setup, record, view, cohort, own_options, ledger.spare_hours.get(cohort.agent_id, 0.0), savings,
                land_goods, margins))
        rows.bids_from(orders.bids)
        rows.offers_from(orders.offers)
        funds.extend(orders.funds_offers)
    households_cohort.set_column(record.cohorts, "planned_spending", planned_of)
    rows.write()
    if bid_rows is not None:
        order_book.append_bids(*bid_rows, HOUSEHOLD)       # after every cohort's tool bids, so a cohort's own bids keep their order
    return funds


def state_orders(setup, record, view, area_map, order_book, keep) -> None:
    """The state's bids for its lines and its store, and its offers: what it holds beyond what its own lines will draw, at what holding
    it would net."""
    bids, store_offers, kept = state_store.orders(setup, record, view)
    state_budget.goods_bids(setup, record, view, area_map, order_book, kept)
    rows = OrderRows(order_book, STATE)
    rows.bids_from(bids)
    rows.offers_from(store_offers)
    rate = own_rate(view, setup.currency_id)
    for (good, tile), quantity in sorted(held_stock(record.book, setup.state_agent).items()):
        surplus = quantity - keep.get(good, 0.0) - (kept.get(good, 0.0) if tile == setup.capital_tile else 0.0)
        if surplus <= 0.0 or good not in area_map.goods():
            continue
        area = area_map.area_of(good, tile)
        expected = view.offered_price(good, area)      # what a buyer can see to buy at, not a bid ceiling or a cost quote
        if expected is None:
            continue
        spoilage = setup.specs[good].spoilage_per_year if good in setup.specs else 0.0
        rows.offer(setup.state_agent, good, area, tile, surplus, holding_reservation(expected, rate, spoilage, 0.0))
    rows.write()


def merchant_orders(setup, record, view, area_map, carriage, order_book) -> None:
    """The carriers' replacement bids, then each merchant's orders in the order the rotation gives."""
    money = setup.currency_id
    rate = own_rate(view, money)
    ordered = sorted(record.merchants.values(), key=lambda each: each.agent_id)
    route = merchants_book.route_pass(view, carriage, area_map, setup.specs) if ordered else None
    shares = merchants_book.DenseShares(route.book) if ordered else None
    carrier_bids, carrier_budget = (carriage_fleet_book.bids(setup, record, view, area_map,
                                                       {each.agent_id: record.book.balance(each.agent_id, money) for each in ordered})
                                    if carriage_wear.wears(setup) else ([], {}))
    carriers = OrderRows(order_book, CARRIER)
    carriers.bids_from(carrier_bids)     # replacements for the carriers last year's shipments wore
    carriers.write()
    rows = OrderRows(order_book, MERCHANT)
    merchants_plan.prepare_rows(route, [each for each in ordered if record.book.balance(each.agent_id, money) - carrier_budget.get(each.agent_id, 0.0) > 0.0],
                                rate)
    first = view.year % len(ordered) if ordered else 0          # who sizes first rotates, so no merchant always gets first pick
    for merchant in ordered[first:] + ordered[:first]:
        held = held_stock(record.book, merchant.agent_id)
        orders = merchants.orders(merchant, view, carriage, area_map, record.book.balance(merchant.agent_id, money) - carrier_budget.get(merchant.agent_id, 0.0),
                                  held, setup.specs, rate, shares, route)
        rows.bids_from(orders.bids)
        rows.offers_from(orders.offers)
    rows.write()
