"""Complaint 273: the yearly cost of keeping the household's coin under guard is charged to its purse and
shows in the cash ledger as its own cause, in proportion to the coin held."""
from .harness import *  # noqa: F401,F403

from sim.engine import cash_book

CAUSE = "keeping coin under guard"


def stepped(capital):
    """(money the ledger charged for keeping coin in one step, what the hoard owed each time it was asked)."""
    game = sim(capital=capital, manual=False, events=False)
    owed = []
    hoard = game.coin_hoard

    def watched():
        report = hoard()
        owed.append(report["keeping_cost_per_year"])
        return report
    game.coin_hoard = watched
    game.step()
    return -cash_book.causes_since(game, None).get(CAUSE, 0.0), owed


poor_paid, poor_owed = stepped(1.0e3)
rich_paid, rich_owed = stepped(1.0e6)
check("the cash ledger names the cost of keeping coin", rich_paid > 0.0, rich_paid)
check("the charge is what the hoard owed when the year's money was struck",
      any(abs(rich_paid - amount) <= 1e-9 * max(1.0, amount) for amount in rich_owed), (rich_paid, rich_owed))
check("a larger hoard is charged more", rich_paid > poor_paid > 0.0, (poor_paid, rich_paid))

debt_paid, _debt_owed = stepped(-1.0e4)
check("a purse in debt holds no coin and is charged nothing for it", debt_paid == 0.0, debt_paid)
