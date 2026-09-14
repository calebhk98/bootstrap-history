"""parallelism_note: split verbatim from the old test_regressions.py (original lines 8787-8854).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# PARALLELISM IS THE CENTRAL MECHANIC AND NOTHING TAUGHT IT. An external
# blind playthrough treated a long calendar-floor project as exclusive
# research time for most of its early game, only discovering that spare
# founder-hours and staff could run other projects in the background after
# an outside hint - which their own write-up calls probably the difference
# between finishing comfortably and risking the 600 AD horizon. Two fixes:
# a one-time note the first time a real multi-year project starts, and free
# founder-hours surfaced prominently (not just as one quiet field) when
# every active project is purely waiting on the calendar.
# =============================================================================
_par = sim(capital=1_000_000.0)
_par_target = next((k for k in _par.order
                    if NODES[k]["yrs"] >= 2 and _par.can_start(k)), None)
check("a real startable multi-year project exists to test the tutorial "
      "note against",
      _par_target is not None, _par_target)
if _par_target:
    _par_out = S._agent_dispatch(_par, NODES, {"cmd": "start", "id": _par_target})
    _par_note = _par_out.get("a_calendar_floor_is_not_exclusive_research_time", "")
    check("starting the first long-calendar-floor project explains that "
          "the floor is not exclusive research time, and says to spend "
          "the spare hours on something else",
          "a_calendar_floor_is_not_exclusive_research_time" in _par_out
          and "else" in _par_note,
          _par_note)
    _par_target2 = next((k for k in _par.order
                         if NODES[k]["yrs"] >= 2 and _par.can_start(k)), None)
    if _par_target2:
        _par_out2 = S._agent_dispatch(_par, NODES, {"cmd": "start", "id": _par_target2})
        check("...but only once - a second long project in the same run "
              "does not repeat the tutorial note",
              "a_calendar_floor_is_not_exclusive_research_time" not in _par_out2,
              _par_out2.get("a_calendar_floor_is_not_exclusive_research_time"))

# --- free hours, shouted, when everything running is calendar-bound.
_fh = sim(capital=1_000_000.0)
_fh_target = next((k for k in _fh.order
                   if NODES[k]["yrs"] >= 3 and NODES[k]["ph"] > 0
                   and _fh.can_start(k)), None)
check("a startable project with real founder-hours AND a real calendar "
      "floor exists to test this against",
      _fh_target is not None, _fh_target)
if _fh_target:
    S._agent_dispatch(_fh, NODES, {"cmd": "start", "id": _fh_target})
    # Force the project's own hours fully spent for the year without
    # touching anything else about the sim, so it is purely calendar-bound -
    # the exact state _waiting_on reports as "the calendar".
    _fh.active[_fh_target]["ph_left"] = 0.0
    _fh_state = S._agent_dispatch(_fh, NODES, {"cmd": "state"})
    check("when every active project is only waiting on the calendar and "
          "real founder-hours sit unused, state says so prominently rather "
          "than leaving it to one quiet field",
          bool(_fh_state.get("free_hours_going_unused")),
          _fh_state.get("free_hours_going_unused"))
    # `step`'s reply is built from this exact same _agent_state() call
    # (protocol.py: "out.update(_agent_state(s, nodes))"), so the field
    # reaches it automatically - not re-asserted by actually calling step()
    # here, which would advance the year and recompute ph_left out from
    # under the fixture this check depends on.
    import inspect as _insp
    check("...and the field is assigned inside _agent_state() itself, which "
          "`step`'s own reply is built from - not something 'state' adds on "
          "top afterward",
          "free_hours_going_unused" in _insp.getsource(_protocol._agent_state),
          "checked _agent_state's own source")


