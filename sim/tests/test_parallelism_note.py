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
    # _agent_state() PLUS ITS OWN SECTION HELPERS, NOT _agent_state() ALONE.
    # This read only _agent_state's source while that function was one 499-line
    # dict literal. It is now a short assembler over `_agent_state_*` helpers,
    # one per section of the reply, and the assignment this check is about
    # lives in _agent_state_training_and_hours.
    #
    # Reading only the assembler would have this check pass on a COMMENT that
    # happens to name the field, which is what briefly happened: the split left
    # a comment above the update() call mentioning free_hours_going_unused, and
    # a substring search cannot tell that from an assignment. A check that
    # passes on prose is worse than no check, because it still reads as
    # evidence. Gathering the helpers by prefix puts the real assignment back in
    # scope, and keeps it there across any future re-split.
    #
    # The property being asserted has not changed: whichever part of
    # _agent_state's own call graph produces this field, it must be that call
    # graph, so that `step`'s reply - built from the same _agent_state() call -
    # gets the field without anyone maintaining a second copy.
    # READ THE DEFINING MODULE, NOT THE SHIM. engine/protocol.py re-exports a
    # fixed list of public protocol names and the section helpers are not on
    # it, so gathering them off the shim finds nothing and this check would
    # once again be passing on the comment alone. engine.proto.state is where
    # they are defined.
    from engine.proto import state as _state_module
    _state_source = "".join(
        [_insp.getsource(_state_module._agent_state)]
        + [_insp.getsource(getattr(_state_module, _name))
           for _name in sorted(dir(_state_module))
           if _name.startswith("_agent_state_")
           and callable(getattr(_state_module, _name, None))])
    check("...and the field is assigned inside _agent_state()'s own call "
          "graph, which `step`'s own reply is built from - not something "
          "'state' adds on top afterward",
          "free_hours_going_unused" in _state_source,
          "checked _agent_state and its _agent_state_* section helpers")


