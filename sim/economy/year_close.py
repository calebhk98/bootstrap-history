"""The year's end: carriage, money taxes, the mint, every agent's close, spoilage, and what the
markets remember for next year."""
import dataclasses
import math
from typing import Dict, Tuple

from . import currency, households, inventory, merchants, metal_stock, producers, producers_close, taxes
from .market_memory import market_key
from .setup import labour_area
from .taxes_bases import YearFacts
from .types import is_edge
from .year_goods import _held_stock
from .year_ledger import YearLedger


def dispatch_merchants(setup, record, carriage, ledger: YearLedger) -> None:
    money = setup.currency_id
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        fills = ledger.buy_fills.get(merchant.agent_id, [])
        if not fills:
            continue
        done = merchants.dispatch(merchant, fills, carriage, setup.specs, money,
                                  record.book.balance(merchant.agent_id, money), _held_stock(record.book, merchant.agent_id))
        record.book.post(done.transfers, done.moves)
        ledger.note_postings(done.transfers)


def money_taxes(setup, record, view, ledger: YearLedger) -> None:
    forms = [form for form in setup.tax_forms if not form.paid_in]
    if not forms:
        return
    money = setup.currency_id
    hours = setup.working_hours_per_year
    working = {cohort.agent_id: cohort.working_people for cohort in record.cohorts.values()}
    wage_year = {cohort.agent_id: (view.wage(setup.unskilled_trade, labour_area(cohort.tile)) or 0.0) * hours
                 for cohort in record.cohorts.values()}
    cash = {agent: record.book.balance(agent, money) for agent in record.book.agents() if not is_edge(agent)}
    facts = YearFacts(currency=money, working_people=working, wage_per_labour_year=wage_year, cash=cash)
    transfers, _moves, _assessments = taxes.assess(forms, facts, setup.state_agent, {}, setup.state_capacity)
    record.book.transfer_many(transfers)
    ledger.note_postings(transfers)


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
        costs = ledger.money_out.get(producer_id, 0.0)
        closed = producers_close.close_year(producer, recipe, revenue, costs, view)
        if closed.exited:
            # a run of losses mothballs the plant rather than scrapping it: it keeps its cash and wears
            # out unless prices bring it back to work (share_working decides how much of it works)
            wear = 1.0 / recipe.plant_life_years if recipe.plant_life_years > 0.0 else 0.0
            record.producers[producer_id] = _with_sales(dataclasses.replace(
                producer, capacity_runs=producer.capacity_runs * (1.0 - wear), years_of_loss=0,
                expected_prices=closed.producer.expected_prices), recipe, ledger)
            continue
        record.book.transfer_many(closed.transfers)
        for transfer in closed.transfers:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
        if closed.loan_request is not None:
            record.loan_requests.append(closed.loan_request)
            record.expansion_runs[producer_id] = closed.expansion_runs
        record.producers[producer_id] = _with_sales(closed.producer, recipe, ledger)
    prices = {}
    volumes = {}
    for result in ledger.clearings:
        prices[(result.good, result.area)] = result.price
        volumes[(result.good, result.area)] = result.quantity
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        transfers = merchants.close_year(merchant, prices, volumes, record.book.balance(merchant.agent_id, money),
                                         _held_stock(record.book, merchant.agent_id), area_map.area_of, money)
        record.book.transfer_many(transfers)
        for transfer in transfers:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
    for cohort_id, cohort in sorted(record.cohorts.items()):
        received = dict(ledger.received.get(cohort_id, {}))
        for good, quantity in ledger.grown.get(cohort_id, {}).items():
            received[good] = received.get(good, 0.0) + quantity
        income = ledger.wages_in.get(cohort_id, 0.0) + record.property_income.get(cohort_id, 0.0)
        spent = ledger.money_out.get(cohort_id, 0.0)
        closed, moves = households.close_year(cohort, received, view, setup.specs, setup.basket, income, spent)
        record.book.move_many(moves)
        record.cohorts[cohort_id] = closed
    record.property_income = property_income


def _with_sales(producer, recipe, ledger: YearLedger):
    """Expected sales move toward what it sold this year, in runs of its main output."""
    good = producers.main_output(recipe)
    sold = ledger.sold.get((producer.agent_id, good), 0.0) / recipe.outputs[good]
    if producer.expected_sales <= 0.0:
        return dataclasses.replace(producer, expected_sales=sold)
    share = producers.EXPECTATION_ADJUSTMENT_SHARE
    return dataclasses.replace(producer, expected_sales=producer.expected_sales + share * (sold - producer.expected_sales))


def national_prices(record) -> Dict[str, float]:
    """Each good's price over its areas, weighted by what traded there."""
    totals: Dict[str, Tuple[float, float, float]] = {}
    for key, price in record.memory.prices.items():
        good = key.split("|", 1)[0]
        volume = record.volumes.get(key, 0.0)
        value, quantity, plain = totals.get(good, (0.0, 0.0, 0.0))
        totals[good] = (value + price * volume, quantity + volume, plain or price)
    return {good: (value / quantity if quantity > 0.0 else plain)
            for good, (value, quantity, plain) in sorted(totals.items())}


def remember_price_level(setup, record) -> float:
    level = currency.price_level(national_prices(record), record.index_base_prices or setup.opening_prices,
                                 record.opening_basket)
    record.memory.note_price_level(setup.currency_id, level)
    return level


def check_money(record) -> float:
    """Largest residual share across currencies and goods: zero when everything has a counterparty."""
    report = record.book.check_conservation(1e-9)
    shares = list(report.money.values()) + list(report.goods.values())
    return max((abs(share) for share in shares), default=0.0) if shares else 0.0
