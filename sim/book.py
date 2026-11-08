"""The double-entry book: every agent's money (per currency) and goods (per good per tile).

It is a top-level module because both the economy's agents and the actors' purses (`sim/agents/purses.py`)
keep their holdings in a book of this one class.

Money and goods change hands only through `transfer` and `move` (or the batch forms), so each
posting has a counterparty. Edge accounts (`is_edge`) are the only ones that may go negative;
they are where the model meets what it does not simulate, and the sum over all accounts stays zero.

Layout: the state is compiled tables with integer ids (agents, goods, tiles, currencies), described in sim/book_tables.py and
kept by sim/book_store.py. Postings are rows of two posting tables applied by a kernel (sim/book_apply.py), all or none per
batch; the methods here, by name, are thin wrappers that build the rows, call the kernel and turn a refusal back into an error.
A converter that holds ids calls `apply_postings` and the kernels of sim/book_read_kernels.py instead.

The mixins, by topic:  BookStore (ids, tables, admitting names)  BookPostings (post, transfer, move, apply_postings)  BookSingle (one posting on its own)
BookReads (balance, stock, holdings, totals, flows)  BookBatch (many reads, post_settled)  BookRecord (save, merge, rename).
"""
from sim.book_batch import BookBatch
from sim.book_post import BookPostings
from sim.book_reads import BookReads
from sim.book_record import BookRecord
from sim.book_single import BookSingle
from sim.book_store import BookStore
from sim.book_types import (  # noqa: F401  (the names callers import from here)
    EDGE_EXCHANGE, EDGE_PREFIX, ROUNDING_SHARE, UNDERFLOW, AgentId, BookError, ConservationReport, CurrencyId,
    DeliveredMove, GoodId, GoodsMove, InsufficientFunds, InsufficientGoods, NegativeAmount, TileId, Transfer, delivery_tile,
    is_edge, _share)


class Book(BookStore, BookPostings, BookSingle, BookReads, BookBatch, BookRecord):
    pass
