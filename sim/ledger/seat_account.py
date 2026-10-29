"""A seat's money as the ledger moves it: the seat's account in the actors' book and its cash book.

`SeatAccount` is the seat's own purse. Money in or out through it moves the account's net position against the
account outside the book and is entered in the cash book under its cause. `SeatActor` is the seat as a party in
the book: a payment between it and another party is one posting between their accounts, entered in the cash book
beside it. Both are made by the ledger for the length of a command and never handed out.
"""
from typing import Any

from . import cash_book

SET_LABEL = "set"   # the label of a posting that brings an account to a figure, the other side being outside the book


class SeatAccount:
    """The purse of the seat `account`, with the cash book `cash` (a `LedgerSeat`) that records its movements."""

    # the seat's own purse stands at the home country's centre when coin is carried; a party in the book has no place of its own
    stands_at_home = True

    def __init__(self, cash: Any, purses: Any, account: str) -> None:
        self.cash, self.book, self.account = cash, purses, account

    @property
    def capital(self) -> float:
        return float(self.book.net(self.account))

    @capital.setter
    def capital(self, value: float) -> None:
        self.book.set_net(self.account, float(value), SET_LABEL)

    def note_income(self, purpose: Any, amount: float) -> None:
        """Money that came in by a posting in the book, entered in the cash book under its cause."""
        cash_book.record(self.cash, 1.0, float(amount), purpose)

    def note_outlay(self, purpose: Any, amount: float) -> None:
        """Money that went out by a posting in the book, entered in the cash book under its cause."""
        cash_book.record(self.cash, -1.0, float(amount), purpose)

    def credit(self, amount: float, purpose: Any) -> None:
        """Money in, entered in the cash book under its cause."""
        self.capital += float(amount)
        cash_book.record(self.cash, 1.0, float(amount), purpose)

    def debit(self, amount: float, purpose: Any) -> None:
        """Money out, entered in the cash book under its cause."""
        self.capital -= float(amount)
        cash_book.record(self.cash, -1.0, float(amount), purpose)


class SeatActor(SeatAccount):
    """The seat as a party in the actors' book: `ledger.transfer` posts between its account and the other party's."""

    stands_at_home = False

    @property
    def purses(self) -> Any:
        return self.book

    @property
    def account_id(self) -> str:
        return self.account

    @property
    def actor_id(self) -> str:
        return self.account

    @property
    def money(self) -> float:
        return self.capital

    @money.setter
    def money(self, value: float) -> None:
        self.capital = value
