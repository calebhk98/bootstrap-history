"""Typed names resolve to ids, fog limits what is suggested, and `available` sorts and pages. The rules are called on the
tree's names, on ids and sort keys the test states, and on a stand-in game that holds only what they read; the
name step of the command dispatch is called on a stand-in game too."""
from types import SimpleNamespace
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.ui.proto.dispatch import _agent_dispatch_inner
from sim.ui.proto.name_candidates import candidates_the_player_may_see
from sim.ui.proto.nodes import _did_you_mean, _resolve_by_name
from sim.ui.proto.techtree import _SORT_KEYS, _available_params, _heard_all_sorted, _sort_startable_list

QUICK_TOPIC = True

# --- A typed name resolves to the id of the node that carries it.
check("a typed name resolves to the id, case and punctuation folded",
      _resolve_by_name("Reaper-Binder") == ["ag2_reaper_binder"], _resolve_by_name("Reaper-Binder"))
printed_name = NODES["ag2_balanced_ration"]["name"]
check("a name copied verbatim off another screen resolves the same way",
      "ag2_balanced_ration" in _resolve_by_name(printed_name), (printed_name, _resolve_by_name(printed_name)))
loom = _resolve_by_name("loom")
check("a fragment that several names share resolves to every one of them, for the real ids to choose between",
      len(loom) >= 2 and "tex_horizontal_loom" in loom, loom)
check("a fragment too short to mean a name resolves to nothing", _resolve_by_name("lo") == [], _resolve_by_name("lo"))

# --- Fog: a name never offers a candidate the player has not heard of.
heard = {"loom_a", "loom_b"}
visible = heard.__contains__
check("under fog the candidates are only what the player has heard of",
      candidates_the_player_may_see(["loom_a", "loom_b", "loom_hidden"], visible, "goal", "start", ()) == ["loom_a", "loom_b"])
check("fog never offers more than full visibility would",
      set(candidates_the_player_may_see(["a", "b", "c"], {"a"}.__contains__, "goal", "why", ())) < {"a", "b", "c"})
check("why on the goal's exact printed name is the one thing fog answers",
      candidates_the_player_may_see(["goal"], visible, "goal", "why", ("goal",)) == ["goal"])
check("...but the exception does not widen to other commands on the same name",
      candidates_the_player_may_see(["goal"], visible, "goal", "start", ("goal",)) == [])
check("...and a vague guess does not silently resolve to the goal",
      candidates_the_player_may_see(["goal"], visible, "goal", "why", ()) == [])

# --- `available` can be sorted and paged all the way through.
nodes = {"a": {"name": "Alpha", "risk": 0.3, "ph": 5, "yrs": 1}, "b": {"name": "Beta", "risk": 0.1, "ph": 9, "yrs": 2},
         "c": {"name": "Gamma", "risk": 0.2, "ph": 1, "yrs": 3}}
costs = {"a": 30.0, "b": 10.0, "c": 20.0}
game = SimpleNamespace(project_cost=costs.get)
check("a plain page defaults to cheapest first", _sort_startable_list(game, nodes, ["a", "b", "c"], None, False) == ["b", "c", "a"])
check("available can be sorted by risk", _sort_startable_list(game, nodes, ["a", "b", "c"], _SORT_KEYS["risk"], False) == ["b", "c", "a"])
check("...and reversed",
      _sort_startable_list(game, nodes, ["a", "b", "c"], _SORT_KEYS["risk"], True) == ["a", "c", "b"])
check("...by hours as well", _sort_startable_list(game, nodes, ["a", "b", "c"], _SORT_KEYS["hours"], True) == ["b", "a", "c"])
paging = _available_params({"limit": "10", "offset": "-4", "sort": " Risk ", "reverse": True})
check("the paging and sort knobs are read off the command: limit, offset held at zero, a folded sort key, reverse",
      paging[3] == 10 and paging[4] == 0 and paging[6] == "risk" and paging[7] is _SORT_KEYS["risk"] and paging[8] is True, paging)
check("a limit that is not a number is no limit", _available_params({"limit": "many"})[3] == 0)
quoted = _available_params({"subject": '"zzzznotaheading"'})
check("a quoted word that is not a subject heading is a search word", quoted[1] == "zzzznotaheading" and quoted[0] == "", quoted)

# --- Fog: `available`'s heard-of block respects `find`.
tree = {"atomic_theory": {"name": "Atomic theory", "pre": ["x"], "note": "", "tags": []},
        "dyeing": {"name": "Dyeing", "pre": [], "note": "", "tags": []}}
stand_in = SimpleNamespace(revealed={"atomic_theory", "dyeing"}, done=set(), active={},
                           start_reason=lambda node_id: (False, "not yet"))
check("a search matching nothing heard of lists nothing from the heard-of block",
      _heard_all_sorted(stand_in, tree, "zzzznonexistentxyz", "", None, False) == [])
check("...but the heard-of list still shows everything heard of when no search was asked for",
      sorted(_heard_all_sorted(stand_in, tree, "", "", None, False)) == ["atomic_theory", "dyeing"])
check("...and a search that does match a heard-of item still shows it",
      _heard_all_sorted(stand_in, tree, "atomic", "", None, False) == ["atomic_theory"])
check("the heard-of list is nearest first: fewest missing prerequisites",
      _heard_all_sorted(stand_in, tree, "", "", None, False)[0] == "dyeing")

# --- The dispatch step that turns a typed name into an id, on a stand-in game (the step runs before any handler reads the game).
def _name_stand_in(fog, heard=()):
    return SimpleNamespace(nodes=NODES, fog=fog, goal=GOAL, done=set(), active={}, revealed=set(heard), is_visible=lambda node_id, _memo=None: node_id in heard)


def _name_reply(game, command, name):
    with mock.patch("sim.ui.proto.dispatch.material_story", return_value=None):   # a material story reads the market
        return _agent_dispatch_inner(game, NODES, {"cmd": command, "id": name})


full_loom = _name_reply(_name_stand_in(False), "why", "loom")["error"]
check("a typed name several nodes share is refused with cause ambiguous_name and the real ids to choose between",
      full_loom.cause == "ambiguous_name" and "tex_horizontal_loom" in full_loom.choices and len(full_loom.choices) >= 2,
      (full_loom.cause, full_loom.choices))
two_heard = set(full_loom.choices[:2])
fogged_two = _name_reply(_name_stand_in(True, two_heard), "why", "loom")["error"]
check("under fog an ambiguous name offers only the candidates the player has heard of, fewer than full visibility",
      fogged_two.cause == "ambiguous_name" and set(fogged_two.choices) == two_heard < set(full_loom.choices), fogged_two.choices)
goal_start = _name_reply(_name_stand_in(True), "start", NODES[GOAL]["name"])["error"]
check("under fog `start` on the goal's name is refused as never_heard_of", goal_start.cause == "never_heard_of", goal_start.cause)
guess = _name_reply(_name_stand_in(True), "why", "transistor")["error"]
check("under fog a vague guess is never_heard_of and offers no unheard-of node, the goal included",
      guess.cause == "never_heard_of" and GOAL not in (guess.choices or ()), (guess.cause, guess.choices))
did_you_mean_tree = {"aqueduct_survey": {}, "aqueduct_arch": {}, "aqueduct_lining": {}}
check("a near miss under fog is answered only from what the player has heard of",
      _did_you_mean("aqueduct_surve", did_you_mean_tree, sim=_name_stand_in(True, {"aqueduct_survey"})) == ["aqueduct_survey"])
check("a near miss with fog off is answered from every node",
      sorted(_did_you_mean("aqueduct_surve", did_you_mean_tree, sim=_name_stand_in(False))) == sorted(did_you_mean_tree))
