"""Small screen items: Complaints/92 (hazard hedge timing), 93 (four funding concepts),
86 (knowledge apart from held living stock), 97 (opening state hierarchy)."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.render_screens_big import render_state, render_why
from sim.engine.proto.render_screens_economy import render_money
from sim.engine.proto.render_screens_status import render_risk

# --- 92: every hedge with a calendar floor says whether it finishes before the window opens
england = sim(civ="england_1300", capital=1e6)
risk = S._agent_dispatch(england, NODES, {"cmd": "risk"})
timed = []
for hazard in risk["knowledge_risk"]["known_hazards_ahead"]:
    for advice in (hazard.get("what_you_can_do") or {}).values():
        for step in advice.get("you_could_begin_now_toward_it") or []:
            if step.get("years_even_if_you_start_today") is not None:
                timed.append((hazard, step))
check("hedges with a calendar floor exist to be timed", bool(timed), None)
check("every such hedge carries its earliest finish year and the window's opening year",
      all((step.get("timing") or {}).get("earliest_finish_year") is not None
          and step["timing"]["window_opens_year"] == hazard["years"][0] for hazard, step in timed),
      [step.get("timing") for _hazard, step in timed][:2])
check("the earliest finish is the calendar floor counted from the year now",
      all(step["timing"]["earliest_finish_year"]
          == england.year + int(-(-step["years_even_if_you_start_today"] // 1)) for _hazard, step in timed), None)
check("in time means finishing in a year before the window opens, and some hedges are not",
      all(step["timing"]["in_time_if_started_today"]
          == (step["timing"]["earliest_finish_year"] < hazard["years"][0]) for hazard, step in timed)
      and {step["timing"]["in_time_if_started_today"] for _hazard, step in timed} == {True, False},
      [(step["id"], step["timing"]["in_time_if_started_today"]) for _hazard, step in timed])
check("the risk screen prints the timing beside the hedge",
      "window opens" in render_risk(risk), render_risk(risk)[:400])

# --- 93: money names cash, credit, surplus and what is owed apart; the sum is the engine's capacity
funded = sim(civ="rome_100ad", capital=1e5)
money = S._agent_dispatch(funded, NODES, {"cmd": "money"})
funding = money.get("funding") or {}
check("money carries the four funding figures apart",
      {"cash_on_hand", "credit_available_now", "surplus_allowance_over_years",
       "sustainable_annual_surplus", "already_committed"} <= set(funding), sorted(funding))
check("the capacity shown is cash plus credit plus the surplus allowance",
      abs(funding.get("cash_on_hand", 0) + funding.get("credit_available_now", 0)
          + funding.get("surplus_allowance_over_years", 0) - funded.funding_capacity()) < 0.2
      and abs(money["you_could_actually_fund_up_to"] - funded.funding_capacity()) < 0.2, funding)
check("the already-committed figure is the engine's committed spend",
      abs(funding.get("already_committed", -1) - funded.committed_spend()) < 0.2, funding)
shown = render_money(money)
check("the money screen prints cash, credit, surplus and commitments on separate lines",
      all(any(line.strip().startswith(label) for line in shown.splitlines())
          for label in ("CASH ON HAND", "CREDIT AVAILABLE", "ANNUAL SURPLUS", "ALREADY COMMITTED")),
      shown[-900:])
