"""Scenario for Complaint 273 in a whole game: a step charges the household's purse for keeping its coin under guard, as
its own cause in the cash ledger, and the money and state screens report the hoard's mass. The rules (the mass, the
keeping cost) are in test_coin_hoard_mass."""
from .harness import *  # noqa: F401,F403

from sim.engine import cash_book

CAUSE = "keeping coin under guard"

game = sim(capital=1.0e6, manual=False, events=False)
owed = []
hoard = game.coin_hoard


def watched():
    report = hoard()
    owed.append(report["keeping_cost_per_year"])
    return report


game.coin_hoard = watched
game.step()
paid = -cash_book.causes_since(game, None).get(CAUSE, 0.0)
check("scenario: a step charges the household what the hoard owed, under its own cause in the cash ledger",
      paid > 0.0 and any(abs(paid - amount) <= 1e-9 * max(1.0, amount) for amount in owed), (paid, owed))

replies, _stdout, _code = proto([{"cmd": "money"}, {"cmd": "state"}], civ="han_china_100ad")
money_reply, state_reply = replies[-2], replies[-1]
opening = sim(civ="han_china_100ad").coin_hoard_report()
check("scenario: the money and state screens report the hoard's mass",
      money_reply.get("coin_hoard", {}).get("tonnes") == opening["tonnes"]
      and state_reply.get("coin_hoard", {}).get("tonnes") == opening["tonnes"],
      (money_reply.get("coin_hoard"), state_reply.get("coin_hoard")))
