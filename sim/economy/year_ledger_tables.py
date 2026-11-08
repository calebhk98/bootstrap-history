"""The year ledger's tables: what each column holds, and the namedtuple types the kernels take.

The ledger is rebuilt every year and not saved. It keeps what happened to each agent and market this year, in tables keyed by
the numbers the rest of the game already uses: agents, goods and tiles by the book (`book.agent_number`, `good_number`),
purposes by the book's purpose templates and references, goods markets, labour markets and trades by the market memory
(`memory.tables`). The ledger makes no numbering of its own.

Tables, by the thing a row is:
    AgentFigures   one row per agent number      seven money/hour/run figures and three "nested" figures (for each: whether the
                                                 agent has it this year, its place in entry order, and the head and tail of its rows)
    PairRows       one row per (agent, subkey)   one table of this shape for each of received, grown, sold, output, hours_hired,
                                                 hours_hired_by_market, imports_paid, exports_received
    MarketFigures  one row per goods market      delivered and unmet quantity
    ClearingRounds one row per cleared round     which market, how much, at what price

Entry order: a dict shows its keys in the order they were first added, and the close sums in that order, so a figure that
must keep it has an `order_*` column (1, 2, 3, ... in the order of first addition; 0 = not a member) and the ledger keeps a
counter of the next number and a count of members per figure (`counters`, two entries per figure: next number, members).
A chain link, head or tail holds a row number plus one, so the zero a fresh table holds means "none".

Rows `0 .. row_count - 1` are in use (see sim/compiled_tables/spec.py)."""
import collections

import numpy

from sim.compiled_tables.spec import Column, TableSpec

# The agent figures that are plain numbers, in counter order.
MONEY_OUT, WAGES_IN, SALES_IN, PLANT_SPEND, PLANT_WORN, HOURS_SOLD, SPARE_HOURS = range(7)
# The agent figures that own rows of a pair table (the agent "has" the figure once it has an entry, even an empty one).
RECEIVED, GROWN, HOURS_HIRED = range(7, 10)
FIGURE_COUNT = 10
# What a settlement row's purpose was: wages for labour, a sale of goods, or anything else (rent, dues).
OTHER_PURPOSE, WAGES_PURPOSE, SALES_PURPOSE = 0, 1, 2
# The kinds of pending notes (`year_ledger_batch.py`), and which kind each figure and pair table waits on (None: none does).
SETTLEMENTS, HOURS, ROUNDS, OUTPUT = range(4)
FIGURE_KIND = {MONEY_OUT: SETTLEMENTS, WAGES_IN: SETTLEMENTS, SALES_IN: SETTLEMENTS, PLANT_SPEND: SETTLEMENTS, PLANT_WORN: None,
               HOURS_SOLD: HOURS, SPARE_HOURS: None}
PAIR_KIND = {"received": SETTLEMENTS, "sold": SETTLEMENTS, "imports_paid": SETTLEMENTS, "exports_received": SETTLEMENTS,
             "hours_hired": HOURS, "hours_hired_by_market": HOURS, "output": OUTPUT, "grown": None}
# Counter layout: counters[2 * figure] is the next entry number, counters[2 * figure + 1] the number of members.
NEXT_ENTRY, MEMBERS = 0, 1

_VECTOR_MEANINGS = (
    ("money_out", "money the agent paid out this year (everything it paid, plant included)", "currency units"),
    ("wages_in", "wages the agent was paid this year", "currency units"),
    ("sales_in", "money the agent received for goods it sold this year", "currency units"),
    ("plant_spend", "money the agent paid for goods its own plant is built from (a build, not a running cost)", "currency units"),
    ("plant_worn", "runs of capacity that wore out this year", "runs"),
    ("hours_sold", "hours of work the agent sold and was paid for this year", "hours"),
    ("spare_hours", "hours a household had left once its own plot took what the land it holds could", "hours"),
)
_NESTED_MEANINGS = (
    ("received", "goods the agent received this year, by good"),
    ("grown", "goods the agent made for itself this year, by good"),
    ("hours_hired", "hours the agent hired this year, by trade"),
)


def _agent_columns():
    columns = []
    for name, meaning, unit in _VECTOR_MEANINGS:
        columns.append(Column(name, numpy.float64, meaning, unit))
        columns.append(Column("order_" + name, numpy.int64, "place of the agent in the order agents entered `%s`; 0: not there" % name,
                              "entry number"))
    for name, meaning in _NESTED_MEANINGS:
        columns.append(Column("order_" + name, numpy.int64, "place of the agent in the order agents entered `%s`; 0: not there" % name,
                              "entry number"))
        columns.append(Column("first_" + name, numpy.int64, "the agent's first row in the %s pair table, plus one; 0: none" % name,
                              "row + 1"))
        columns.append(Column("last_" + name, numpy.int64, "the agent's newest row in the %s pair table, plus one; 0: none" % name,
                              "row + 1"))
    return tuple(columns)


AGENT_FIGURES = TableSpec("AgentFigures", _agent_columns())
AgentFigures = AGENT_FIGURES.make_type(__name__)

PAIR_ROWS = TableSpec("PairRows", (
    Column("key", numpy.int64, "agent, subkey and extra packed by pack_key; what the hash index searches (-1 once the row is dead)",
           "packed key"),
    Column("agent", numpy.int64, "the agent the figure is about", "agent id", ids="agents"),
    Column("subkey", numpy.int64, "what the figure is about: a good, a trade, a labour market, or a purpose template", "good, trade, "
           "labour market or purpose id"),
    Column("extra", numpy.int64, "a second part of the subkey: a purpose reference for the foreign-money figures, else 0",
           "reference id", ids="references"),
    Column("amount", numpy.float64, "the figure: goods, hours or money, summed in the order they were added", "units of the figure"),
    Column("second_amount", numpy.float64, "a second figure (money paid, for hours_hired_by_market); 0 for the other tables",
           "currency units"),
    Column("next_in_agent", numpy.int64, "the agent's next row in this table in the order they were made, plus one; 0: none",
           "row + 1"),
    Column("live", numpy.uint8, "flag: 0 once the row was replaced or removed (the column the hash index rebuilds by)", "0 or 1"),
))
PairRows = PAIR_ROWS.make_type(__name__)

MARKET_FIGURES = TableSpec("MarketFigures", (
    Column("delivered", numpy.float64, "goods the market's settlements moved this year", "good units"),
    Column("order_delivered", numpy.int64, "place of the market in the order markets entered `delivered`; 0: not there", "entry number"),
    Column("unmet", numpy.float64, "quantity wanted in the market that nobody supplied this year", "good units"),
    Column("order_unmet", numpy.int64, "place of the market in the order markets entered `unmet`; 0: not there", "entry number"),
))
MarketFigures = MARKET_FIGURES.make_type(__name__)
DELIVERED, UNMET = 0, 1
MARKET_FIGURE_COUNT = 2

CLEARING_ROUNDS = TableSpec("ClearingRounds", (
    Column("market", numpy.int64, "the goods market the round cleared (a number in the market memory's goods markets)", "goods market id",
           ids="goods_markets"),
    Column("quantity", numpy.float64, "the quantity the round matched", "good units"),
    Column("price", numpy.float64, "the price the round was worked from; NaN: the round had none", "currency units per unit"),
))
ClearingRounds = CLEARING_ROUNDS.make_type(__name__)

# What a pair-table kernel needs besides the rows: the hash index, and for a table whose agents own rows the agent figure's columns.
PairTarget = collections.namedtuple("PairTarget", ("rows", "hash_index", "firsts", "lasts", "orders", "counters", "figure", "chained"),
                                    module=__name__)
