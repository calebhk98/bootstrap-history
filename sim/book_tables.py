"""The book's tables: what each column holds, and the namedtuple types kernels take.

Ids (all `IdTable`s owned by the book, saved as name lists): agents, goods, tiles, currencies, kinds (the text of an agent
id before its first colon), purpose templates and purpose references (`sim/book_purposes.py`).

Tables, by the thing a row is:
    Agents      one row per agent id            flags set at admission, whether the book knows it, the head and tail of its
                                                chain of stock slots
    Balances    one row per (agent, currency)   row = agent * stride + currency; the balance and, for an edge account, this
                                                year's volume and net
    Currencies  one row per currency id         everything ever posted, and the supply when the year began
    Goods       one row per good id             everything ever moved
    Stocks      one row per (agent, good, tile) found through a hash index on `key`
    PurposeFlows one row per (good, purpose)    this year's quantity moved for that purpose
    EdgeGoods   one row per (edge agent, good)  this year's volume and net
Postings (appended during a phase, applied by `sim/book_apply.py`, all or none per batch):
    TransferPostings, GoodsMovePostings, and BatchOutcomes (one row per batch: whether it applied, and if not why)
Scratch for one apply call: Plans (the cells a batch touches, before and after).

Rows `0 .. row_count - 1` are in use (see sim/compiled_tables/spec.py). A column named in a docstring as "flag" is 0 or 1."""
import collections

import numpy

from sim.compiled_tables.causes import Causes
from sim.compiled_tables.spec import Column, TableSpec

AGENTS = TableSpec("Agents", (
    Column("is_edge", numpy.uint8, "flag: an edge account, the only kind allowed to go negative", "0 or 1"),
    Column("is_mint", numpy.uint8, "flag: the account coin is struck from and melted into (an edge)", "0 or 1"),
    Column("is_external", numpy.uint8, "flag: an edge standing for a foreign economy the model does not simulate", "0 or 1"),
    Column("kind", numpy.int64, "the text of the agent id before its first colon, as a number in the kinds ids (empty if none)",
           "kind id", ids="kinds"),
    Column("known", numpy.uint8, "flag: the agent has held or paid something in this book (a refused posting does not set it)",
           "0 or 1"),
    Column("first_slot", numpy.int64, "the agent's first stock slot, or -1 when it has none", "stock slot"),
    Column("last_slot", numpy.int64, "the agent's newest stock slot, or -1 when it has none", "stock slot"),
))
Agents = AGENTS.make_type(__name__)

BALANCES = TableSpec("Balances", (
    Column("amount", numpy.float64, "what the agent holds of the currency (negative only for an edge account)", "currency units"),
    Column("seen", numpy.uint8, "flag: the cell has been posted or loaded, so it is part of the agent's holdings", "0 or 1"),
    Column("edge_volume", numpy.float64, "this year's gross money in and out through the edge account", "currency units"),
    Column("edge_net", numpy.float64, "this year's money the edge paid into the economy less what it took out", "currency units"),
    Column("edge_seen", numpy.uint8, "flag: edge_volume and edge_net have been started this year", "0 or 1"),
))
Balances = BALANCES.make_type(__name__)

CURRENCIES = TableSpec("Currencies", (
    Column("gross_posted", numpy.float64, "everything ever posted in the currency, for the conservation check", "currency units"),
    Column("gross_seen", numpy.uint8, "flag: something has been posted in the currency", "0 or 1"),
    Column("supply_at_start", numpy.float64, "the money supply (edge accounts excluded) when the year began", "currency units"),
    Column("supply_seen", numpy.uint8, "flag: supply_at_start has been noted", "0 or 1"),
))
Currencies = CURRENCIES.make_type(__name__)

GOODS = TableSpec("Goods", (
    Column("gross_moved", numpy.float64, "everything ever moved of the good, for the conservation check", "good units"),
    Column("gross_seen", numpy.uint8, "flag: something has been moved of the good", "0 or 1"),
))
Goods = GOODS.make_type(__name__)

STOCKS = TableSpec("Stocks", (
    Column("key", numpy.int64, "agent, good and tile packed by pack_key; what the hash index searches", "packed key"),
    Column("agent", numpy.int64, "the holder", "agent id", ids="agents"),
    Column("good", numpy.int64, "the good held", "good id", ids="goods"),
    Column("tile", numpy.int64, "where it is held", "tile id", ids="tiles"),
    Column("quantity", numpy.float64, "how much is held (negative only for an edge account)", "good units"),
    Column("next_in_agent", numpy.int64, "the holder's next slot in the order they were made, or -1", "stock slot"),
    Column("live", numpy.uint8, "flag: 0 once a rename merged the slot into another", "0 or 1"),
))
Stocks = STOCKS.make_type(__name__)

PURPOSE_FLOWS = TableSpec("PurposeFlows", (
    Column("key", numpy.int64, "good, purpose template and purpose reference packed by pack_key", "packed key"),
    Column("good", numpy.int64, "the good moved", "good id", ids="goods"),
    Column("purpose_code", numpy.int64, "the purpose's template", "purpose id", ids="purposes"),
    Column("purpose_reference", numpy.int64, "what the template names (a good, a trade, a tax); 0 is the empty text",
           "reference id", ids="references"),
    Column("quantity", numpy.float64, "this year's quantity moved for the purpose", "good units"),
    Column("live", numpy.uint8, "flag: always 1 (the column the hash index rebuilds by)", "0 or 1"),
))
PurposeFlows = PURPOSE_FLOWS.make_type(__name__)

EDGE_GOODS = TableSpec("EdgeGoods", (
    Column("key", numpy.int64, "edge agent and good packed by pack_key", "packed key"),
    Column("agent", numpy.int64, "the edge account", "agent id", ids="agents"),
    Column("good", numpy.int64, "the good", "good id", ids="goods"),
    Column("volume", numpy.float64, "this year's gross goods in and out through the edge", "good units"),
    Column("net", numpy.float64, "this year's goods the edge gave to the economy less what it took", "good units"),
    Column("live", numpy.uint8, "flag: always 1 (the column the hash index rebuilds by)", "0 or 1"),
))
EdgeGoods = EDGE_GOODS.make_type(__name__)

TRANSFER_POSTINGS = TableSpec("TransferPostings", (
    Column("payer", numpy.int64, "who pays", "agent id", ids="agents"),
    Column("payee", numpy.int64, "who is paid", "agent id", ids="agents"),
    Column("currency", numpy.int64, "the currency paid", "currency id", ids="currencies"),
    Column("amount", numpy.float64, "how much is paid; never negative (reverse payer and payee instead)", "currency units"),
    Column("purpose_code", numpy.int64, "why: the purpose's template", "purpose id", ids="purposes"),
    Column("purpose_reference", numpy.int64, "why: what the template names", "reference id", ids="references"),
    Column("batch", numpy.int64, "the all-or-none batch the posting belongs to; rows of one batch are together, batches rising",
           "batch number"),
))
TransferPostings = TRANSFER_POSTINGS.make_type(__name__)

GOODS_MOVE_POSTINGS = TableSpec("GoodsMovePostings", (
    Column("giver", numpy.int64, "who gives", "agent id", ids="agents"),
    Column("receiver", numpy.int64, "who receives", "agent id", ids="agents"),
    Column("good", numpy.int64, "the good moved", "good id", ids="goods"),
    Column("tile", numpy.int64, "where the giver holds it", "tile id", ids="tiles"),
    Column("receiver_tile", numpy.int64, "where the receiver takes delivery (the same as tile for a plain move)", "tile id",
           ids="tiles"),
    Column("quantity", numpy.float64, "how much is moved; never negative", "good units"),
    Column("purpose_code", numpy.int64, "why: the purpose's template", "purpose id", ids="purposes"),
    Column("purpose_reference", numpy.int64, "why: what the template names", "reference id", ids="references"),
    Column("batch", numpy.int64, "the all-or-none batch the posting belongs to; rows of one batch are together, batches rising",
           "batch number"),
))
GoodsMovePostings = GOODS_MOVE_POSTINGS.make_type(__name__)

BATCH_OUTCOMES = TableSpec("BatchOutcomes", (
    Column("code", numpy.int64, "0 when the batch was applied, else the cause code in BOOK_CAUSES", "cause code"),
    Column("culprit", numpy.int64, "the first posting row (negative amount or quantity) or touched cell (an overdraft) behind the cause; "
           "-1 when applied. A money cell is agent * stride + currency; a stock cell is a packed key.", "row or cell"),
))
BatchOutcomes = BATCH_OUTCOMES.make_type(__name__)

PLANS = TableSpec("Plans", (
    Column("key", numpy.int64, "the cell touched: a balance row, or a packed stock key", "cell"),
    Column("holder", numpy.int64, "the agent whose cell it is", "agent id", ids="agents"),
    Column("slot", numpy.int64, "a stock cell's existing slot, or -1 when the batch would make it", "stock slot"),
    Column("before", numpy.float64, "what the cell held before the batch", "units"),
    Column("after", numpy.float64, "what it would hold after the batch", "units"),
    Column("moved", numpy.float64, "gross amount through the cell in the batch (the rounding tolerance is a share of it)", "units"),
    Column("failing", numpy.uint8, "flag: the batch would overdraw the cell", "0 or 1"),
    Column("position", numpy.int64, "where the cell sits in the batch's own hash index (cleared when the batch ends)", "index"),
))
Plans = PLANS.make_type(__name__)

# What a kernel returns when a batch is refused (code 0 is applied). The boundary turns a code into the book's own errors.
BOOK_CAUSES = Causes(("negative_amount", "negative_quantity", "insufficient_funds", "insufficient_goods", "table_full"))
NEGATIVE_AMOUNT = BOOK_CAUSES.code("negative_amount")
NEGATIVE_QUANTITY = BOOK_CAUSES.code("negative_quantity")
INSUFFICIENT_FUNDS = BOOK_CAUSES.code("insufficient_funds")
INSUFFICIENT_GOODS = BOOK_CAUSES.code("insufficient_goods")
TABLE_FULL = BOOK_CAUSES.code("table_full")

# What a posting kernel reads and writes besides the postings, in two halves so a batch of only money (or only goods) passes
# only its half to the kernel: dispatching a kernel costs a little for every array it is given.
MoneyTables = collections.namedtuple("MoneyTables", ("agents", "balances", "stride", "currencies"), module=__name__)
GoodsTables = collections.namedtuple("GoodsTables", (
    "agents", "goods", "stocks", "stock_index", "flows", "flow_index", "edge_goods", "edge_index"), module=__name__)
BookTables = collections.namedtuple("BookTables", ("money", "goods"), module=__name__)

# The scratch of one apply call: a plan and a hash index over it for money cells, and likewise for stock cells.
Scratch = collections.namedtuple("Scratch", ("money_plan", "money_local", "goods_plan", "goods_local"), module=__name__)

FREE = -1      # first_slot, last_slot, next_in_agent and a plan's slot when there is none
