"""`market_curves.summarize` over the columns of a market's rows in the order tables: the same summary of the market's own book, with no
`Bid` or `Offer` made.

`summarize_columns` takes the first round's bids as columns and the offers as columns, with a flag for each that the external edge made
(`EDGE_EXTERNAL`: left out), and answers the summary `market_curves.summarize` gives (the arrays are `market_curves_kernel.curve_arrays`:
bids merged where they share a reference price, elasticity and ceiling, offers merged by price). `of_rows` reads the columns from the
order tables for a cleared market."""
from .market_curves_kernel import curve_arrays, curve_arrays_of_rows
from .types import EDGE_EXTERNAL


def _summary(arrays) -> dict:
    """The summary dict from the arrays of `market_curves_kernel.curve_arrays`."""
    sums, reference, shape, unbounded, ceiling, levels, totals = arrays
    bids = [[floors, flexibles, ref, shape_of, budgets, None if unbound else cap]
            for (floors, flexibles, budgets), ref, shape_of, unbound, cap in zip(
                sums.tolist(), reference.tolist(), shape.tolist(), unbounded.tolist(), ceiling.tolist())]
    return {"bids": bids, "offers": [[level, units] for level, units in zip(levels.tolist(), totals.tolist())]}


def summarize_columns(floor, flexible, reference_price, elasticity, budget, maximum_price, bid_external, price, quantity, offer_external):
    """`market_curves.summarize` of bids and offers given as columns (arrays of one length for each side)."""
    return _summary(curve_arrays(floor, flexible, reference_price, elasticity, budget, maximum_price, bid_external, price, quantity,
                                 offer_external))


def of_rows(orders, bid_rows, offer_rows):
    """`market_curves.summarize` of the market with these bid and offer rows (arrays of rows in the order tables)."""
    bids, offers = orders.tables()
    return _summary(curve_arrays_of_rows(bids, offers, bid_rows, offer_rows, orders.book.agent_ids.numbers.get(EDGE_EXTERNAL, -1)))
