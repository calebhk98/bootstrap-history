"""What the close kernel reads that the year arrays do not hold: the year's flows (ledger), the book's stocks and balances,
the loans and the clearing prices, packed once per close into arrays indexed like the producer columns.

`pack(...)` returns a `ClosePack`; `constants_array()` is the rules' declared numbers in the order close_kernel names them."""
from dataclasses import dataclass
from typing import Dict, Mapping

import numpy as np

from . import ask_adjust, credit, expected_sales, firm_finance, inventory, plant_investment, producers, producers_close
from .year_arrays import YearArrays
from .year_arrays_memory import NO_AREA


def constants_array() -> np.ndarray:
    return np.array([
        producers.EXPECTATION_ADJUSTMENT_SHARE, producers.REGRESSIVE_EXPECTATION_WEIGHT, producers.COST_SPREAD_WITHIN_PRODUCER,
        producers.OUTPUT_CHANGE_SHARE_PER_YEAR, producers.STOCK_CLEARING_YEARS, inventory.DEFAULT_MONTHS_OF_COVER,
        ask_adjust.GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR, ask_adjust.ASK_BAND_CEILING, producers_close.CLOSED_CAPACITY_SHARE,
        producers_close.WORKING_CAPITAL_YEARS_OF_VARIABLE_COST, plant_investment.INVESTMENT_INERTIA,
        firm_finance.DIVIDEND_EARNINGS_RATIO, firm_finance.FULL_PAYOUT_YEARS_OF_REVENUE, firm_finance.DEBT_RESCALING_FACTOR,
        firm_finance.BANKRUPTCY_IDLE_YEARS, firm_finance.CASH_BUFFER_SHARE_OF_COSTS, firm_finance.ARREARS_EPSILON,
        max(0, firm_finance.HISTORY_YEARS - 1), expected_sales.SOLD_OUT_LEFT_SHARE], dtype=np.float64)


@dataclass
class ClosePack:
    rate_of: np.ndarray
    cash_in_currency: np.ndarray
    cash_in_money: np.ndarray
    revenue: np.ndarray
    running_costs: np.ndarray
    stock: np.ndarray
    sold: np.ndarray
    made: np.ndarray
    hours_hired: np.ndarray
    interest: np.ndarray
    commitments: np.ndarray
    arrears: np.ndarray
    debt: np.ndarray
    held_start: np.ndarray
    held_good: np.ndarray
    held_quantity: np.ndarray
    clearing: np.ndarray
    unmet: np.ndarray
    spoilage: np.ndarray
    ground: np.ndarray
    currencies: list


def _fill_by_slot(target: np.ndarray, flows: Mapping, arrays: YearArrays) -> None:
    """`flows` keyed (agent, good): into target[producer row, the recipe's slot of the good]."""
    producers_ = arrays.producers
    matrices = arrays.matrices
    for (agent, good), quantity in flows.items():
        row = producers_.row.get(agent)
        column = matrices.goods.row.get(good)
        if row is None or column is None:
            continue
        slots = np.nonzero(matrices.slot_goods[producers_.recipe_row[row]] == column)[0]
        if len(slots):
            target[row, slots[0]] += quantity


def _loans(record, arrays: YearArrays, pack_arrays) -> None:
    interest, commitments, arrears, debt = pack_arrays
    row_of = arrays.producers.row
    for loan in record.credit.loans:
        row = row_of.get(loan.borrower)
        if row is None:
            continue
        interest[row] += loan.principal * loan.rate
        commitments[row] += loan.principal * loan.rate + credit.installment_of(loan)
        arrears[row] += loan.arrears
        debt[row] += loan.principal + loan.arrears


def pack(setup, record, view, ledger, arrays: YearArrays) -> ClosePack:
    columns = arrays.producers
    matrices = arrays.matrices
    memory = arrays.memory
    count = len(columns.ids)
    book = record.book
    money = setup.currency_id
    own_rate = record.memory.rates.get(money, np.nan)
    first = matrices.first_output[columns.recipe_row]
    area_column = arrays.area_index.of_good_tile[first, columns.tile_row]
    rate_of = np.where(area_column == NO_AREA, own_rate, memory.rate[np.maximum(area_column, 0)])
    currencies: Dict[tuple, str] = {}
    cash_in_currency = np.zeros(count)
    currency_of_row = []
    cash_in_money = np.zeros(count)
    stock = np.zeros((count, matrices.good_slots))
    held_start = np.zeros(count + 1, dtype=np.int64)
    held_good, held_quantity = [], []
    goods_row = matrices.goods.row
    for position, producer_id in enumerate(columns.ids):
        producer = columns.records[position]
        key = (int(first[position]), int(columns.tile_row[position]))
        currency = currencies.get(key)
        if currency is None:
            currency = currencies[key] = view.currency_of(view.area_of(min(setup.recipes[producer.recipe_id].outputs), producer.tile))
        currency_of_row.append(currency)
        cash_in_currency[position] = book.balance(producer_id, currency)
        cash_in_money[position] = book.balance(producer_id, money)
        for slot, column in enumerate(matrices.slot_goods[columns.recipe_row[position]]):
            if column < 0:
                break
            stock[position, slot] = book.stock(producer_id, matrices.goods.ids[column], producer.tile)
        for good, tiles in book.holdings(producer_id)["goods"].items():
            column = goods_row.get(good)
            quantity = sum(value for value in tiles.values() if value > 0.0)
            if column is not None:
                held_good.append(column)
                held_quantity.append(quantity)
        held_start[position + 1] = len(held_good)
    revenue = np.array([ledger.sales_in.get(each, 0.0) for each in columns.ids])
    running = np.array([ledger.running_costs(each) for each in columns.ids])
    sold = np.zeros_like(stock)
    made = np.zeros_like(stock)
    _fill_by_slot(sold, ledger.sold, arrays)
    _fill_by_slot(made, ledger.output, arrays)
    hours = np.zeros((count, matrices.slot_trades.shape[1]))
    for agent, trades in ledger.hours_hired.items():
        row = columns.row.get(agent)
        if row is None:
            continue
        slots = matrices.slot_trades[columns.recipe_row[row]]
        for trade, value in trades.items():
            column = matrices.trades.row.get(trade)
            found = np.nonzero(slots == column)[0] if column is not None else ()
            if len(found):
                hours[row, found[0]] += value
    interest, commitments, arrears, debt = (np.zeros(count) for _name in range(4))
    _loans(record, arrays, (interest, commitments, arrears, debt))
    shape = memory.price.shape
    clearing, unmet = np.full(shape, np.nan), np.zeros(shape)
    traded, round_prices = ledger.market_totals()
    area_row = arrays.area_index.areas.row
    for (good, area), price in round_prices.items():
        column, good_column = area_row.get(area), goods_row.get(good)
        if column is not None and good_column is not None and traded[(good, area)] > 0.0 and price is not None:
            clearing[good_column, column] = price
    for (good, area), quantity in ledger.unmet_demand.items():
        column, good_column = area_row.get(area), goods_row.get(good)
        if column is not None and good_column is not None:
            unmet[good_column, column] = quantity
    spoilage = np.zeros(len(matrices.goods.ids))
    ground = np.zeros(len(matrices.goods.ids), dtype=bool)
    for good, spec in setup.specs.items():
        column = goods_row.get(good)
        if column is not None:
            spoilage[column] = spec.spoilage_per_year
            ground[column] = not spec.portable
    return ClosePack(rate_of, cash_in_currency, cash_in_money, revenue, running, stock, sold, made, hours, interest, commitments,
                     arrears, debt, held_start, np.array(held_good, dtype=np.int64), np.array(held_quantity), clearing, unmet,
                     spoilage, ground, currency_of_row)
