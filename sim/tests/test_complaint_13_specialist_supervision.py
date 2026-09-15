"""Regression coverage for Complaint 13: specialist venture supervision."""
from .harness import *
from engine.proto.render import render_pretty


def prepared(node_id):
    s = sim(capital=1_000_000)
    s.done.add(node_id)
    s.artisans = 20.0
    return s


# Plate mirrors have substantial glassblower work. Generic artisans can supply
# general oversight, but cannot replace that specialist foreman.
s = prepared("mirror_amalgam")
ok, why = s.open_venture("mirror_amalgam", pay=False)
check("generic artisans alone cannot supervise an advanced mirror concern",
      not ok and "glassblower" in why and "Generic artisans cannot substitute" in why,
      why)

s.employees["smith"] = 1
ok, why = s.open_venture("mirror_amalgam", pay=False)
check("an unrelated specialist cannot supervise plate-mirror work",
      not ok and "glassblower" in why, why)

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
s = prepared("fud_distillation_spirits")
s.employees["chemist"] = 1
for node_id in ("fud_distillation_spirits",):
    s.operating.add(node_id)
trade, fte = s.venture_foreman("fud_distillation_spirits")
check("distillation retains its chemist as an operating foreman",
      trade == "chemist" and fte == 0.25, (trade, fte))

# Losing the skilled supervisor closes the concern just as losing its generic
# keeper does; the requirement is ongoing, not merely an opening toll.
s.employees["chemist"] = 0
closed = s.close_unstaffed_ventures(s.year)
check("a concern closes when its required specialist foreman is lost",
      "fud_distillation_spirits" in closed, closed)
