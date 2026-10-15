"""Complaint 320: a saved and loaded game plays on exactly as the unbroken one
would. State the next year reads must be in the save: the material demand the
last throttle left behind, and the order of every dict (float sums follow it)."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state


def _round_trip(game):
    path = os.path.join(tempfile.mkdtemp(), "save.json")
    save_state(game, path)
    reloaded = sim(capital=1.0)
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


# --- the demand the last throttle left behind is read before the next one -----
game = sim(capital=1e9)
first_id, second_id = _two_projects_with_different_materials(game)
game.initialize_project(first_id)
game.resource_throttle()
game.initialize_project(second_id)
check("set-up: work started after the last throttle makes the held demand lag the live one",
      game._cached_material_demand() != game.annual_material_demand())
reloaded = _round_trip(game)
check("a reloaded game reads the same material demand the unbroken game reads",
      reloaded._cached_material_demand() == game._cached_material_demand(),
      (reloaded._cached_material_demand(), game._cached_material_demand()))

# --- dict order survives the save --------------------------------------------
order_game = sim(capital=1e9)
order_game.state.projects.done_year = {"zeta_node": 3, "alpha_node": 4, "mid_node": 5}
order_reloaded = _round_trip(order_game)
check("a dict keeps its insertion order across a save",
      list(order_reloaded.state.projects.done_year) == list(order_game.state.projects.done_year),
      list(order_reloaded.state.projects.done_year))

# --- household demand ratios are a function of the rounded population and income, not of when they were last computed ---
demand_game = sim(capital=1e9)
before_ratios = dict(demand_game.household_demand_ratios())
for cohort in ("children", "working_age", "elderly"):
    setattr(demand_game.population, cohort, getattr(demand_game.population, cohort) * 1.0003)
check("set-up: the population moved less than the rounding step",
      demand_game.household_demand_ratios() is not None)
demand_reloaded = _round_trip(demand_game)
check("a reloaded game reads the household demand ratios the unbroken game reads",
      demand_reloaded.household_demand_ratios() == demand_game.household_demand_ratios())

# --- Complaint 521: a log line keeps its kind, facts and choices across a save ---------------------------------
from sim.refusal import LogLine, Refusal, cause_of, facts_of, choices_of
log_game = sim(civ="rome_100ad", capital=1e5)
log_game.end_year = log_game.cfg["start_year"] + 50
log_game.state.household.log.append((log_game.year, LogLine("probe_kind", "a probe line", amount=3, names=["a", "b"])))
log_game.state.household.log.append((log_game.year, "a plain line"))
log_game.state.household.log.append((log_game.year, Refusal("probe_cause", "a probe refusal", choices=["x", "y"], figure=2.5)))
log_game.state.household.capital = -50000.0   # a debt the creditors settle, which the log names by kind
_step_reply = S._agent_dispatch(log_game, NODES, {"cmd": "step", "years": 3})
log_reloaded = _round_trip(log_game)


def _shape(entries):
    return [(year, str(message), cause_of(message), facts_of(message), choices_of(message)) for year, message in entries]


check("a game's log has the same kinds, facts and choices after a save and load as before",
      _shape(log_reloaded.state.household.log) == _shape(log_game.state.household.log),
      (_shape(log_reloaded.state.household.log)[:3], _shape(log_game.state.household.log)[:3]))
check("set-up: the log holds lines with a kind",
      any(cause_of(message) for _year, message in log_game.state.household.log))
_log_before = S._agent_dispatch(log_game, NODES, {"cmd": "log", "limit": 100})
_log_after = S._agent_dispatch(log_reloaded, NODES, {"cmd": "log", "limit": 100})
_codes = lambda reply: [(entry.get("event_kind"), entry.get("facts")) for entry in reply["entries"]]
check("the `log` reply's events have the same kinds and facts after a save and load",
      _codes(_log_before) == _codes(_log_after) and any(kind for kind, _facts in _codes(_log_after)),
      (_codes(_log_before)[:4], _codes(_log_after)[:4]))
_step_codes = [(event["event_kind"], event["facts"]) for event in _step_reply["events"] if event.get("event_kind")]
_reloaded_codes = _codes(_log_after)
check("a step reply's events appear in the reloaded log with the same kinds and facts",
      bool(_step_codes) and all(code in _reloaded_codes for code in _step_codes), (_step_codes[:3], _reloaded_codes[:3]))


def _coded_values(value, found, seen):
    """Every Refusal or LogLine held anywhere in a state, as (code, facts)."""
    if id(value) in seen:
        return found
    seen.add(id(value))
    if isinstance(value, Refusal):
        found.append((cause_of(value), facts_of(value)))
    elif isinstance(value, dict):
        for item in list(value.keys()) + list(value.values()):
            _coded_values(item, found, seen)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _coded_values(item, found, seen)
    elif hasattr(value, "__dataclass_fields__"):
        for name in value.__dataclass_fields__:
            _coded_values(getattr(value, name), found, seen)
    return found


check("every coded value held anywhere in the state comes back from a save",
      sorted(map(repr, _coded_values(log_reloaded.state, [], set()))) == sorted(map(repr, _coded_values(log_game.state, [], set()))),
      (len(_coded_values(log_reloaded.state, [], set())), len(_coded_values(log_game.state, [], set()))))
