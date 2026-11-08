"""What the close kernel reads that the year arrays do not hold: the year's flows (ledger), the book's stocks and balances,
the loans and the clearing prices, packed once per close into arrays indexed like the producer columns.

`pack(...)` returns a `ClosePack`; `constants_array()` is the rules' declared numbers in the order close_kernel names them."""
import math
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


def slot_of_good(matrices) -> list:
    """For each recipe row, {good column: slot}."""
    return [{int(column): slot for slot, column in enumerate(row) if column >= 0} for row in matrices.slot_goods]


def _fill_by_slot(target: np.ndarray, flows: Mapping, arrays: YearArrays, slots_of_recipe) -> None:
    """`flows` keyed (agent, good): into target[producer row, the recipe's slot of the good]."""
    columns = arrays.producers
    goods_row = arrays.matrices.goods.row
    for (agent, good), quantity in flows.items():
        row = columns.row.get(agent)
        column = goods_row.get(good)
        if row is None or column is None:
            continue
        slot = slots_of_recipe[columns.recipe_row[row]].get(column)
        if slot is not None:
            target[row, slot] += quantity


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
    currencies: Dict[object, str] = {}
    currency_of_row = []
    balance = book.balance
    goods_of = book.goods_of
    cash_in_currency_list, cash_in_money_list = [], []
    slots_of_row = [[(slot, matrices.goods.ids[column]) for slot, column in enumerate(row) if column >= 0] for row in matrices.slot_goods]
    stock_rows, stock_slots, stock_values = [], [], []
    held_start = [0]
    held_good, held_quantity = [], []
    goods_row = matrices.goods.row
    recipe_list, tile_list, area_list = columns.recipe_row.tolist(), columns.tile_row.tolist(), area_column.tolist()
    area_ids = arrays.area_index.areas.ids
    for position, producer_id in enumerate(columns.ids):
        producer = columns.records[position]
        area = area_list[position]
        key = area if area != NO_AREA else (recipe_list[position], tile_list[position])     # an area has one currency
        currency = currencies.get(key)
        if currency is None:
            currency = currencies[key] = view.currency_of(
                area_ids[area] if area != NO_AREA else view.area_of(min(setup.recipes[producer.recipe_id].outputs), producer.tile))
        currency_of_row.append(currency)
        cash_in_currency_list.append(balance(producer_id, currency))
        cash_in_money_list.append(balance(producer_id, money))
        held = goods_of(producer_id)
        if held:
            tile = producer.tile
            for slot, good in slots_of_row[recipe_list[position]]:
                by_tile = held.get(good)
                if by_tile:
                    quantity = by_tile.get(tile)
                    if quantity:
                        stock_rows.append(position)
                        stock_slots.append(slot)
                        stock_values.append(quantity)
            for good in sorted(held):        # goods in name order, whatever order the book holds them in
                column = goods_row.get(good)
                tiles = held[good]
                if column is not None and any(value != 0.0 for value in tiles.values()):
                    held_good.append(column)
                    held_quantity.append(math.fsum(value for value in tiles.values() if value > 0.0))
        held_start.append(len(held_good))
    cash_in_currency, cash_in_money = np.array(cash_in_currency_list), np.array(cash_in_money_list)
    held_start = np.array(held_start, dtype=np.int64)
    stock = np.zeros((count, matrices.good_slots))
    stock[stock_rows, stock_slots] = stock_values
    revenue = ledger.sales_in.values_of(columns.ids)
    running = ledger.running_costs_of(columns.ids)
    sold = np.zeros_like(stock)
    made = np.zeros_like(stock)
    slots_of_recipe = slot_of_good(matrices)
    _fill_by_slot(sold, ledger.sold, arrays, slots_of_recipe)
    _fill_by_slot(made, ledger.output, arrays, slots_of_recipe)
    hours = np.zeros((count, matrices.slot_trades.shape[1]))
    trade_slots = [{int(column): slot for slot, column in enumerate(row) if column >= 0} for row in matrices.slot_trades]
    for agent, trades in ledger.hours_hired.items():
        row = columns.row.get(agent)
        if row is None:
            continue
        slots = trade_slots[columns.recipe_row[row]]
        for trade, value in trades.items():
            slot = slots.get(matrices.trades.row.get(trade, -1))
            if slot is not None:
                hours[row, slot] += value
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
