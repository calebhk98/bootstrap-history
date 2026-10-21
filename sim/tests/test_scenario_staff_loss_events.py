"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: staff who take better offers close a concern, and the step's reply carries
both events and stops on it. The rules are plain functions with tests of their own: test_complaint_579_staff_loss_events.
This builds a game and steps three years, which is why it is a topic of its own (it runs past two minutes)."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent

_loss_node = concern_needing_craftsmen_to_supervise()
_loss_game = sim(capital=1_000_000.0)
_loss_game.done.update(NODES[_loss_node]["pre"])
_loss_game.done.add(_loss_node)
_loss_game._done_changed()
_loss_game.employees["artisan"] = 6.0
_loss_game.labour._resync_pools()
_loss_game.open_venture(_loss_node)
_loss_game.state.founder.policy["keep_pay_at_market"] = False
_loss_game.state.household.staff_pay_held["artisan"] = 1e-6     # paid next to nothing: every hired craftsman takes an offer
_loss_reply = ask_agent(_loss_game, cmd="step", years=3)
_loss_events = _loss_reply["events"]
_departure = next((event for event in _loss_events if event.get("event_kind") == "staff_lost_stops_concerns"), None)
_closure = next((event for event in _loss_events if event.get("event_kind") == "concerns_closed_unstaffed"), None)
check("scenario staff loss: a departure that closes a concern is an event in the step's reply, and the step stops on it",
      _departure is not None and _departure["facts"]["reason"] == "better_offers"
      and _departure["facts"]["trades"] == {"artisan": 6} and _departure["facts"]["stops"] == [_loss_node]
      and _loss_reply.get("stopped_early") and _loss_reply.get("stopped_kind"), (_departure, _loss_reply.get("stopped_kind")))
check("scenario staff loss: the closure is an event naming the concern, its cause, the shortfall and what it stops earning",
      _closure is not None and _closure["facts"]["concerns"] == [_loss_node]
      and _closure["facts"]["closed_because"] == "short_staffed" and _closure["facts"]["short"]
      and "stops_earnings_per_year" in _closure["facts"], _closure)
_quiet_game = sim(capital=1_000_000.0)
_quiet_game.employees["artisan"] = 3.0
_quiet_game.labour._resync_pools()
_quiet_game.state.founder.policy["keep_pay_at_market"] = False
_quiet_game.state.household.staff_pay_held["artisan"] = 1e-6
_quiet_events = ask_agent(_quiet_game, cmd="step", years=1)["events"]
_quiet_left = [event for event in _quiet_events if str(event.get("event_kind", "")).startswith("staff_lost")]
check("scenario staff loss: a departure that stops nothing is a plain staff_lost event with no stops",
      _quiet_left and _quiet_left[0]["event_kind"] == "staff_lost" and _quiet_left[0]["facts"]["stops"] == [], _quiet_events)
