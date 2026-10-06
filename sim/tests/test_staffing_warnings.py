"""staffing_warnings: regression checks, run individually with `--only staffing_warnings`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

# --- a warning before the door shuts (projects.py: staffing_closure_warnings)
# close_unstaffed_ventures closes a concern the household can no longer
# supervise; reopen_restaffed_ventures (landed separately) already brings it
# back once restaffed. What was still missing: seeing it coming. "Power grid
# supervision is within 5 craftsmen of closure" - a warning, not a third
# automation; nothing here hires, teaches or stops anything on its own.
_s_sw = sim(civ="rome_100ad")
_sw_cands = [node_id for node_id in NODES if NODES[node_id].get("rev", 0) > 0][:30]
_s_sw.done.update(_sw_cands)
_s_sw._done_changed()
_s_sw.artisans, _s_sw.scholars = 40.0, 10.0
for _k in _sw_cands:
    _s_sw.open_venture(_k)
check("comfortably staffed: no staffing warning at all",
      _s_sw.staffing_closure_warnings() == [], _s_sw.staffing_closure_warnings())
_sw_sch_used, _sw_art_used = _s_sw.venture_staff_used()
_s_sw.artisans = _sw_art_used + 3.0   # inside STAFFING_WARNING_BAND (5)
_sw_warn = _s_sw.staffing_closure_warnings()
check("within the band: a warning names a real operating concern and how "
      "many craftsmen stand between here and its closure",
      bool(_sw_warn) and _sw_warn[0]["id"] in _s_sw.operating
      and _sw_warn[0]["of"] == "craftsmen" and _sw_warn[0]["within"] > 0
      and "spare" in _sw_warn[0]["headline"]
      and "closes" in _sw_warn[0]["headline"], _sw_warn)
check("the concern it names is the same one close_unstaffed_ventures would "
      "actually close first (dearest to keep, for what it ties up)",
      _sw_warn and _sw_warn[0]["id"] == sorted(
          [node_id for node_id in _s_sw.operating if _s_sw.venture_hands(node_id)[1] > 0.005
           or _s_sw.venture_hands(node_id)[0] > 0.005],
          key=lambda node_id: ((NODES[node_id]["rev"] - NODES[node_id]["up"])
                         / max(0.01, _s_sw.venture_hands(node_id)[1]),
                         -_s_sw.venture_hands(node_id)[1]))[0],
      _sw_warn)
_sw_before = set(_s_sw.operating)
_s_sw.artisans = _sw_art_used - 2.0    # room exhausted
_sw_warn2 = _s_sw.staffing_closure_warnings()
check("room exhausted: the warning says so plainly rather than quoting a "
      "negative number of craftsmen",
      bool(_sw_warn2) and "next in line to close" in _sw_warn2[0]["headline"],
      _sw_warn2)
check("this is a warning, not a cure: calling it changes nothing about "
      "who is still operating - only close_unstaffed_ventures itself does "
      "the closing, on its own schedule, unchanged by this",
      set(_s_sw.operating) == _sw_before, sorted(_s_sw.operating))

# --- BREAK: an England player hired more staff, watched this warning's own
# number climb 1.3 to 2.3, and read the RISE as the situation getting WORSE
# before working out that bigger means safer - "the 'X is within N
# craftsmen of closure' warning is ambiguous on first read". The fix is the
# wording, not the arithmetic: "spare" reads as safer the more of it there
# is, the same as the no-slack sibling just above ("has no spare craftsmen:
# losing just one more closes it outright"), and never says "within" at all
# any more, which read like a countdown.
_s_sw2 = _s_sw
_sw2_art_used = _sw_art_used
_s_sw2.artisans = _sw2_art_used + 1.3
_sw_before_hire = _s_sw2.staffing_closure_warnings()
_room_before = _sw_before_hire[0]["within"] if _sw_before_hire else None
_s_sw2.artisans += 1.0   # hire one more craftsman
_sw_after_hire = _s_sw2.staffing_closure_warnings()
_room_after = _sw_after_hire[0]["within"] if _sw_after_hire else None
check("hiring more staff moves the reported room UP, same as the England "
      "run (1.3 -> 2.3)",
      _room_before is not None and _room_after is not None
      and _room_after > _room_before,
      (_room_before, _room_after))
# --- the missing case: a concern with NO slack at all, where losing one
# more person of its trade closes it outright - not just "within N of
# closure" but the recurring income at stake and the command that fixes it.
_s_sw.artisans = _sw_art_used - 0.6   # room under 1.0: one loss closes it
_sw_warn3 = _s_sw.staffing_closure_warnings()
check("no slack at all: the warning says losing just one more closes it, "
      "not merely that it is 'within' some number",
      bool(_sw_warn3) and _sw_warn3[0]["one_loss_closes_it"]
      and "losing just one more closes it" in _sw_warn3[0]["headline"],
      _sw_warn3)
check("...and names what that closure would actually cost in recurring "
      "income, not just that it would happen",
      _sw_warn3 and _sw_warn3[0]["recurring_income_at_risk"] > 0
      and "den/yr" in _sw_warn3[0]["headline"], _sw_warn3)
check("...and names the command that fixes it - a real {\"cmd\":\"hire\"} "
      "example with a real trade, not just the generic 'craftsmen'/"
      "'scholars' word",
      _sw_warn3 and '"cmd":"hire"' in _sw_warn3[0]["fix"]
      and _sw_warn3[0]["fix"] in _sw_warn3[0]["headline"], _sw_warn3)
check("within the band but NOT down to the last one: one_loss_closes_it is "
      "false, and the headline stays the earlier 'N spare' sentence",
      _sw_warn and _sw_warn[0]["one_loss_closes_it"] is False
      and "spare" in _sw_warn[0]["headline"], _sw_warn)
check("room already exhausted (<=0.05): also costed and fixed, same as the "
      "one-loss-away case",
      _sw_warn2 and _sw_warn2[0]["recurring_income_at_risk"] > 0
      and '"cmd":"hire"' in _sw_warn2[0]["fix"], _sw_warn2)
# render_state used to crash the instant any staffing warning fired at all -
# "can only concatenate str (not 'dict') to str" - because
# staffing_closure_warnings() returns dicts and the renderer assumed bare
# strings. Nothing caught this because the regression suite only ever called
# the engine method directly, never through the human-text renderer.
_sw_state_out = S._agent_dispatch(_s_sw, NODES, {"cmd": "state"})
check("render_state no longer crashes when a staffing warning is live, and "
      "prints the actual headline sentence",
      _sw_warn3[0]["name"] in _RSTATE(_sw_state_out), _sw_state_out.get("supervision_close_to_the_edge"))

# NO RENDERER MAY CRASH ON A RICH GAME. A player agent reported the readable
# view of `state` and `step 1` vanishing entirely, replaced by "(could not
# render a readable view of this reply: TypeError: can only concatenate str
# (not \"dict\") to str)", once it had several projects running and several
# concerns open. That was render_state appending staffing-warning DICTS as
# bare strings, and it is fixed - but the class is the point: render_pretty
# catches everything on purpose, so a formatter bug costs the formatting and
# never the session, which is exactly why one can sit there unnoticed. The
# suite had only ever called the engine methods directly, never the
# renderers, which is how it survived. So: build a household rich enough to
# populate every optional section, then render every op in the table.
# THE STATE HAS TO ACTUALLY CARRY THE OPTIONAL SECTIONS, or this proves
# nothing. A first version of this check built a busy household, rendered
# everything, passed - and went on passing with the original bug put back,
# because a busy household is not by itself a household whose concerns are
# one artisan from closing, so render_state never reached the line that
# crashed. Mutation-tested since: with the dict appended bare again, the
# `state` entry below reports the apology and this check fails.
_s_rr = _s_sw   # already holds many open concerns
_s_rr.capital = 400000.0
_s_rr.end_year = _s_rr.cfg["start_year"] + _s_rr.cfg["horizon_years"]
_rr_started = 0
for _k in ORDER:
    if _rr_started >= 6:
        break
    if _s_rr.start_reason(_k)[0]:
        _s_rr.start_project(_k)
        _rr_started += 1
# one craftsman from closing something, which is the state that broke it
_rr_sch_used, _rr_art_used = _s_rr.venture_staff_used()
_s_rr.artisans = _rr_art_used - 0.6
assert _s_rr.staffing_closure_warnings(), \
    "the renderer sweep needs a live staffing warning or it proves nothing"

_rr_cmds = {"state": {"cmd": "state"}, "step": None, "labour": {"cmd": "labour"},
            "money": {"cmd": "money"}, "risk": {"cmd": "risk"},
            "ventures": {"cmd": "ventures"}, "mines": {"cmd": "mines"},
            "stuck": {"cmd": "stuck"}, "log": {"cmd": "log"},
            "values": {"cmd": "values"}, "policy": {"cmd": "policy"},
            "capacity": {"cmd": "capacity"}, "portfolio": {"cmd": "portfolio"},
            "economy": {"cmd": "economy"}, "changes": {"cmd": "changes"},
            "available": {"cmd": "available"}, "score": {"cmd": "score"}}
_rr_broken = []
for _op, _payload in sorted(_rr_cmds.items()):
    if _payload is None:
        continue
    try:
        _resp = S._agent_dispatch(_s_rr, NODES, _payload)
    except Exception as _e:
        _rr_broken.append((_op, "dispatch raised %s: %s" % (type(_e).__name__, _e)))
        continue
    _txt = _PROTO.render_pretty(_op, _resp)
    if "could not render a readable view" in (_txt or ""):
        _rr_broken.append((_op, _txt[:160]))
check("every command's readable view renders on a household with projects "
      "running, concerns open and staffing short - the state a player agent "
      "was in when the whole annual report vanished behind a TypeError",
      not _rr_broken, _rr_broken)

# AND THE ONE THAT ACTUALLY BROKE, through the renderer rather than the engine
# method, on a state where the warning is live.
_rr_state = S._agent_dispatch(_s_rr, NODES, {"cmd": "state"})
_rr_step = _PROTO.render_pretty("step", S._agent_dispatch(_s_rr, NODES,
                                                          {"cmd": "step", "years": 1}))
check("...including `step`, the other command the report named",
      "could not render a readable view" not in (_rr_step or ""), _rr_step[:200])
