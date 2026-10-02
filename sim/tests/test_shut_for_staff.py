"""shut_for_staff: regression checks, run individually with `--only shut_for_staff`."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_screens_big import _state_concerns

# Complaint 87: state names the missing specialist behind each shut concern.

_concern = "camera_obscura"   # needs a carpenter foreman to run
foreman_trade, foreman_share = None, 0.0

test_sim = sim(capital=1e6)
foreman_trade, foreman_share = test_sim.venture_foreman(_concern)
test_sim.done.add(_concern)
test_sim._done_changed()
test_sim.state.household.artisans = 50.0
test_sim.state.household.scholars = 50.0

state_out = S._agent_state(test_sim, NODES)
rows = state_out.get("shut_for_want_of_staff") or []
row = next((entry for entry in rows if entry.get("id") == _concern), {})
check("state lists a shut, profitable concern held shut by a missing foreman, with the trade and FTE",
      row.get("missing") == {foreman_trade: foreman_share}, rows)
check("...and says what to type to fix it",
      "hire %s" % foreman_trade in (row.get("fix") or ""), row)

text = "\n".join(_state_concerns(state_out))
check("the rendered state names the concern and what it lacks",
      NODES[_concern]["name"] in text and "missing %s %s" % ("0.25", foreman_trade) in text, text)

test_sim.state.household.employees[foreman_trade] = 1.0
rows = S._agent_state(test_sim, NODES).get("shut_for_want_of_staff") or []
check("once the specialist is on the payroll the concern is no longer listed as short of staff",
      bool(row) and not any(entry.get("id") == _concern for entry in rows), rows)
