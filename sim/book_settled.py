"""A good's settled markets applied on the book by numbers (the id-based twin of `Book.post_settled`).

`post_settled_by_numbers` takes the batch's per-agent sums and per-key goods as book numbers, applies them with `book_apply.apply_settled`
and records the gross totals and the good's flow as `Book.post_settled` records them. The settlement rules live in the economy; the book's
tables are written here."""
import math

import numpy

from sim.book_apply import apply_settled
from sim.book_commit import add_flow
from sim.book_post import grown_settled
from sim.compiled_tables.causes import OK


def reserve_for_settlement(book, agents: int, keys: int) -> None:
    """Room in the book for a settlement of that many agents and stock keys: stock and edge-goods rows, the flow row and the plans."""
    book.stock_rows.reserve(keys)
    book.edge_goods_rows.reserve(keys)
    book.flow_rows.reserve(1)
    book.settled_plans = grown_settled(book.settled_plans, agents, keys)


def settlement_plans(book):
    """The book's plans for summed settlements, made when it has none."""
    if book.settled_plans is None:
        book.settled_plans = grown_settled(None, 8, 8)
    return book.settled_plans


def post_settled_by_numbers(book, currency: str, purpose: str, item: str, currency_number: int, good: int, agents, paid, received, holder, tile,
                given, taken) -> None:
    """Apply the batch's sums on the book as `Book.post_settled` does, by numbers; a refusal is replayed through `post_settled` by
    name so the error is the book's own."""
    reserve_for_settlement(book, len(agents), len(holder))
    scratch = book.settled_plans
    code, _culprit = apply_settled(book.tables(), scratch, currency_number, agents, paid, received, holder, tile, good, given, taken)
    if code != OK:
        names, tiles = book.agent_ids.name_list, book.tile_ids.name_list
        book.post_settled(currency, purpose, item, [names[each] for each in agents.tolist()], paid.tolist(), received.tolist(),
                          [(names[each], tiles[place]) for each, place in zip(holder.tolist(), tile.tolist())], given.tolist(),
                          taken.tolist())
        raise RuntimeError("the book refused the sale of %s and then took it" % item)
    record_totals(book, currency_number, good, purpose, paid, given)


def record_totals(book, currency_number: int, good: int, purpose: str, paid: numpy.ndarray, given: numpy.ndarray) -> None:
    """The gross totals and the purpose flow of a settlement: exact sums added to the totals, as `Book._record_settled_totals`."""
    currencies = book.currency_table
    before = currencies.gross_posted.item(currency_number) if currencies.gross_seen.item(currency_number) else 0.0
    currencies.gross_posted[currency_number] = before + math.fsum(paid.tolist())
    currencies.gross_seen[currency_number] = 1
    moved = math.fsum(given.tolist())
    if moved > 0.0:
        goods = book.good_table
        before = goods.gross_moved.item(good) if goods.gross_seen.item(good) else 0.0
        goods.gross_moved[good] = before + moved
        goods.gross_seen[good] = 1
        code, reference = book.purposes.encode(purpose)
        add_flow(book.flow_rows.table, book.flow_rows.index, good, code, reference, moved)
