"""Scenario for the compact agent mode in a live game: `why` and `stuck` compact come from the real replies, and `state`
compact is far smaller than `state json` and than the text screen while keeping every field a turn needs. The parser and
the enrichers, on synthetic replies, are test_compact_mode."""
import json

from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_screen_state import render_state as _RSTATE


def scenario(name, **claims):
    """One named scenario check: it passes when every claim holds, and names the claims that do not."""
    failed = sorted(label for label, held in claims.items() if not held)
    check(name, not failed, failed)


_game = sim()
_blocked = next(node_id for node_id in ORDER if node_id not in _game.done and not _game.can_start(node_id))
_why_compact = S._agent_dispatch(_game, NODES, {"cmd": "why", "id": _blocked, "compact": True})
_stuck_plain = S._agent_dispatch(_game, NODES, {"cmd": "stuck"})
_stuck_compact = S._agent_dispatch(_game, NODES, {"cmd": "stuck", "compact": True})
scenario("scenario: live `why` and `stuck` compact name what blocks, one blocker per reason, smaller than the plain reply",
         why_says_blocked_and_names_what_blocks=_why_compact.get("blocked") is True and bool(_why_compact.get("blocked_by")),
         stuck_has_one_blocker_per_reason=len(_stuck_compact["blockers"]) == len(_stuck_plain["what_is_holding_you_up"]),
         stuck_is_smaller_than_json=len(json.dumps(_stuck_compact)) < len(json.dumps(_stuck_plain)))

# the project is started after the `why` and `stuck` replies are read
_started = next(node_id for node_id in ORDER if _game.can_start(node_id))
_game.start_project(_started)
_state_json = S._agent_dispatch(_game, NODES, {"cmd": "state", "json": True})
_state_compact = S._agent_dispatch(_game, NODES, {"cmd": "state", "json": True, "compact": True})
_json_bytes, _compact_bytes = len(json.dumps(_state_json)), len(json.dumps(_state_compact))
_fields_needed = ("year", "money", "net_per_year", "founder_hours_free", "projects",
                  "concerns", "standing", "danger", "nearest_goal_blocker")
scenario("scenario: live `state compact` is far smaller than `state json` and the text screen and keeps what a turn needs",
         under_a_third_of_json=_compact_bytes * 3 < _json_bytes,
         smaller_than_the_text_screen=_compact_bytes < len(_RSTATE(_state_json)),
         has_every_field_a_turn_needs=all(field in _state_compact for field in _fields_needed),
         lists_the_project_just_started=any(row["id"] == _started and "blocker" in row for row in _state_compact["projects"]),
         names_the_nearest_goal_blocker=isinstance(_state_compact["nearest_goal_blocker"], dict)
         and "id" in _state_compact["nearest_goal_blocker"],
         money_and_net_match_the_full_reply=_state_compact["money"] == _state_json["capital"]
         and _state_compact["net_per_year"] == _state_json["net_per_year"])
