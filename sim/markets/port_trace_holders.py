"""Money held by kind of agent, read from an economy's book: the columns the spin-up traces add to each year's row.

The kind of an account is the part of its id before the first colon (`household:town:2` is a household). Edge
accounts are left out, since they are where money enters and leaves the model; any other kind is `other`, so the
columns add up to the money stock.
"""
from sim.book import is_edge

HOLDER_COLUMNS = ("money_households", "money_producers", "money_merchants", "money_state", "money_banks", "money_other")

_COLUMN_OF_PREFIX = {"household": "money_households", "producer": "money_producers", "merchant": "money_merchants",
                     "state": "money_state", "bank": "money_banks"}


def holder_kind(agent_id):
    """The column a book account's money goes to, from its prefix (`money_other` for a prefix none names)."""
    return _COLUMN_OF_PREFIX.get(agent_id.split(":", 1)[0], "money_other")


def money_by_holder_columns(book, currency):
    """{money_households, money_producers, money_merchants, money_state, money_banks, money_other} for `currency`: the
    balance of every non-edge account in `book`, summed by holder_kind."""
    columns = {column: 0.0 for column in HOLDER_COLUMNS}
    for agent_id in book.agents():
        if not is_edge(agent_id):
            columns[holder_kind(agent_id)] += book.balance(agent_id, currency)
    return columns
