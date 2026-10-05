"""Complaint 425: a hire the market fills only in part reports the people found, not the people asked for."""
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.labour.labour_market_api import LabourMarket

ASKED, FOUND = 5, 2

game = sim(capital=5_000_000.0)
headcount_before = game.employees.get("artisan", 0.0)
with mock.patch.object(LabourMarket, "whole_recruits", return_value=FOUND):
    reply = S._agent_dispatch(game, NODES, {"cmd": "hire", "trade": "artisan", "n": ASKED})
check("the partial hire went through", reply.get("ok") is True, reply)
check("the headcount rose by the people found", game.employees["artisan"] - headcount_before == FOUND,
      (headcount_before, game.employees.get("artisan")))
check("the reply names the people found, not the people asked for", reply.get("n") == FOUND, reply)
check("the reply still says what was asked", reply.get("asked") == ASKED, reply)

# The staff audit: each automatic hire row names the people the staff gained.
auto = sim(capital=2_000_000.0, manual=False)
auto.end_year = auto.cfg["start_year"] + auto.cfg["horizon_years"]
gained = []
real_hire = type(auto.labour).hire


def counting_hire(self, trade, count, *args, **kwargs):
    before = auto.employees.get(trade, 0.0)
    result = real_hire(self, trade, count, *args, **kwargs)
    if result[0]:
        gained.append("%d %s" % (round(auto.employees.get(trade, 0.0) - before), trade))
    return result


def one_person_found(self, trade, people, pay_premium=0.0):
    return min(int(people), 1) if people > 0 else 0


rows = []
with mock.patch.object(LabourMarket, "whole_recruits", one_person_found), \
        mock.patch.object(type(auto.labour), "hire", counting_hire):
    for _ in range(6):
        S._agent_dispatch(auto, NODES, {"cmd": "step", "years": 1})
        rows += [row for row in S._agent_dispatch(auto, NODES, {"cmd": "automation"})["rows"]
                 if row["action"] == "hire"]
check("automation hired through the capped market", rows and gained, (len(rows), len(gained)))
check("every automatic hire row names the people gained, not the people sought",
      sorted(row["what"] for row in rows) == sorted(gained),
      (sorted(row["what"] for row in rows)[:4], sorted(gained)[:4]))
