"""`cashbook`: opening cash, each cause and closing cash for the last closed years and the open one,
read from the cash book (the `money` screen shows only the open year's causes)."""
from sim.engine.ui_port import cash_book
from .command_registry import command

CLOSED_YEARS_SHOWN = 3
RECONCILE_TOLERANCE = 1.0   # the book rounds each part to a tenth


def _year_row(year, opening, closing, causes, open_year):
    gap = round(closing - opening - sum(causes.values()), 1)
    return {"year": year, "open_year": open_year, "opening": opening, "closing": closing,
            "causes": [{"cause": cause, "amount": amount}
                       for cause, amount in sorted(causes.items(), key=lambda item: (-abs(item[1]), item[0]))],
            "not_itemised": gap if abs(gap) > RECONCILE_TOLERANCE else 0.0}


def cash_ledger(sim):
    book = cash_book.book(sim)
    closed = book["earlier_years"][-CLOSED_YEARS_SHOWN:]
    rows = [_year_row(row["year"], row["opening"], row["closing"], row["causes"], False) for row in closed]
    rows.append(_year_row(book["year"], book["opening"], book["closing"], book["causes"], True))
    return {"ok": True, "years": rows,
            "note": "each year: opening cash, the causes, closing cash; 'money' shows the rest of the ledger"}


@command("cashbook", shape="bare", group="money", aliases=("cashflow", "cashyears"),
         summary="cash year by year: opening, causes, closing",
         usage=["cashbook"], options={},
         description="Opening cash, every cause line and closing cash for the last few closed years "
                     "and the open one, so the cash reconciles; a leftover the book cannot name is "
                     "shown as its own line.")
def _cmd_cashbook(sim, nodes, cmd, ended):
    return cash_ledger(sim)
