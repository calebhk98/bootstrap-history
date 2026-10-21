"""Scenarios in a whole game: `start` reports the whole bill split into materials paid now and instalments owed, and the
total is what `why` quoted (Complaint 500); `why`, `quote open`, `ventures` and `open` agree on a concern's running cost
and label staffing (Complaint 501). The figures are built by `cost_if_started_now` and `upkeep_quote`, called on numbers in
test_quote_figures_rules; here the screens are checked to show what the engine quotes."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_screens_start import render_start


def _ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# --- 500: the parts of the start reply sum to the total `why` quoted ---------
start_sim = sim(capital=1e7)
total_quoted = start_sim.project_cost_now("horse_collar")
capital_before = start_sim.capital
reply = _ask(start_sim, cmd="start", id="horse_collar")
materials_paid = reply.get("of_which_materials_paid_now", -1)
instalments = reply.get("of_which_instalments_still_owed", -1)
check("start spends the materials money now, its parts sum to its total, and the total is the cost quoted before starting",
      reply.get("ok") and materials_paid > 0 and abs((capital_before - start_sim.capital) - materials_paid) < 0.2
      and abs(materials_paid + instalments - reply["the_bill_you_have_taken_on"]) < 0.2
      and abs(reply["the_bill_you_have_taken_on"] - total_quoted) < 0.2, (reply, capital_before, start_sim.capital, total_quoted))
# presentation: the text screen names both parts
check("start's text screen names both parts",
      "materials paid now" in render_start(reply).lower().replace("_", " ")
      and "instalments still owed" in render_start(reply).lower().replace("_", " "), render_start(reply))

# --- 501: one running cost, labelled, on every screen -----------------------
upkeep_sim = sim(capital=1e7)
concern_id = next(node_id for node_id in ORDER
                  if upkeep_sim.is_venture(node_id) and node_id in upkeep_sim.CAPABILITY_INSTITUTIONS
                  and node_id not in upkeep_sim.done and NODES[node_id]["up"] > 0)
upkeep_sim.done.add(concern_id)
upkeep_sim._done_changed()
why_reply = _ask(upkeep_sim, cmd="why", id=concern_id)
quote = _ask(upkeep_sim, cmd="quote", what="open", id=concern_id)
listing = _ask(upkeep_sim, cmd="ventures", limit=500)
row = next(row for rows in listing.values() if isinstance(rows, list)
           for row in rows if isinstance(row, dict) and row.get("id") == concern_id)
now_cost = upkeep_sim.venture_upkeep_quote(concern_id)["now"]
full_cost = upkeep_sim.venture_upkeep_quote(concern_id)["at_full_staffing"]
check("why, quote open and ventures show the running cost now, and at full staffing, as the engine quotes it",
      all(abs(shown - expected) < 0.2 for shown, expected in (
          (why_reply["upkeep"], now_cost), (why_reply["upkeep_at_full_staffing"], full_cost),
          (quote["costs_a_year_to_run"], now_cost), (quote["costs_a_year_at_full_staffing"], full_cost),
          (row["costs_a_year"], now_cost), (row["costs_a_year_at_full_staffing"], full_cost))),
      (why_reply, quote, row, now_cost, full_cost))
check("the test concern is understaffed, so full staffing costs more than today", full_cost > now_cost, (now_cost, full_cost))
open_reply = _ask(upkeep_sim, cmd="open", id=concern_id)
# presentation: the open message names the opening charge and today's cost
check("the open message names the opening charge and today's running cost",
      open_reply.get("ok") and "opening charge" in open_reply["opened"]
      and "{:,.0f}".format(open_reply["opening_charge"]) in open_reply["opened"]
      and "{:,.0f}".format(now_cost) in open_reply["opened"], (now_cost, open_reply))
