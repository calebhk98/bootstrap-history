"""The year's end: carriage, money taxes, the mint, every agent's close, spoilage, and what the
markets remember for next year."""
import dataclasses
import math
from typing import Dict, Tuple

from . import (currency, households, inventory, merchants, metal_stock, ownership, producer_exit, producers, producers_close,
               state_budget, taxes)
from .households_cohort import renewed
from .market_memory import market_key
from .national_prices import national_prices
from .notional import recently_traded_goods
from .setup import labour_area
from .taxes_bases import YearFacts
from .types import is_edge
from .year_goods import _held_stock
from .year_ledger import YearLedger


def dispatch_merchants(setup, record, carriage, ledger: YearLedger) -> None:
    """Merchants carry what they bought. The carriage is the carters' pay: it goes, as wages, to the
    poorest households of the tile the goods leave. Shortcut until carriers hire hours in the labour
    market: the carters' hours are not taken from what those households offer."""
    money = setup.currency_id
    carriers = {}
    for cohort in record.cohorts.values():
        held = carriers.get(cohort.tile)
        if held is None or cohort.income_class < record.cohorts[held].income_class:
            carriers[cohort.tile] = cohort.agent_id
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        fills = ledger.buy_fills.get(merchant.agent_id, [])
        if not fills:
            continue
        done = merchants.dispatch(merchant, fills, carriage, setup.specs, money,
                                  record.book.balance(merchant.agent_id, money), _held_stock(record.book, merchant.agent_id),
                                  carrier_of=carriers.get)
        record.book.post(done.transfers, done.moves)
        ledger.note_postings(done.transfers, "wages")


def tax_facts(setup, record, view, ledger: YearLedger) -> YearFacts:
    money = setup.currency_id
    hours = setup.working_hours_per_year
    working = {cohort.agent_id: cohort.working_people for cohort in record.cohorts.values()}
    wage_year = {cohort.agent_id: (view.wage(setup.unskilled_trade, labour_area(cohort.tile)) or 0.0) * hours
                 for cohort in record.cohorts.values()}
    cash = {agent: record.book.balance(agent, money) for agent in record.book.agents() if not is_edge(agent)}
    return YearFacts(currency=money, working_people=working, wage_per_labour_year=wage_year, cash=cash,
                     imports_paid=ledger.imports_paid, exports_received=ledger.exports_received)


def money_taxes(setup, record, view, ledger: YearLedger) -> None:
    forms = [form for form in setup.tax_forms if not form.paid_in]
    received = 0.0
    if forms:
        facts = tax_facts(setup, record, view, ledger)
        transfers, _moves, _assessments = taxes.assess(forms, facts, setup.state_agent, {}, setup.state_capacity)
        record.book.transfer_many(transfers)
        ledger.note_postings(transfers)
        received = math.fsum(transfer.amount for transfer in transfers)
    state_budget.close_year(setup, record, ledger, received)


def wear_and_spoilage(setup, record) -> None:
    book = record.book
    holdings: Dict[Tuple[str, str, str], float] = {}
    for agent in book.agents():
        if is_edge(agent):
            continue
        for good, tiles in book.holdings(agent)["goods"].items():
            for tile, quantity in tiles.items():
                if quantity > 0.0:
                    holdings[(agent, good, tile)] = quantity
    book.move_many(inventory.spoilage_moves(holdings, setup.specs))
    book.move_many(inventory.wear_moves(holdings, setup.specs, set(record.cohorts)))
    cash = {agent: book.balance(agent, record.currency.currency_id) for agent in book.agents() if not is_edge(agent)}
    book.transfer_many(metal_stock.yearly_wear(cash, record.currency))


def close_agents(setup, record, view, ledger: YearLedger, area_map) -> None:
    money = setup.currency_id
    property_income: Dict[str, float] = {}
    for producer_id, producer in sorted(record.producers.items()):
        recipe = setup.recipes[producer.recipe_id]
        revenue = ledger.sales_in.get(producer_id, 0.0)
        costs = ledger.running_costs(producer_id)
        per_run = recipe.outputs[producers.main_output(recipe)]
        worked = ledger.output.get((producer_id, producers.main_output(recipe)), 0.0) / (
            per_run * producer.yield_factor or per_run)
        closed = producers_close.close_year(producer, recipe, revenue, costs, view, worked)
        if closed.exited:
            paid = producer_exit.exit_producer(record, producer_id, list(closed.transfers))
            for transfer in paid:
                property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
            continue
        paid = ownership.spread(record, closed.transfers)
        record.book.transfer_many(paid)
        worn = producer.capacity_runs - closed.producer.capacity_runs
        if worn > 0.0 and recipe.plant_life_years > 0.0 and revenue > costs:
            record.worn_runs[producer_id] = worn    # a producer covering its costs rebuilds what wore out
        for transfer in paid:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
        if closed.loan_request is not None:
            record.loan_requests.append(closed.loan_request)
            record.expansion_runs[producer_id] = closed.expansion_runs
        record.producers[producer_id] = _with_sales(closed.producer, recipe, ledger)
    prices, volumes = learned_prices(ledger.clearings, record.memory)
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        transfers = merchants.close_year(merchant, prices, volumes, record.book.balance(merchant.agent_id, money),
                                         _held_stock(record.book, merchant.agent_id), area_map.area_of, money,
                                         view.interest_rate(money))
        paid = ownership.spread(record, transfers)
        record.book.transfer_many(paid)
        for transfer in paid:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
    for cohort_id, cohort in sorted(record.cohorts.items()):
        received = dict(ledger.received.get(cohort_id, {}))
        for good, quantity in ledger.grown.get(cohort_id, {}).items():
            received[good] = received.get(good, 0.0) + quantity
        income = ledger.wages_in.get(cohort_id, 0.0) + record.property_income.get(cohort_id, 0.0)
        spent = ledger.money_out.get(cohort_id, 0.0)
        closed, moves = households.close_year(cohort, received, view, setup.specs, setup.basket_for(cohort.tile),
                                                   income, spent)
        record.book.move_many(held_only(moves, record.book))
        record.cohorts[cohort_id] = closed
    record.property_income = property_income


def learned_prices(clearings, memory):
    """(prices, volumes) by (good, area) that traders learn from the year: the price the market now
    remembers, which for a market that sold nothing is what buyers would have paid."""
    prices, volumes = {}, {}
    for result in clearings:
        key = (result.good, result.area)
        prices[key] = memory.prices.get(market_key(result.good, result.area), result.price)
        volumes[key] = result.quantity
    return prices, volumes


def held_only(moves, book):
    """The moves with each giver's quantity cut to what it holds: settlement can deliver a rounding hair
    less than a fill, and an agent consumes what it has, not what its fills say."""
    return [move if is_edge(move.giver) else
            dataclasses.replace(move, quantity=min(move.quantity, max(0.0, book.stock(move.giver, move.good, move.tile))))
            for move in moves]


def _with_sales(producer, recipe, ledger: YearLedger):
    """Expected sales move toward what it sold this year, in runs of its main output."""
    good = producers.main_output(recipe)
    per_run = recipe.outputs[good]
    sold = ledger.sold.get((producer.agent_id, good), 0.0) / per_run
    worked = ledger.output.get((producer.agent_id, good), 0.0) / (per_run * producer.yield_factor or per_run)
    if producer.expected_sales <= 0.0:
        return dataclasses.replace(producer, expected_sales=sold, last_runs=worked)
    share = producers.EXPECTATION_ADJUSTMENT_SHARE
    return dataclasses.replace(producer, expected_sales=producer.expected_sales + share * (sold - producer.expected_sales),
                               last_runs=worked)


def remember_price_level(setup, record) -> float:
    """The fixed basket's cost at today's prices over its cost at the base prices, over the goods that
    traded recently (notional.RECENT_TRADE_YEARS): a good that has not cleared holds only an estimate,
    and an estimate frozen at its base price would damp measured inflation. The basket's quantities
    stay those of the opening; which goods are priced follows trade."""
    recent = recently_traded_goods(record.memory)
    prices = {good: price for good, price in national_prices(record).items() if good in recent}
    level = currency.price_level(prices, record.index_base_prices or setup.opening_prices, record.opening_basket)
    record.memory.note_price_level(setup.currency_id, level)
    return level


def rebase_price_level(setup, record) -> None:
    """Today's prices become the index base (level one) and everyone, the market's memory and each
    household alike, stops expecting inflation, so the rebase is not read as a jump in prices."""
    money = setup.currency_id
    record.index_base_prices = national_prices(record)
    record.memory.price_levels[money] = 1.0
    record.memory.expected_inflation[money] = 0.0
    record.cohorts = {agent: renewed(cohort, last_price_level=1.0, expected_inflation=0.0)
                      for agent, cohort in record.cohorts.items()}


def check_money(record) -> float:
    """Largest residual share across currencies and goods: zero when everything has a counterparty."""
    report = record.book.check_conservation(1e-9)
    shares = list(report.money.values()) + list(report.goods.values())
    return max((abs(share) for share in shares), default=0.0) if shares else 0.0
