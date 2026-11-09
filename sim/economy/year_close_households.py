"""Every cohort's year end: its record after the year, and the goods it used up as one call to the book.

`close_households(setup, record, view, ledger, property_income)` closes the cohorts in id order. The year's receipts of each cohort
(received and grown goods), its wages and what it spent are read from the ledger's tables for all cohorts at once; the cohort's new
record is `households_close.closed_cohort` (the rules that read the view); the goods each uses up are posting rows from a kernel,
cut to what the cohort holds, applied as one call with a batch for each cohort. A cohort's consumption only changes its own stocks,
so the cut reads the same stock the one-cohort-at-a-time loop read."""
from typing import Dict

import numpy as np

from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.causes import OK

from . import cohort_close_write, cohort_prime, household_work_year, households_close, households_close_pack
from .close_pack import figure_values
from .types import EDGE_CONSUMPTION, GoodsMove
from .year_close_household_kernels import consumption_postings, receipts_with_grown

CONSUMPTION_PURPOSE = "consumption"
_READ = ("expected_inflation", "last_basket_price_level", "cash_target", "share_wealth", "last_year_income", "expected_spending",
         "planned_spending", "expected_floor_cost")      # the float fields a close reads from the table
_WRITTEN = ("expected_inflation", "last_basket_price_level", "cash_target", "share_wealth", "last_year_income", "expected_spending",
            "planned_spending", "expected_floor_cost")    # and writes back


def _wealth(value):
    """`share_wealth` as a cohort holds it: None where the column is empty (NaN)."""
    return None if value != value else value


def _good_ranks(names) -> np.ndarray:
    ranks = np.empty(len(names), dtype=np.int64)
    ranks[sorted(range(len(names)), key=names.__getitem__)] = np.arange(len(names))
    return ranks


def _durable_flags(book, specs) -> np.ndarray:
    """Per good number: 1 for a good that is used up (all but the durables, which serve and stay)."""
    consumed = np.ones(len(book.good_ids), dtype=np.uint8)
    for good, spec in specs.items():
        number = book.good_ids.numbers.get(good)
        if number is not None and spec.service_life_years > 0.0:
            consumed[number] = 0
    return consumed


def _number_unseen(book, rows, cohort_ids, tiles_of) -> None:
    """Number, in the order the cohorts are booked, the cohorts and tiles the book has not met and the consumption account, as
    the book would on meeting them one batch at a time. Fills in the giver and tile of the rows that had none."""
    givers, _goods, tiles, _quantities, _batches, owners = rows
    unseen = np.nonzero((givers < 0) | (tiles < 0))[0]
    if not len(unseen) and EDGE_CONSUMPTION in book.agent_ids.numbers:
        return
    seen_batch = -1
    for row, owner in enumerate(owners.tolist()):
        if owner == seen_batch:
            continue
        seen_batch = owner
        if givers[row] < 0:
            givers[owners == owner] = book.agent_number(cohort_ids[owner])
        if tiles[row] < 0:
            tiles[owners == owner] = book.tile_number(tiles_of[owner])
        book.agent_number(EDGE_CONSUMPTION)


def _post_consumption(book, rows) -> None:
    givers, goods, tiles, quantities, batches, _owners = rows
    count = len(givers)
    if not count:
        return
    receiver = book.agent_number(EDGE_CONSUMPTION)
    code, reference = book.purposes.encode(CONSUMPTION_PURPOSE)
    moves = table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, count, givers, np.full(count, receiver), goods, tiles, tiles, quantities,
                       np.full(count, code), np.full(count, reference), batches)
    transfers = table_from(TRANSFER_POSTINGS, TransferPostings, 0, *[[] for _column in TRANSFER_POSTINGS.columns])
    batch_count = int(batches[-1]) + 1
    outcomes, _scratch = book.apply_postings(transfers, moves, batch_count)
    refused = np.nonzero(outcomes.code[:batch_count] != OK)[0]
    if len(refused):         # the book's own refusal for the first cohort whose goods it would not move
        rows_of = np.nonzero(batches == int(refused[0]))[0].tolist()
        good_names, tile_names, agent_names = book.good_ids.name_list, book.tile_ids.name_list, book.agent_ids.name_list
        book.move_many([GoodsMove(agent_names[givers[row]], EDGE_CONSUMPTION, good_names[goods[row]], tile_names[tiles[row]],
                                  float(quantities[row]), CONSUMPTION_PURPOSE) for row in rows_of])


def close_households(setup, record, view, ledger, property_income: Dict[str, float]) -> None:
    book = record.book
    tables = ledger.tables
    if tables.book is not book:
        raise ValueError("the year ledger must number agents and goods as the record's book does")
    store = record.cohorts
    order = store.order()                       # every figure below is for the cohorts in id order
    cohort_ids = [store.ids[row] for row in order.tolist()]
    tiles_of = store.tile_names(order)
    tables.flush()
    agent_numbers = np.array([tables.book.agent_ids.numbers.get(each, -1) for each in cohort_ids], dtype=np.int64)
    figures = tables.figures
    wages = figure_values(figures.wages_in, figures.order_wages_in, agent_numbers).tolist()
    spent = figure_values(figures.money_out, figures.order_money_out, agent_numbers).tolist()
    start, goods, amounts = receipts_with_grown(figures.first_received, tables.pairs["received"].rows.table, figures.first_grown,
                                                tables.pairs["grown"].rows.table, agent_numbers)
    good_names = tables.book.good_ids.name_list
    offered_prices: Dict = {}      # the prices households are closed on do not change while they close
    baskets: Dict = {}
    packed = households_close_pack.PackedBaskets(book, setup.specs)
    hired, milled = store.floats("hired_work_per_person", order), [store.milled_of(row) for row in order.tolist()]
    numbers, floor_costs = [], []
    cohort_prime.prime_cohort_baskets(setup, record, view, False)
    keys = household_work_year.signatures_from_fields(record, tiles_of, cohort_ids, hired, milled)       # the hearths of every cohort in one pass
    for position, key in enumerate(keys):
        # cohorts of one tile, hearth, hired work and milled grains share a basket and its floor cost
        if key not in baskets:
            eaten = household_work_year.eaten_signature(key)
            baskets[key] = (household_work_year.basket_of_signature(setup, eaten),
                            household_work_year.priced_basket_of(setup, view, tiles_of[position], eaten).subsistence_cost_per_person())
        numbers.append(packed.add(key, baskets[key][0]))
        floor_costs.append(baskets[key][1])
    people = store.floats("people", order)
    unmet = households_close_pack.unmet_by_cohort(book, packed, cohort_ids, tiles_of, people, numbers, start, goods, amounts)     # every cohort's shortfall in one kernel call
    columns = {name: store.floats(name, order) for name in _READ}
    plans = [store.pairs_of("plan", row) for row in order.tolist()]
    closed = [households_close.closed_figures(
        cohort_ids[position], tiles_of[position], people[position], columns["expected_inflation"][position],
        columns["last_basket_price_level"][position], columns["cash_target"][position], _wealth(columns["share_wealth"][position]),
        columns["last_year_income"][position], columns["expected_spending"][position], columns["planned_spending"][position],
        columns["expected_floor_cost"][position], plans[position], view, packed.baskets[numbers[position]],
        wages[position] + property_income.get(cohort_ids[position], 0.0), spent[position], floor_costs[position], unmet[position])
        for position in range(len(cohort_ids))]
    cohort_close_write.write_close(store, order, {name: [each[name] for each in closed] for name in _WRITTEN},
                                   [each["unmet_floor_by_need"] for each in closed], [each["own_plan_by_need"] for each in closed])
    tile_numbers = np.array([book.tile_ids.numbers.get(each, -1) for each in tiles_of], dtype=np.int64)
    book_agents = np.array([book.agent_ids.numbers.get(each, -1) for each in cohort_ids], dtype=np.int64)
    rows = consumption_postings(start, goods, amounts, book_agents, tile_numbers, _durable_flags(book, setup.specs),
                                _good_ranks(good_names), book.stock_rows.table, book.stock_rows.index)
    _number_unseen(book, rows, cohort_ids, tiles_of)
    _post_consumption(book, rows)
