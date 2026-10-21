"""Scenario for Complaint 13 in a whole game: a plate-mirror concern is opened only with a glassblower, the ventures
screen exposes the specialist commitment, and a concern closes when its required specialist foreman is lost. The rules
are in test_complaint_13_specialist_supervision."""
from .harness import *
from sim.refusal import cause_of, facts_of


def prepared(node_id):
    sim_state = sim(capital=1_000_000)
    sim_state.done.add(node_id)
    sim_state.artisans = 20.0
    return sim_state


s = prepared("mirror_amalgam")
ok_without, why = s.open_venture("mirror_amalgam", pay=False)
s.employees["glassblower"] = 1
ok_with, why_with = s.open_venture("mirror_amalgam", pay=False)
ventures = S._agent_dispatch(s, NODES, {"cmd": "ventures"})
mirror_row = next(row for row in ventures["running"] if row["id"] == "mirror_amalgam")

SPIRITS = "distillation_alcohol"
d = prepared(SPIRITS)
trade, fte = d.venture_foreman(SPIRITS)
d.employees[trade] = 1
d.operating.add(SPIRITS)
d.employees[trade] = 0
closed = d.close_unstaffed_ventures(d.year)

check("scenario: a mirror concern needs a glassblower to open, the ventures reply exposes his share, and losing a specialist closes a concern",
      not ok_without and cause_of(why) == "foreman_missing" and facts_of(why)["trade"] == "glassblower"
      and ok_with and mirror_row["specialist_foreman"] == {"trade": "glassblower", "fte": 0.25}
      and (trade, fte) == ("smith", 0.25) and SPIRITS in closed,
      dict(without=why, with_=why_with, row=mirror_row, foreman=(trade, fte), closed=closed))
