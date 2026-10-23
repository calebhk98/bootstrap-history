"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: a saved and loaded game plays on exactly as the unbroken one would. The rules
have tests of their own: test_complaint_320_save_round_trip (serialising state, the demand key)."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state
from sim.refusal import LogLine, Refusal, cause_of, choices_of, facts_of


def _round_trip(game):
    path = os.path.join(tempfile.mkdtemp(), "save.json")
    save_state(game, path)
    reloaded = unopened_sim(capital=1.0)
    load_state(reloaded, path)
    return reloaded


def _two_projects_with_different_materials(game):
    node_ids = []
    for node_id in ORDER:
        materials = set(NODES[node_id].get("mat") or ())
        if node_id in game.done or not materials:
            continue
        if not node_ids or not materials & set(NODES[node_ids[0]]["mat"]):
            node_ids.append(node_id)
        if len(node_ids) == 2:
            return node_ids
    raise AssertionError("no two projects with different materials")


_game = unopened_sim(capital=1e9)
_first_id, _second_id = _two_projects_with_different_materials(_game)
_game.initialize_project(_first_id)
_game.resource_throttle()
_game.initialize_project(_second_id)
check("scenario save round trip: set-up, work started after the last throttle makes the held demand lag the live one",
      _game._cached_material_demand() != _game.annual_material_demand())
_reloaded = _round_trip(_game)
check("scenario save round trip: a reloaded game reads the same material demand and household demand ratios",
      _reloaded._cached_material_demand() == _game._cached_material_demand()
      and _reloaded.household_demand_ratios() == _game.household_demand_ratios(),
      (_reloaded._cached_material_demand(), _game._cached_material_demand()))

_log_game = unopened_sim(civ="rome_100ad", capital=1e5)
_log_game.end_year = _log_game.cfg["start_year"] + 50
_log_game.state.household.log.append((_log_game.year, LogLine("probe_kind", "a probe line", amount=3, names=["a", "b"])))
_log_game.state.household.log.append((_log_game.year, Refusal("probe_cause", "a probe refusal", choices=["x", "y"], figure=2.5)))
_log_game.state.household.capital = -50000.0   # a debt the creditors settle, which the log names by kind
_step_reply = S._agent_dispatch(_log_game, NODES, {"cmd": "step", "years": 3})
_log_reloaded = _round_trip(_log_game)


def _shape(entries):
    return [(year, str(message), cause_of(message), facts_of(message), choices_of(message)) for year, message in entries]


_codes = lambda reply: [(entry.get("event_kind"), entry.get("facts")) for entry in reply["entries"]]
_log_before = S._agent_dispatch(_log_game, NODES, {"cmd": "log", "limit": 100})
_log_after = S._agent_dispatch(_log_reloaded, NODES, {"cmd": "log", "limit": 100})
_step_codes = [(event["event_kind"], event["facts"]) for event in _step_reply["events"] if event.get("event_kind")]
check("scenario save round trip: a played game's log keeps its kinds, facts and choices through a save and load, "
      "and the step's events are in it",
      _shape(_log_reloaded.state.household.log) == _shape(_log_game.state.household.log)
      and any(cause_of(message) for _year, message in _log_game.state.household.log)
      and _codes(_log_before) == _codes(_log_after) and any(kind for kind, _facts in _codes(_log_after))
      and bool(_step_codes) and all(code in _codes(_log_after) for code in _step_codes),
      (_codes(_log_before)[:4], _codes(_log_after)[:4], _step_codes[:3]))
