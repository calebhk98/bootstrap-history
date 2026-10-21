"""Scenarios for the staffing warning in a whole game: the household's numbers reach `staffing_closure_warnings` (the rows are
`staffing_warning_rows`, tested in test_staffing_warnings), the state screen prints the headline, and no command's
readable view crashes on a rich household with a warning live (a TypeError once swallowed the whole annual report)."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

_s_sw = unopened_sim(civ="rome_100ad")
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
_s_sw.artisans = _sw_art_used - 0.6   # room under 1.0: one loss closes it
_sw_warn3 = _s_sw.staffing_closure_warnings()
check("no slack at all: the game's own household feeds the warning and the state screen prints its headline",
      bool(_sw_warn3) and _sw_warn3[0]["one_loss_closes_it"] and _sw_warn3[0]["id"] in _s_sw.operating
      and _sw_warn3[0]["name"] in _RSTATE(S._agent_dispatch(_s_sw, NODES, {"cmd": "state"})), _sw_warn3)

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
_rr_started_keys = []
for _k in ORDER:
    if _rr_started >= 6:
        break
    if _s_rr.start_reason(_k)[0]:
        _s_rr.start_project(_k)
        _rr_started_keys.append(_k)
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
# stepping needs an opened economy: rebuild the same household on one
_s_rr_open = run_it(sim(civ="rome_100ad"), *_s_rr.operating)
_s_rr_open.artisans, _s_rr_open.scholars = _s_rr.artisans, _s_rr.scholars
_s_rr_open.capital, _s_rr_open.end_year = _s_rr.capital, _s_rr.end_year
for _k in _rr_started_keys:
    if _s_rr_open.start_reason(_k)[0]:
        _s_rr_open.start_project(_k)
_rr_step = _PROTO.render_pretty("step", S._agent_dispatch(_s_rr_open, NODES,
                                                          {"cmd": "step", "years": 1}))
check("...including `step`, the other command the report named",
      "could not render a readable view" not in (_rr_step or ""), _rr_step[:200])
