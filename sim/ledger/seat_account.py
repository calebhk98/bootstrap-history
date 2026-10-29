"""A seat's money as the ledger moves it: the seat's account in the actors' book and its cash book.

`SeatAccount` is the seat as a party in the book: a payment between it and another party is one posting between their
accounts (`ledger.transfer`), entered in the cash book beside it. It is made by the ledger for the length of a command and
never handed out.
"""
from typing import Any

from . import cash_book

SET_LABEL = "set"   # the label of a posting that brings an account to a figure, the other side being outside the book


class SeatAccount:
    """The purse of the seat `account` in the actors' book, with the cash book `cash` (a `LedgerSeat`) that records its movements."""

    # the seat's purse stands at the home country's centre when coin is carried, whichever command moves it
    stands_at_home = True

    def __init__(self, cash: Any, purses: Any, account: str) -> None:
        self.cash, self.book, self.account = cash, purses, account

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
    def capital(self) -> float:
        return float(self.book.net(self.account))

    @capital.setter
    def capital(self, value: float) -> None:
        self.book.set_net(self.account, float(value), SET_LABEL)

    @property
    def money(self) -> float:
        return self.capital

    @money.setter
    def money(self, value: float) -> None:
        self.capital = value

    def note_income(self, purpose: Any, amount: float) -> None:
        """Money that came in by a posting in the book, entered in the cash book under its cause."""
        cash_book.record(self.cash, 1.0, float(amount), purpose)

    def note_outlay(self, purpose: Any, amount: float) -> None:
        """Money that went out by a posting in the book, entered in the cash book under its cause."""
        cash_book.record(self.cash, -1.0, float(amount), purpose)

    def credit(self, amount: float, purpose: Any) -> None:
        """Money in with no counterparty in the book (`CreditSeat`: the sender posts the other side), entered under its cause."""
        self.capital += float(amount)
        self.note_income(purpose, amount)

    def debit(self, amount: float, purpose: Any) -> None:
        """Money out with no counterparty in the book (`DebitSeat`), entered under its cause."""
        self.capital -= float(amount)
        self.note_outlay(purpose, amount)
