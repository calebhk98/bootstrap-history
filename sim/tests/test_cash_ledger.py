"""Complaint 292: every change to the founder's cash goes through the household's ledger with a
cause (Complaint 95). The rules are tested on a household built here; the whole-game scenarios are in
test_cash_ledger_scenario."""
QUICK_TOPIC = True

import os
import re
import types

from .harness import *  # noqa: F401,F403

from sim.engine import cash_book
from sim.engine.state import HouseholdState

from .source_dirs import SIM_DIR, engine_side_dirs

# The only places allowed to write the purse itself: the ledger's own methods and the opening balance.
PURSE_WRITERS = {os.path.join("engine", "state.py"), os.path.join("engine", "core_properties.py"),
                 os.path.join("agents", "household.py"),
                 os.path.join("engine", "opening_money.py")}   # reprices the opening purses to the economy's money per hour: a unit change, not a transfer
DIRECT_WRITE = re.compile(r"\.capital\s*[-+*/]?=(?!=)")

# --- no code path writes the purse around the ledger -------------------------------------------
offenders = []
for folder, _dirs, files in (entry for directory in engine_side_dirs() for entry in os.walk(directory)):
    for name in files:
        path = os.path.join(folder, name)
        relative = os.path.relpath(path, SIM_DIR)
        if not name.endswith(".py") or relative in PURSE_WRITERS:
            continue
        with open(path, encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                if DIRECT_WRITE.search(line.split("#", 1)[0]):
                    offenders.append("%s:%d" % (relative, number))
check("no engine code changes the founder's cash except through the ledger", not offenders, offenders)


# --- the household's postings keep the book reconciled -----------------------------------------
def household_game(capital=1000.0, year=100):
    household = HouseholdState(capital=capital)
    return types.SimpleNamespace(state=types.SimpleNamespace(household=household), year=year)


def reconciles(game):
    return abs(cash_book.unaccounted(game)) < 1e-9


game = household_game()
household = game.state.household
household.credit(50.0, "venture revenue")
household.debit(20.0, "living costs")
household.debit(5.0, "living costs")
check("credit and debit enter the cause with its sign", household.cash_flow == {"venture revenue": 50.0, "living costs": -25.0},
      household.cash_flow)
check("a book of credits and debits reconciles", reconciles(game), cash_book.unaccounted(game))

household.debit(10.0, {"running costs": 12.0, "sales": -2.0})
check("one payment can carry several causes, each with its own signed part",
      household.cash_flow["running costs"] == -12.0 and household.cash_flow["sales"] == 2.0, household.cash_flow)

household.reset_cash(600.0, "settlement")
check("a settlement enters the difference under its cause and reconciles",
      reconciles(game) and household.capital == 600.0 and household.cash_flow["settlement"] < 0.0, household.cash_flow)

household.note_income("sales", 7.0)
household.note_outlay("sales", 3.0)
check("income and outlay posted in the book alone count in the cash book under their cause",
      household.cash_flow["sales"] == 2.0 + 7.0 - 3.0, household.cash_flow)

closing_cash = household.capital
cash_book.close_period(game)
check("closing a period starts the next from today's cash with no entries",
      cash_book.opening(household) == closing_cash and household.cash_flow == {}, household.cash_flow)
check("...and the closed period keeps its opening, closing and causes",
      household.cash_periods[-1]["closing"] == closing_cash and household.cash_periods[-1]["causes"].get("venture revenue") == 50.0,
      household.cash_periods)

household.capital += 9.0   # a write around the ledger, the fault the book exists to expose
check("a write around the ledger shows as unaccounted cash", abs(cash_book.unaccounted(game) - 9.0) < 1e-9,
      cash_book.unaccounted(game))

for year in range(101, 101 + 3 * cash_book.PERIODS_KEPT):
    cash_book.close_period(types.SimpleNamespace(state=game.state, year=year))
check("the ledger keeps only the last few closed periods", len(household.cash_periods) == cash_book.PERIODS_KEPT,
      len(household.cash_periods))

game = household_game()
game.state.household.credit(10.0, "a")
cash_book.close_period(types.SimpleNamespace(state=game.state, year=101))
game.state.household.credit(5.0, "a")
game.state.household.debit(2.0, "b")
check("causes since a year add the closed periods after it to the open one",
      cash_book.causes_since(game, 100) == {"a": 15.0, "b": -2.0} and cash_book.causes_since(game, 101) == {"a": 5.0, "b": -2.0},
      (cash_book.causes_since(game, 100), cash_book.causes_since(game, 101)))
book = cash_book.book(game)
check("the book shows opening plus causes equal to closing",
      abs(book["opening"] + sum(book["causes"].values()) - book["closing"]) < 0.1, book)
