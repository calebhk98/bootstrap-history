"""Signatures of the kernels that no hand-built fixture year reaches, so `compile-kernels` compiles them from types.

A kernel the fixture economy steps through needs no entry here: `compile-kernels` runs the fixture and numba compiles
what it reaches. A kernel that only a full civilisation reaches (or only a rare branch) is listed with the numba types
its caller passes: a different dtype or layout compiles a second version the game never calls, so these follow the
callers. `test_compile_kernels` fails when a registered kernel is reached by neither."""


def declared_signatures():
    """{`module.function`: [argument-type tuple, ...]} using numba types; imported lazily so plain Python works."""
    from numba import types
    number = types.float64
    integer = types.int64
    flag = types.boolean

    def array(element, dimensions):
        return types.Array(element, dimensions, "C")

    from numba import typeof
    from sim.economy.api import GOODS_MARKETS, GoodsMarkets
    markets = typeof(GOODS_MARKETS.new_table(GoodsMarkets, 1))      # the namedtuple of columns a goods market kernel takes
    floats, whole, whole_grid = array(number, 1), array(integer, 1), array(integer, 2)

    signatures = {
        "sim.economy.market_table_kernels.remap_goods_markets": [(markets, markets, whole, whole, whole, whole, whole)],
        "sim.economy.market_table_kernels.put_floats": [(floats, whole, whole, whole, integer, whole, floats)],
        "sim.economy.market_table_kernels.drop_floats": [(floats, whole, integer, whole)],
        "sim.economy.market_table_kernels.put_counts": [(whole, whole, whole, whole, whole, integer, integer, whole, whole)],
        "sim.economy.market_table_kernels.drop_counts": [(whole, whole, integer, integer, whole)],
        "sim.economy.market_table_kernels.market_of_good_tile": [(whole_grid, whole_grid)],
        "sim.economy.market_column_kernels.add_in_order_by_group": [(whole, floats, integer)],
        "sim.economy.notional_kernel.costed_goods": [(integer, whole, whole, whole) + (whole, whole, floats) * 5 + (
            floats, floats, array(flag, 1), floats, number, array(flag, 1), flag, floats, floats, number)],
        "sim.economy.market_column_kernels.traded_price_by_group": [(whole, array(flag, 1), floats, floats)],
        "sim.economy.price_kind_kernels.kinds_by_good": [(markets, whole, integer)],
        "sim.economy.goods_table_quotes.untraded_figures": [(whole, whole, floats, floats, floats, floats, floats, array(flag, 1))],
        "sim.economy.goods_table_quotes.wanted_by_market": [(whole, floats, floats, floats, floats, floats, floats, floats)],
        "sim.economy.merchants_kernel.lost_share": [(number, integer)],
        "sim.economy.merchants_kernel.search_good": [(
            array(number, 1), array(number, 2), array(integer, 2), array(integer, 1), array(flag, 1),
            number, number, number, number, number)],
        "sim.geography.routes_tree_kernel.least_tree": [(
            array(integer, 1), array(integer, 1), array(number, 1), array(number, 1), array(integer, 1),
            array(number, 1), array(number, 1), flag)],
        "sim.labour.market.sold_hours_kernel.sold_hours": [(number, array(number, 2), number)],
        "sim.labour.market.state_read_kernels.people_weighted_wage_by_area": [(
            integer, array(flag, 1), floats, array(flag, 1), array(number, 2), whole)],
        "sim.labour.market.state_read_kernels.working_people_in_areas": [(whole, integer, array(flag, 1), array(number, 2), whole)],
        "sim.labour.market.state_read_kernels.scale_pairs": [(integer, integer, number, array(flag, 1), array(number, 2), whole)],
        "sim.labour.market.state_read_kernels.scale_cohorts": [(integer, integer, number, array(number, 2), whole)],
        "sim.labour.market.training_kernel.age_cohorts": [(
            array(integer, 1), array(number, 1), array(number, 1), array(number, 2), integer, integer, array(number, 1), array(flag, 1),
            integer, array(number, 1), number, number, array(number, 2), array(flag, 1), array(integer, 1), array(integer, 1),
            array(flag, 1), array(integer, 1), array(integer, 1), array(number, 1), array(flag, 1), array(flag, 1))],
    }
    signatures.update(book_signatures(types))
    signatures.update(ledger_signatures(types))
    signatures.update(bondage_signatures(types))
    signatures.update(compiled_tables_signatures(types))
    signatures.update(priced_need_signatures(types))
    signatures.update(loan_signatures(types))
    signatures.update(crossing_signatures(types))
    return signatures


def priced_need_signatures(types):
    """The baskets-priced-at-tiles kernel, which no game year calls (the year prices needs one basket at a time; see the plan): typed from
    the tables a batch makes (its helpers compile with it)."""
    from numba import typeof
    from sim.economy.api import GOOD_ROWS, NEED_ROWS, PricedGoodRows, PricedNeedRows
    return {"sim.economy.priced_need_kernel.price_needs": [(
        typeof(NEED_ROWS.new_table(PricedNeedRows, 1)), typeof(GOOD_ROWS.new_table(PricedGoodRows, 1)), types.Array(types.float64, 2, "C"),
        types.float64, types.boolean)]}


def loan_signatures(types):
    """The loan table's kernel that only a write-off reaches, typed from the table the economy keeps."""
    from numba import typeof
    from sim.loans.columns import LOAN_TABLE, Loans
    loan_table = typeof(LOAN_TABLE.new_table(Loans, 1))
    number, integer, flag = types.float64, types.int64, types.boolean
    return {"sim.loans.write_down_kernel.write_down": [(
        loan_table, types.Array(integer, 1, "C"), types.Array(number, 1, "C"), number, types.Array(number, 1, "C"),
        types.Array(flag, 1, "C"))]}


def compiled_tables_signatures(types):
    """The shared table utilities and the documented example table, which no game year calls yet."""
    from numba import typeof
    from sim.compiled_tables.example_loans import LOANS, Loans
    loans = typeof(LOANS.new_table(Loans, 1))
    integer, number = types.int64, types.float64
    return {
        "sim.compiled_tables.sums.ordered_total": [(types.Array(number, 1, "C"), integer)],
        "sim.compiled_tables.example_loans.lend": [(loans, integer, integer, number, number)],
        "sim.compiled_tables.example_loans.interest_due": [(loans, integer)],
        "sim.compiled_tables.example_loans.accrue_interest": [(loans,)],
        "sim.compiled_tables.example_loans.owed_by_agent": [(loans, integer)],
    }


def book_signatures(types):
    """The book's entry kernels that only a batch holding both transfers and goods moves, or a goods total, reaches: typed from
    the tables a fresh book passes them (their callees compile with them)."""
    import numpy
    from numba import typeof
    from sim.book import Book
    from sim.book_apply import RULE_BATCH
    from sim.book_post import new_scratch
    from sim.book_tables import BATCH_OUTCOMES, BatchOutcomes
    book = Book()
    starts = numpy.zeros(2, dtype=numpy.int64)
    apply_arguments = (book._transfer_table([]), starts, book._move_table([]), starts, 1, book.tables(), new_scratch(1, 1),
                       BATCH_OUTCOMES.new_table(BatchOutcomes, 1), RULE_BATCH, True)
    return {
        "sim.book_apply.apply_batches": [tuple(typeof(argument) for argument in apply_arguments)],
        "sim.book_read_kernels.good_quantities": [(typeof(book.stock_rows.table), types.int64)],
        "sim.compiled_tables.grouping.group_starts": [(typeof(starts), types.int64, types.int64)],
    }



def ledger_signatures(types):
    """The year ledger's kernels that only a rare branch reaches (a replaced or removed entry, money across the border), typed from
    the tables a fresh ledger passes them."""
    from numba import typeof
    from sim.economy.api import LedgerTables
    target = typeof(LedgerTables().pairs["received"].target())
    number, integer = types.float64, types.int64
    whole, floats = types.Array(integer, 1, "C"), types.Array(number, 1, "C")
    module = "sim.economy.year_ledger_kernels."
    return {
        "sim.economy.year_ledger_note_kernels.note_settlement_foreign": [(target, target, whole, floats, floats, whole, whole)],
        module + "clear_agent_rows": [(target, integer)],
        module + "kill_row": [(target, integer)],
        module + "set_pair": [(target, integer, integer, integer, number, number)],
        module + "remove_from_figure": [(whole, whole, integer, integer)],
    }


def bondage_signatures(types):
    """The bondage placement kernels, which a year with no bought bonded people and no bonded cohorts never calls: typed from the
    arrays `bondage_hours` passes them."""
    number, integer, flag = types.float64, types.int64, types.boolean
    floats, whole, flags = types.Array(number, 1, "C"), types.Array(integer, 1, "C"), types.Array(flag, 1, "C")
    return {
        "sim.economy.bondage_kernels.place_held_kernel": [(
            whole, floats, floats, whole, whole, whole, whole, whole, whole, floats, floats, number, floats, floats, whole, whole, floats,
            whole, floats, floats)],
        "sim.economy.bondage_kernels.place_bonds_kernel": [(
            whole, whole, whole, floats, whole, floats, floats, whole, whole, whole, floats, whole, number, number, floats, floats, floats,
            floats, flags, flags, whole, floats, floats)],
    }


def crossing_signatures(types):
    """The price search over a market's columns, which only an expansion judged in the close or a price response reaches: typed from
    the prepared columns of one small market (the helpers compile with these)."""
    import numpy
    from numba import typeof
    from sim.economy.api import BidColumns, demand_columns
    columns = BidColumns(*(numpy.ones(2) for _ in range(6)))
    order = numpy.arange(2, dtype=numpy.int64)
    demand = typeof(demand_columns(columns, order))
    floats, flags, number = types.Array(types.float64, 1, "C"), types.Array(types.int64, 1, "C"), types.float64
    return {
        "sim.economy.crossing_columns.prepare_demand": [tuple(typeof(each) for each in (*columns, order))],
        "sim.economy.crossing_price.minimum_price_of": [(floats, number)],
        "sim.economy.crossing_price.single_supply_price": [(demand, types.boolean, number, number, flags)],
        "sim.economy.crossing_price.price_at_levels": [(floats, floats, number, number, demand, flags)],
    }
