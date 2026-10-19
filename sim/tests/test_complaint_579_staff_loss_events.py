"""Complaints/579: each departure and each closure is a reply event with a kind, its cause and what it stops."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent
from sim.ui.proto.event_kinds import EVENT_KINDS, stops_a_step

_node_id = concern_needing_craftsmen_to_supervise()
_game = sim(capital=1_000_000.0)
_game.done.update(NODES[_node_id]["pre"])
_game.done.add(_node_id)
_game._done_changed()
_game.employees["artisan"] = 6.0
_game.labour._resync_pools()
_game.open_venture(_node_id)
_game.state.founder.policy["keep_pay_at_market"] = False
_game.state.household.staff_pay_held["artisan"] = 1e-6     # paid next to nothing: every hired craftsman takes an offer

_reply = ask_agent(_game, cmd="step", years=3)
_events = _reply["events"]
_departure = next((event for event in _events if event.get("event_kind") == "staff_lost_stops_concerns"), None)
_closure = next((event for event in _events if event.get("event_kind") == "concerns_closed_unstaffed"), None)

check("a departure that closes a concern is an event in the step's reply", _departure is not None, _events)
check("...its kind is listed in event_kinds", "staff_lost_stops_concerns" in EVENT_KINDS)
check("...it carries its cause", _departure["facts"]["reason"] == "better_offers", _departure)
check("...it names the people and what it stops",
      _departure["facts"]["trades"] == {"artisan": 6} and _departure["facts"]["stops"] == [_node_id], _departure)
check("...it is a warning that stops a step", stops_a_step(_departure), _departure)
check("the step stopped early on it", _reply.get("stopped_early") and _reply.get("stopped_kind"), _reply.get("stopped_kind"))
check("the closure is an event naming the concern, its cause and the shortfall",
      _closure is not None and _closure["facts"]["concerns"] == [_node_id]
      and _closure["facts"]["closed_because"] == "short_staffed" and _closure["facts"]["short"], _closure)
check("...and what it stops earning", "stops_earnings_per_year" in _closure["facts"], _closure)

# a loss that leaves every running concern staffed is an ordinary departure
_quiet = sim(capital=1_000_000.0)
_quiet.employees["artisan"] = 3.0
_quiet.labour._resync_pools()
_quiet.state.founder.policy["keep_pay_at_market"] = False
_quiet.state.household.staff_pay_held["artisan"] = 1e-6
_quiet_events = ask_agent(_quiet, cmd="step", years=1)["events"]
_left = [event for event in _quiet_events if str(event.get("event_kind", "")).startswith("staff_lost")]
check("a departure that stops nothing is a plain staff_lost event with no stops",
      _left and _left[0]["event_kind"] == "staff_lost" and _left[0]["facts"]["stops"] == [], _quiet_events)
