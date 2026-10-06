"""A project underfunded by arrears says so: in the log and on `why`, `stuck` and `portfolio`."""
from .harness import *  # noqa: F401,F403

s_arrears = s = sim(capital=1000.0)
_af_k = next(node_id for node_id in NODES
     if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n = NODES[_af_k]
s.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0, spent=0.0,
                      cost_left=s.project_cost(_af_k), lab_left=dict(_af_n["lab"]))
_lim_af = s.credit_limit()
_fixed_af = s.living_cost() + s.upkeep() + s.mine_operating_cost()
_reserve_af = max(0.0, _fixed_af - s.revenue())
# Deep enough that the project's own purse (capital + 0.6*limit - reserve)
# is negative, but still inside credit_limit so enforce_credit_limit does
# not wipe `active` out from under this check.
s.capital = -(_reserve_af + 0.6 * _lim_af) - 50.0
_before_log = len(s.log)
s.step()
check("set-up: the project really is underfunded by arrears this year",
      s.active.get(_af_k, {}).get("underfunded_this_year") is True,
      s.active.get(_af_k, {}).get("why_underfunded"))
_new_lines = [message for _, message in s.log[_before_log:]]
check("the year it happens, the log SAYS founder-hours were wasted to "
      "arrears, by name - not only on a project screen a player has to "
      "think to check",
      any("founder-hours meant for" in message and _af_k in message
          for message in _new_lines),
      _new_lines)
check("...and it is recognisable as bad news by the same marker every "
      "other arrears line already uses ('log failures' finds it)",
      any(_PROTO._is_failure_line(message) for message in _new_lines
          if "founder-hours meant for" in message),
      _new_lines)

# --- and a project that is merely calendar-waiting, fully paid, gets no
# such line: only real, costed hour-loss is reported, never every year a
# household happens to be in arrears.
s = sim(capital=1000.0)
_af_k2 = next(node_id for node_id in NODES
     if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n2 = NODES[_af_k2]
s.active[_af_k2] = dict(ph_left=float(_af_n2["ph"]), yrs=0.0,
                        spent=s.project_cost(_af_k2), cost_left=0.0,
                        lab_left=dict(_af_n2["lab"]))
s.capital = -(s.living_cost() + s.upkeep() + s.mine_operating_cost()
              + 0.6 * s.credit_limit()) - 50.0
_before_log2 = len(s.log)
s.step()
check("a fully-paid project waiting only on the calendar never triggers "
      "the wasted-hours line - there is nothing left for arrears to waste",
      not any("founder-hours meant for" in message
              for _, message in s.log[_before_log2:]),
      [message for _, message in s.log[_before_log2:]])

# --- THE BUG AS FILED: `why`/`stuck` named only "waiting on your hours" while the
# true cause - arrears - sat unread. Same game and year as above.
s = s_arrears
_arb_k = _af_k
_arb_pool_check = S._agent_dispatch(s, NODES, {"cmd": "portfolio"})
check("set-up: founder-hours are plentiful and idle, exactly the player's "
      "report - the shortfall is not staffing or founder time",
      (_arb_pool_check.get("founder_hours_available_this_year") or 0) > 1000,
      _arb_pool_check.get("founder_hours_available_this_year"))
check("set-up: the project is really underfunded by arrears, not by "
      "trade or the calendar",
      s.active.get(_arb_k, {}).get("underfunded_this_year") is True,
      s.active.get(_arb_k, {}).get("why_underfunded"))

_arb_why = S._agent_dispatch(s, NODES, {"cmd": "why", "id": _arb_k})
check("BUG AS FILED: `why` on the stalled project still names only "
      "'your hours' - the misleading half a player actually reads",
      str(_arb_why.get("waiting_on")).startswith("your hours"), _arb_why.get("waiting_on"))
check("THE FIX: `why`'s JSON reply also now carries why_underfunded, the "
      "real cause, not just the misleading waiting_on string",
      bool(_arb_why.get("why_underfunded"))
      and "arrears" in _arb_why["why_underfunded"], _arb_why.get("why_underfunded"))
_arb_why_txt = _RWHY(_arb_why)
check("...and the rendered `why` screen prints it too, so a human reading "
      "the terminal - not just an agent reading JSON - sees the real cause",
      "arrears" in _arb_why_txt, _arb_why_txt)

_arb_stuck = S._agent_dispatch(s, NODES, {"cmd": "stuck"})
_arb_stuck_reason = next(
    (reason for reason in _arb_stuck.get("what_is_holding_you_up", [])
     if reason.get("what") == "work in hand"), {})
check("`stuck`'s JSON reply names the arrears cause against the specific "
      "project it afflicts, not only in the separate whole-household "
      "ARREARS block that does not say which project is affected",
      _arb_k in (_arb_stuck_reason.get("each_why_underfunded") or {})
      and "arrears" in _arb_stuck_reason["each_why_underfunded"][_arb_k],
      _arb_stuck_reason.get("each_why_underfunded"))
_arb_stuck_txt = _PROTO.render_stuck(_arb_stuck)
check("...and the rendered `stuck` screen - the one the player in the bug "
      "report actually read - carries more than the bare 'waiting on your "
      "hours' line for this project",
      "waiting on your hours" in _arb_stuck_txt and "arrears" in _arb_stuck_txt,
      _arb_stuck_txt)

_arb_port = S._agent_dispatch(s, NODES, {"cmd": "portfolio"})
_arb_port_row = next((row for row in _arb_port.get("projects", [])
                      if row["id"] == _arb_k), {})
check("`portfolio`'s JSON reply carries why_underfunded per row too, "
      "the third of the three screens a player actually reads",
      bool(_arb_port_row.get("why_underfunded"))
      and "arrears" in _arb_port_row["why_underfunded"], _arb_port_row)
_arb_port_txt = _RPORT(_arb_port)
check("...and the rendered `portfolio` screen prints it under the same "
      "row's 'waiting on' line",
      "arrears" in _arb_port_txt, _arb_port_txt)

