"""Small screen items, Complaints 93, 86 and 97: the funding capacity the `money` screen quotes is the sum of the three parts it
shows apart (`funding_capacity` over `funding_breakdown`); `why` names the node that brings a living stock only to a player who may
see that node (`rows_for_player`); and the full state screen prints its blocks in the order situation, goal, risks, work, staff,
standing, from a reply built here (presentation: the order of the state screen's blocks). Each is called on values written here."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.tests import finance_host
from sim.ui.proto.render_screen_state import render_state
from sim.ui.proto.stock_gate_rows import rows_for_player

BREAKDOWN = {"cash_on_hand": 400.0, "credit_available_now": 250.0, "surplus_allowance_over_years": 1000.0,
             "sustainable_annual_surplus": 200.0, "already_committed": 900.0}
stand_in = finance_host.build()
stand_in.funding_breakdown = lambda: dict(BREAKDOWN)
check("the funding capacity is cash, the credit available now and the surplus allowance, and not the surplus or the commitments",
      stand_in.funding_capacity() == 1650.0)

GATES = [{"material": "eggs", "needed": 0.02, "held": 0.0, "brought_by": None},
         {"material": "herd", "needed": 5.0, "held": 0.0, "brought_by": "import_herd"},
         {"material": "seed", "needed": 1.0, "held": 0.0, "brought_by": "hidden_node"}]
shown = rows_for_player(GATES, lambda node_id: node_id != "hidden_node")
check("a gate brought by a node the player can see keeps its node", shown[1]["brought_by"] == "import_herd", shown)
check("a gate brought by a node the player cannot see names no node, and keeps its figures",
      shown[2] == {"material": "seed", "needed": 1.0, "held": 0.0, "brought_by": None}, shown)
check("a gate brought by nothing is unchanged and asks nothing of visibility",
      rows_for_player(GATES[:1], lambda node_id: 1 / 0) == GATES[:1])
check("the rows are copies: the gates handed in are not changed", GATES[2]["brought_by"] == "hidden_node")

reply = {"state_view": "full", "goal": "Transistor", "founder_alive": True, "founder_ages": False, "capital": 100.0, "year": 100,
         "at_risk": {"technologies_you_could_lose": 3, "hedged_by": "a copy", "hazards_still_ahead": 1, "in_full": "see risk"}}
lines = render_state(reply).splitlines()


def first_line_starting(prefix):
    return next((position for position, line in enumerate(lines) if line.startswith(prefix)), None)


order = [first_line_starting(prefix) for prefix in ("Money:", "You:", "Goal:", "AHEAD:", "RUNNING", "EMPLOY:", "STANDING:")]
# presentation: the order of the state screen's blocks
check("the full state shows money, hours, goal, looming risks, work, staff, then standing", None not in order and order == sorted(order), order)
