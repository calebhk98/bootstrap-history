"""What the close kernel reads that the year arrays do not hold: the year's flows (ledger), the book's stocks and balances,
the loans and the clearing prices, packed once per close into arrays indexed like the producer columns.

`pack(...)` returns a `ClosePack`; `constants_array()` is the rules' declared numbers in the order close_kernel names them.
The book and the ledger are read by the kernels of close_pack_kernels.py, one call each for every producer."""
from dataclasses import dataclass

import numpy as np

from sim.loans.close_kernel import producer_loans

from . import ask_adjust, expected_sales, firm_finance, inventory, plant_investment, producers, producers_close
from .close_pack_markets import clearing_and_unmet, columns_of_markets
from .close_pack_asks import ask_multiples
from .close_pack_kernels import held_goods, pair_values_by_slot, slot_stocks
from .year_arrays import YearArrays
from .year_arrays_memory import NO_AREA


def constants_array() -> np.ndarray:
    return np.array([
        producers.EXPECTATION_ADJUSTMENT_SHARE, producers.REGRESSIVE_EXPECTATION_WEIGHT, producers.COST_SPREAD_WITHIN_PRODUCER,
        producers.OUTPUT_CHANGE_SHARE_PER_YEAR, producers.STOCK_CLEARING_YEARS, inventory.DEFAULT_MONTHS_OF_COVER,
        ask_adjust.GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR, producers_close.CLOSED_CAPACITY_SHARE,
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
    ask_multiple: np.ndarray


def _loans(record, arrays: YearArrays, pack_arrays) -> None:
    """Each producer's interest, commitments, arrears and debt on its loans (one kernel pass over the loan table, loans in table order)."""
    interest, commitments, arrears, debt = pack_arrays
    store = record.credit.contracts.loan_store
    row_of = arrays.producers.row
    producer_row = np.array([row_of.get(name, -1) for name in store.agents.name_list], dtype=np.int64)
    producer_loans(store.table, len(store), producer_row, interest, commitments, arrears, debt)


def _currencies(setup, view, arrays: YearArrays, area_column: np.ndarray):
    """(the currency of each producer's market, as a list of names): a producer's area has one currency; a producer with no area
    has the currency of the area of its recipe's first output on its tile. Asked once for each distinct place."""
    columns = arrays.producers
    recipes = arrays.matrices.recipes.ids
    area_ids = arrays.area_index.areas.ids
    place = np.where(area_column != NO_AREA, area_column, -1 - (columns.recipe_row * len(arrays.tiles.ids) + columns.tile_row))
    _places, first_row, inverse = np.unique(place, return_index=True, return_inverse=True)
    names = []
    tiles = columns.tile_names()
    for row in first_row.tolist():
        area = int(area_column[row])
        if area != NO_AREA:
            names.append(view.currency_of(area_ids[area]))
        else:
            names.append(view.currency_of(view.area_of(min(setup.recipes[recipes[columns.recipe_row[row]]].outputs), tiles[row])))
    return names, inverse.reshape(-1)


def _slot_keys(matrices, subkey_of_column: np.ndarray, slot_columns: np.ndarray) -> np.ndarray:
    """For each recipe and slot, the subkey of the good or trade in the slot (-1 where there is none)."""
    return np.where(slot_columns >= 0, subkey_of_column[np.maximum(slot_columns, 0)], -1)


def _subkeys(names, numbers) -> np.ndarray:
    """The number each name has in `numbers` (a dict of name to number), -1 for a name without one."""
    return np.array([numbers.get(name, -1) for name in names], dtype=np.int64)


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
    currency_names, currency_index = _currencies(setup, view, arrays, area_column)
    currencies = [currency_names[each] for each in currency_index.tolist()]
    agent_numbers = book.rows_of(columns.ids)
    cash_in_money = book.balances_at(agent_numbers, money)
    cash_in_currency = book.balances_by_currency(agent_numbers, currency_index, currency_names)
    goods_row = matrices.goods.row
    book_goods = book.good_ids.numbers
    book_good_of_column = _subkeys(matrices.goods.ids, book_goods)
    column_of_book_good = np.full(len(book.good_ids), -1, dtype=np.int64)
    for name, column in goods_row.items():
        number = book_goods.get(name)
        if number is not None:
            column_of_book_good[number] = column
    tile_numbers = _subkeys(arrays.tiles.ids, book.tile_ids.numbers)[columns.tile_row]
    good_keys = _slot_keys(matrices, book_good_of_column, matrices.slot_goods)
    stock = slot_stocks(book.stock_rows.table, book.stock_rows.index, agent_numbers, tile_numbers, columns.recipe_row, good_keys)
    held_start, held_good, held_quantity = held_goods(book.agent_table.first_slot, book.stock_rows.table, agent_numbers,
                                                      column_of_book_good)
    ledger.tables.flush()
    ledger_book = ledger.tables.book
    if ledger_book is book:
        ledger_agents, ledger_good_keys = agent_numbers, good_keys
    else:       # a ledger with a numbering of its own (a test's)
        ledger_agents = _subkeys(columns.ids, ledger_book.agent_ids.numbers)
        ledger_good_keys = _slot_keys(matrices, _subkeys(matrices.goods.ids, ledger_book.good_ids.numbers), matrices.slot_goods)
    figures = ledger.tables.figures
    revenue = figure_values(figures.sales_in, figures.order_sales_in, ledger_agents)
    paid = figure_values(figures.money_out, figures.order_money_out, ledger_agents)
    plant = figure_values(figures.plant_spend, figures.order_plant_spend, ledger_agents)
    running = np.maximum(0.0, paid - plant)
    pairs = ledger.tables.pairs
    sold = _pair_figures(pairs["sold"], ledger_agents, columns.recipe_row, ledger_good_keys)
    made = _pair_figures(pairs["output"], ledger_agents, columns.recipe_row, ledger_good_keys)
    trade_keys = _slot_keys(matrices, _subkeys(matrices.trades.ids, ledger.tables.markets.trades.numbers), matrices.slot_trades)
    hours = _pair_figures(pairs["hours_hired"], ledger_agents, columns.recipe_row, trade_keys)
    interest, commitments, arrears, debt = (np.zeros(count) for _name in range(4))
    _loans(record, arrays, (interest, commitments, arrears, debt))
    shape = memory.price.shape
    delivered, priced = ledger.market_total_columns()
    market_tables = ledger.tables.markets
    market_figures = ledger.tables.market_figures
    market_count = min(len(market_tables.goods_markets), int(market_figures.row_count[0]))
    table = market_tables.goods_table
    good_column, area_column = columns_of_markets(table.first[:market_count], table.area[:market_count], market_tables.goods.name_list,
                                                  market_tables.areas.name_list, goods_row, arrays.area_index.areas.row)
    clearing, unmet = clearing_and_unmet(shape, delivered, priced, market_figures.unmet, market_figures.order_unmet,
                                         good_column, area_column)
    spoilage = np.zeros(len(matrices.goods.ids))
    ground = np.zeros(len(matrices.goods.ids), dtype=bool)
    for good, spec in setup.specs.items():
        column = goods_row.get(good)
        if column is not None:
            spoilage[column] = spec.spoilage_per_year
            ground[column] = not spec.portable
    return ClosePack(rate_of, cash_in_currency, cash_in_money, revenue, running, stock, sold, made, hours, interest, commitments,
                     arrears, debt, held_start, held_good, held_quantity, clearing, unmet, spoilage, ground, currencies,
                     ask_multiples(setup, record, arrays))


def figure_values(values: np.ndarray, orders: np.ndarray, agent_numbers: np.ndarray) -> np.ndarray:
    """An agent figure of each agent number: zero for an agent (or number -1) that is not a member of the figure."""
    inside = (agent_numbers >= 0) & (agent_numbers < len(orders))
    safe = np.where(inside, agent_numbers, 0)
    return np.where(inside & (orders[safe] != 0), values[safe], 0.0)


def _pair_figures(store, agent_numbers: np.ndarray, recipe_rows: np.ndarray, slot_keys: np.ndarray) -> np.ndarray:
    return pair_values_by_slot(store.rows.table, store.rows.index, agent_numbers, recipe_rows, slot_keys)
