"""Regression coverage for Complaint 13: specialist venture supervision."""
from .harness import *
from sim.refusal import cause_of, facts_of
from sim.ui.proto.render import render_pretty


def prepared(node_id):
    sim_state = sim(capital=1_000_000)
    sim_state.done.add(node_id)
    sim_state.artisans = 20.0
    return sim_state


# Plate mirrors have substantial glassblower work. Generic artisans can supply
# general oversight, but cannot replace that specialist foreman.
s = prepared("mirror_amalgam")
ok, why = s.open_venture("mirror_amalgam", pay=False)
check("generic artisans alone cannot supervise an advanced mirror concern",
      not ok and cause_of(why) == "foreman_missing" and facts_of(why)["trade"] == "glassblower",
      why)

s.employees["smith"] = 1
ok, why = s.open_venture("mirror_amalgam", pay=False)
check("an unrelated specialist cannot supervise plate-mirror work",
      not ok and cause_of(why) == "foreman_missing" and facts_of(why)["trade"] == "glassblower", why)

s.employees["glassblower"] = 1
ok, why = s.open_venture("mirror_amalgam", pay=False)
check("a glassblower foreman can supervise plate-mirror work", ok, why)
ventures = S._agent_dispatch(s, NODES, {"cmd": "ventures"})
mirror_row = next(row for row in ventures["running"]
                  if row["id"] == "mirror_amalgam")
check("ventures exposes the specialist supervision commitment",
      mirror_row["specialist_foreman"]
      == {"trade": "glassblower", "fte": 0.25}, mirror_row)
check("the rendered ventures screen names the specialist foreman",
      "specialist foreman: 0.25 glassblower FTE"
      in render_pretty("ventures", ventures), render_pretty("ventures", ventures))

# One specialist has a bounded span of control: four quarter-FTE concerns, not
# an unlimited industrial portfolio.
SPIRITS = "distillation_alcohol"
s = prepared(SPIRITS)
trade, fte = s.venture_foreman(SPIRITS)
s.employees[trade] = 1
s.operating.add(SPIRITS)
check("distillation retains its specialist as an operating foreman",
      trade == "smith" and fte == 0.25, (trade, fte))

# Losing the skilled supervisor closes the concern just as losing its generic
# keeper does; the requirement is ongoing, not merely an opening toll.
s.employees[trade] = 0
closed = s.close_unstaffed_ventures(s.year)
check("a concern closes when its required specialist foreman is lost",
      SPIRITS in closed, closed)
