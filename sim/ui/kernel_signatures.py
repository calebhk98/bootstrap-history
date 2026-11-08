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
        "sim.economy.merchants_kernel.lost_share": [(number, integer)],
        "sim.economy.merchants_kernel.search_good": [(
            array(number, 1), array(number, 2), array(integer, 2), array(integer, 1), array(flag, 1),
            number, number, number, number, number)],
        "sim.geography.routes_tree_kernel.least_tree": [(
            array(integer, 1), array(integer, 1), array(number, 1), array(number, 1), array(integer, 1),
            array(number, 1), array(number, 1), flag)],
        "sim.labour.market.sold_hours_kernel.sold_hours": [(number, array(number, 2), number)],
    }
    signatures.update(book_signatures(types))
    signatures.update(ledger_signatures(types))
    return signatures


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
    from sim.economy.year_ledger_store import LedgerTables
    target = typeof(LedgerTables().pairs["received"].target())
    number, integer = types.float64, types.int64
    whole, floats = types.Array(integer, 1, "C"), types.Array(number, 1, "C")
    module = "sim.economy.year_ledger_kernels."
    return {
        module + "note_settlement_foreign": [(target, target, whole, floats, floats, whole, whole)],
        module + "clear_agent_rows": [(target, integer)],
        module + "kill_row": [(target, integer)],
        module + "set_pair": [(target, integer, integer, integer, number, number)],
        module + "remove_from_figure": [(whole, whole, integer, integer)],
    }
