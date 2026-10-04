"""Complaints 88 and 98: portfolio paging, readouts and group drill-down; stuck on a calendar-bound goal path."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.ui.proto import stuck_advice
from sim.ui.proto.parse_portfolio import _parse_portfolio
from sim.ui.proto.portfolio_scale import add_readouts, page_rows
from sim.ui.proto.render_portfolio_rows import paging_line, project_lines
from sim.ui.proto.render_screens_economy import render_portfolio
from sim.ui.proto.render_screens_status import render_stuck


def row(node_id, kind, rank, left=100.0, hours=400.0, effective=100.0, years=1.0):
    return {"id": node_id, "name": node_id, "constraint": "staffing" if kind == "specialists" else "calendar",
            "blocker_kind": kind, "pool_rank_this_year": rank, "still_to_pay": left,
            "founder_hours_left": hours, "hours_effective_this_year": effective,
            "calendar_years_left": years}


rows = [row("p%d" % i, "calendar" if i % 2 else "specialists", i) for i in range(1, 21)]
shown, paging, error = page_rows(rows, [], {})
check("default page is capped and most severe kind first",
      len(shown) == 8 and all(r["blocker_kind"] == "specialists" for r in shown) and paging["more"] == 12, paging)
check("paging names the exact next commands", paging["next_command"] == "portfolio offset:8"
      and paging["all_command"] == "portfolio all", paging)
check("'all' shows every row", len(page_rows(rows, [], {"all": True})[0]) == 20)
drill, drill_paging, _ = page_rows(rows, [], {"group": "calendar", "limit": 3})
check("group drill-down shows only that blocker's projects",
      len(drill) == 3 and drill_paging["total"] == 10 and drill_paging["next_command"] == "portfolio calendar offset:3",
      drill_paging)
check("a group can be a trade", page_rows(rows, [{"trade": "scribe", "projects_drawing_on_it": ["p1", "p2"]}],
                                          {"group": "scribe"})[1]["total"] == 2)
check("unknown group names the choices", "specialists" in (page_rows(rows, [], {"group": "zzz"})[2] or ""))
check("typed line parses group and offset",
      _parse_portfolio("portfolio", ["calendar", "offset:4"], [], [], False)[0]
      == {"cmd": "portfolio", "json": False, "group": "calendar", "offset": 4})

nodes = {"p1": {"yrs": 4}}
readout = add_readouts(SimpleNamespace(year=1000), nodes, [row("p1", "hours", 1, left=800.0, hours=400.0,
                                                               effective=100.0, years=2.0)])[0]
check("absorption is money left over the project's years", readout["annual_absorption"] == 200.0, readout)
check("earliest completion is the slowest of calendar, hours and money",
      readout["earliest_completion_year"] == 1004, readout)
stalled = add_readouts(SimpleNamespace(year=1000), nodes, [row("p1", "hours", 1, effective=0.0)])[0]
check("no effective hours means no finish forecast", stalled["earliest_completion_year"] is None, stalled)

text = "\n".join(project_lines(dict(readout, waiting_on="x", hours_offered_this_year=50.0)))
check("allocation and forecast are labelled apart", "last allocation" in text and "forecast from now" in text, text)
check("paging line points at the next page", "and 12 more" in paging_line(paging), paging_line(paging))
check("render_portfolio shows the pointer", "portfolio offset:8" in render_portfolio(
    {"projects": shown, "paging": paging, "active_project_count": 20}))

# stuck: fog degrades to counts; clear sight names the goal path
real_kinds, real_levers = stuck_advice.delay_kinds, stuck_advice.lever_line
stuck_advice.delay_kinds = lambda test_sim, graph: {"calendar": ["secret_a", "secret_b"]}
stuck_advice.lever_line = lambda test_sim: "literacy: 1"
try:
    fogged = stuck_advice.calendar_bound_advice(SimpleNamespace(fog=True), {})
    check("fog reports counts, names nothing", "all 2 running" in fogged["text"] and "secret" not in str(fogged), fogged)
    graph = {"goal": {"pre": ["secret_a"]}, "secret_a": {"pre": []}, "secret_b": {"pre": []}}
    clear = SimpleNamespace(fog=False, goal="goal", done=set(), active={"secret_a": {}, "secret_b": {}},
                            start_reason=lambda node_id: (False, ""))
    advice = stuck_advice.calendar_bound_advice(clear, graph)
    check("calendar-bound goal path is said and side work suggested",
          advice and advice["every_goal_project_calendar_bound"] and len(advice["side_work"]) == 3, advice)
    clear.start_reason = lambda node_id: (node_id == "goal", "")
    check("a startable road node means it is not calendar-bound",
          stuck_advice.calendar_bound_advice(clear, graph) is None)
finally:
    stuck_advice.delay_kinds, stuck_advice.lever_line = real_kinds, real_levers
stuck_text = render_stuck({"what_is_holding_you_up": "x", "goal_path_is_calendar_bound": advice,
                           "the_cheapest_start_is_filler": "a is only the cheapest startable thing"})
check("stuck renders the wait, side work and filler",
      "CALENDAR" in stuck_text and "coverage" in stuck_text and "only the cheapest" in stuck_text, stuck_text)

live = sim()
reply = S._agent_dispatch(live, NODES, {"cmd": "stuck"})
check("stuck on a real game carries live lever figures and the filler note",
      reply.get("lever_figures") and "filler" in str(reply.get("the_cheapest_start_is_filler")), reply)
check("portfolio on a real game replies with paging", S._agent_dispatch(live, NODES, {"cmd": "portfolio"})["paging"]["total"] == 0)
