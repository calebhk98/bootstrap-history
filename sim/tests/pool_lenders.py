"""A stand-in for the economy's lenders behind the actors' pool, for tests of `Purses`: accounts that hold the economy's unit in the
book, offered at an ask, as the listing of the last lending gives them. Additive helper; the tests that use it say what they set."""
from typing import Dict, Tuple

from sim.agents.purses import EDGE_OUTSIDE
from sim.book import Transfer

UNIT = "unit"


def lend_through(purses, lenders: Dict[str, Tuple[float, float]], coin_per_unit: float = 2.0, unit: str = UNIT) -> None:
    """Give each lender `balance` units in the purses' book and let the pool borrow from them: `lenders` maps account ->
    (units on offer, ask). The listing is read live from the book, cheapest ask first, as the economy's is."""
    for lender, (offered, _ask) in lenders.items():
        purses.book.transfer(Transfer(EDGE_OUTSIDE, lender, unit, offered, "seed"))

    def lenders_for(_account: str, _amount: float):
        rows = [(lender, offered, purses.book.balance(lender, unit), ask) for lender, (offered, ask) in lenders.items()]
        return unit, coin_per_unit, sorted(rows, key=lambda row: (row[3], row[0]))
    purses.lenders_for = lenders_for


def value(purses, coin_per_unit: float = 2.0, unit: str = UNIT) -> float:
    """Every holding of the actors' coin and the economy's unit in the book, in coin, edges included: what the exchange conserves."""
    book = purses.book
    return sum(book.balance(agent, "engine_coin") + coin_per_unit * book.balance(agent, unit) for agent in book.agents())


SAVERS = "cohort:savers"   # one economy lender standing in for the households' savings, at one coin to the unit


def lend_from_savers(purses, coin: float) -> None:
    """The pool can borrow `coin` from one lender that asks the same rate whatever is drawn."""
    lend_through(purses, {SAVERS: (coin, 0.05)}, coin_per_unit=1.0)
