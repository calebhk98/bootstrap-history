"""A bank founded by an actor whose money the engine keeps (a seat): the capital arrives from outside the book."""
from typing import Optional

from . import banks
from .types import Transfer


def found_from_outside(record, money: str, founder: str, capital: float, year: int, edge: str) -> Optional[banks.Bank]:
    """`capital` comes in over `edge` to the founder's account and goes into a new bank at once; None when it is not positive."""
    if capital <= 0.0:
        return None
    record.book.transfer(Transfer(edge, founder, money, capital, "bank capital"))
    return banks.found(record, founder, capital, year, money)
