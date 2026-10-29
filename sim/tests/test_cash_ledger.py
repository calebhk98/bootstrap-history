"""Complaint 292: every change to the founder's cash goes through the ledger with a cause (Complaint 95). The rules are tested
on a seat's purse built here; a write around the ledger shows as unaccounted cash."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.ledger import cash_book
from sim.ledger.api import CloseCashPeriod, CreditSeat, DebitSeat, NoteSeatCash
from sim.tests.money_host import MoneyHost

SEAT = "founder"


def unaccounted(host):
    return host.view("cash_unaccounted")()


# --- the seat's postings keep the book reconciled -----------------------------------------
host = MoneyHost(capital=1000.0)
cash = host.ledger.seat
host.send(CreditSeat(SEAT, 50.0, "venture revenue"))
host.send(DebitSeat(SEAT, 20.0, "living costs"))
host.send(DebitSeat(SEAT, 5.0, "living costs"))
check("credit and debit enter the cause with its sign", cash.cash_flow == {"venture revenue": 50.0, "living costs": -25.0}, cash.cash_flow)
check("a book of credits and debits reconciles", abs(unaccounted(host)) < 1e-9, unaccounted(host))

host.send(DebitSeat(SEAT, 10.0, {"running costs": 12.0, "sales": -2.0}))
check("one payment can carry several causes, each with its own signed part",
      cash.cash_flow["running costs"] == -12.0 and cash.cash_flow["sales"] == 2.0, cash.cash_flow)

host.send(NoteSeatCash(SEAT, 1.0, 7.0, "sales"))
host.send(NoteSeatCash(SEAT, -1.0, 3.0, "sales"))
check("income and outlay posted in the book alone count in the cash book under their cause",
      cash.cash_flow["sales"] == 2.0 + 7.0 - 3.0, cash.cash_flow)

closing_cash = host.view("acting_balance")()
host.send(CloseCashPeriod())
check("closing a period starts the next from today's cash with no entries",
      cash_book.opening(cash, closing_cash) == closing_cash and cash.cash_flow == {}, cash.cash_flow)
check("...and the closed period keeps its opening, closing and causes",
      cash.cash_periods[-1]["closing"] == closing_cash and cash.cash_periods[-1]["causes"].get("venture revenue") == 50.0,
      cash.cash_periods)

host.purses.set_net(SEAT, closing_cash + 9.0, "stray")   # a write around the ledger, the fault the book exists to expose
check("a write around the ledger shows as unaccounted cash", abs(unaccounted(host) - 9.0) < 1e-9, unaccounted(host))

for year in range(101, 101 + 3 * cash_book.PERIODS_KEPT):
    host.year = year
    host.send(CloseCashPeriod())
check("the ledger keeps only the last few closed periods", len(cash.cash_periods) == cash_book.PERIODS_KEPT, len(cash.cash_periods))

host = MoneyHost(capital=1000.0, year=100)
host.send(CreditSeat(SEAT, 10.0, "a"))
host.send(CloseCashPeriod())
host.year = 101
host.send(CreditSeat(SEAT, 5.0, "a"))
host.send(DebitSeat(SEAT, 2.0, "b"))
check("causes since a year add the closed periods after it to the open one",
      host.view("cash_causes_since")(99) == {"a": 15.0, "b": -2.0} and host.view("cash_causes_since")(100) == {"a": 5.0, "b": -2.0},
      (host.view("cash_causes_since")(99), host.view("cash_causes_since")(100)))
book = host.view("cash_book")()
check("the book shows opening plus causes equal to closing",
      abs(book["opening"] + sum(book["causes"].values()) - book["closing"]) < 0.1, book)


# --- the cash figure reads its causes from the ledger: explain_figure on a written-out year
from sim.ui import figures as figure_registry
from sim.ui import figures_headline  # noqa: F401  (registers the cash figure)
from sim.tests.ui_stand_in import Game

this_year = {"venture revenue": 500.0, "living costs": -200.0}
this_year_game = Game(year=101, view=lambda name: {"acting_balance": lambda: 1300.0, "cash_causes_since": lambda year: dict(this_year)}[name])
last_year = [{"year": 100, "figures": {"cash": {"value": 1000.0, "components": {}, "flows": {}, "drivers": {}}}}]
explained = figure_registry.explain_figure(this_year_game, "cash", last_year)
check("the cash figure's change is this year's movement of the purse", explained["change"] == 300.0, explained)
check("...its causes come from the ledger and add up to the change with nothing not itemised",
      {cause["cause"]: cause["contribution"] for cause in explained["causes"]} == {"venture revenue": 500.0, "living costs": -200.0},
      explained["causes"])
