"""sort_nearest: regression checks, run individually with `--only sort_nearest`."""
from .harness import *  # noqa: F401,F403

# `available sort nearest` measured distance to becoming startable, never distance to a goal;
# it is now fewest_missing, with the old spelling kept working.
check("'fewest_missing' is the advertised sort key now, not the misleading 'nearest'",
      "fewest_missing" in _protocol._SORT_KEY_NAMES and "nearest" not in _protocol._SORT_KEY_NAMES,
      _protocol._SORT_KEY_NAMES)
check("...but the old spelling still works, for any script already using it",
      "nearest" in _protocol._SORT_KEYS and "fewest_missing" in _protocol._SORT_KEYS,
      sorted(_protocol._SORT_KEYS))

# One game serves the fog, venture and rush checks.
shared = sim(capital=5_000_000.0)

# `stuck` says outright, under fog, that it cannot check the goal's route.
shared.fog = True
shared.revealed = set()
stuck_fogged = S._agent_dispatch(shared, NODES, {"cmd": "stuck"})
check("`stuck`, under fog with a goal set, says it cannot check the goal's route",
      "this_does_not_know_your_goal" in stuck_fogged, stuck_fogged.get("this_does_not_know_your_goal"))
shared.fog = False
check("...and says nothing of the kind with fog off, where the goal-aware branch runs",
      "this_does_not_know_your_goal" not in S._agent_dispatch(shared, NODES, {"cmd": "stuck"}),
      "fog off: no such field")
shared.fog = True

# is_venture offers `open` only where there is something to open a door on.
check("opening `arithmetic_positional` is not offered - a notation is not a door to open",
      not shared.is_venture("arithmetic_positional")
      and NODES["arithmetic_positional"]["rev"] == 0 and NODES["arithmetic_positional"]["up"] == 0,
      (NODES["arithmetic_positional"]["rev"], NODES["arithmetic_positional"]["up"]))
check("circuit theory does not open as a concern; the capacitor it improves does",
      not shared.is_venture("el2_negative_feedback_stability_gain") and shared.is_venture("el2_capacitor_electrolytic"),
      (shared.is_venture("el2_negative_feedback_stability_gain"), shared.is_venture("el2_capacitor_electrolytic")))
check("a financial instrument is not a venture; the bank that uses one is",
      not shared.is_venture("fin_cheque") and shared.is_venture("fin_deposit_bank"),
      (shared.is_venture("fin_cheque"), shared.is_venture("fin_deposit_bank")))
check("a husbandry method does not open its own shop; the farm it improves does",
      not shared.is_venture("ag2_hybridisation") and shared.is_venture("crop_rotation"),
      (shared.is_venture("ag2_hybridisation"), shared.is_venture("crop_rotation")))
check("a trade practised for a fee (an assay office) still opens as a concern",
      shared.is_venture("fin_assay_office"), shared.is_venture("fin_assay_office"))
venture_count = sum(1 for node_id in NODES if shared.is_venture(node_id))
check("the count of nodes offered to `open` is neither inflated by notations nor collapsed toward zero",
      1300 <= venture_count <= 1450, venture_count)

# `rush`: a bulk start, capped by hours and by limit, fog-safe.
visible_before_rush = {entry["id"] for entry in S._agent_available(shared, NODES, {"all": True})["available"]}
rush_one = S._agent_dispatch(shared, NODES, {"cmd": "rush", "limit": 1})
rush_many = S._agent_dispatch(shared, NODES, {"cmd": "rush", "limit": 1000})
check("a rush limit caps how many it actually begins", rush_one["count_started"] == 1, rush_one["count_started"])
check("`rush` starts more than one thing in a single call", rush_many.get("count_started", 0) >= 2,
      rush_many.get("count_started"))
check("...and every id it reports started is actually active now",
      all(entry["id"] in shared.active or entry["id"] in shared.done
          for entry in rush_one["started"] + rush_many["started"]),
      [entry["id"] for entry in rush_many["started"]])
check("under fog, the first thing `rush` starts was already on the visible `available` list",
      all(entry["id"] in visible_before_rush for entry in rush_one["started"]),
      [entry["id"] for entry in rush_one["started"] if entry["id"] not in visible_before_rush])
hours_owed = sum(NODES[entry["id"]]["ph"] for entry in rush_many.get("started") or [])
check("`rush` does not commit more hours than a couple of years can hold",
      hours_owed <= shared.labour.director_pool() * 2.0 + max(
          NODES[entry["id"]]["ph"] for entry in (rush_many.get("started") or [{"id": GOAL}])),
      (hours_owed, shared.labour.director_pool()))
check("...and says why it stopped rather than silently starting fewer",
      any("would not make them go faster" in str(entry.get("why")) for entry in (rush_many.get("not_started") or [])),
      [entry.get("why") for entry in (rush_many.get("not_started") or [])][:1])
check("'values' and 'rush' are in the list every unknown-command refusal advertises",
      "values" in S.KNOWN_COMMANDS and "rush" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)

# The founder's death is legible: its own field with a numeric age, the step stops there, the age
# survives a save and load, and the log says what it means for the run.
mortal = sim(capital=1_000_000.0, events=True)
mortal.cfg["immortal"] = False
mortal.life_left = 1.0
mortal.end_year = mortal.cfg["start_year"] + 200
step_reply = S._agent_dispatch(mortal, NODES, {"cmd": "step", "years": 150})
died = step_reply.get("the_founder_died_this_step")
check("the founder's death gets a field of its own in the step that carries it",
      isinstance(died, dict), died)
check("...and the age is a number you can read", isinstance((died or {}).get("aged_about"), int), died)
check("...and `state` carries the age from then on",
      step_reply.get("founder_died_aged") == (died or {}).get("aged_about"),
      (step_reply.get("founder_died_aged"), died))
check("...and the step stopped there instead of running the requested years past it",
      step_reply["year"] < mortal.cfg["start_year"] + 150, step_reply["year"])
session_path = os.path.join(ROOT, _rel("founder_death.json"))
S.save_state(mortal, session_path)
reloaded = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
reloaded.goal, reloaded.done_year = GOAL, {}
S.load_state(reloaded, session_path)
reloaded_state = S._agent_dispatch(reloaded, NODES, {"cmd": "state"})
check("the founder's age at death survives a save and a fresh process loading it back",
      reloaded_state.get("founder_died_aged") == step_reply.get("founder_died_aged")
      and reloaded_state.get("founder_died_aged") is not None,
      (reloaded_state.get("founder_died_aged"), step_reply.get("founder_died_aged")))
for _ in range(2):
    mortal.step()
check("the founder's death says what it means for the run, not only that it happened",
      any("THE FOUNDER DIES" in message and "no deputy" in message for _, message in mortal.log),
      [message for _, message in mortal.log if "FOUNDER DIES" in message][:1])
check("...and the programme dissolving is counted down where a player sees it",
      any("DISSOLVING" in message and "ends at twelve" in message for _, message in mortal.log),
      [message for _, message in mortal.log if "DISSOLVING" in message][:1])

# Losing people to death and better offers is announced, not silent.
attrition = sim(capital=10_000_000.0, events=False)
run_it(attrition, "workshop_first", "school_founded", "freedman_staff")
attrition.labour.hire("scholar", 8)
for _ in range(12):
    attrition.step()
    if any("lose" in message and "scholar" in message for _, message in attrition.log):
        break
check("losing people to death and better offers is announced, not silent",
      any("lose" in message and "scholar" in message for _, message in attrition.log),
      [message for _, message in attrition.log if "lose" in message][:2])

# --- BREAK, round 12: a developer's own change-log marker was shipped in the
# prose a player reads. 1,108 nodes carried "[AUDIT: ... See JOB 1 upkeep
# audit.]" in their note field, the win condition among them, naming the task
# numbering of the agent that had edited them. The reasoning for a change
# belongs in the commit message; the note field is what the player reads.
_leaks = sorted(node_id for node_id, value in NODES.items()
                if "AUDIT" in ((value.get("note") or "") + (value.get("name") or "")))
check("no developer change-log marker is shipped in player-facing prose",
      not _leaks, _leaks[:5])

from sim.ui.protocol import _unlocked_by as _UB, _downstream_of as _DS
_ra_cases = ("sea_clinker_hull", "met_bloomery_bog_iron", "fud_chinampa")
for _k_ra in _ra_cases:
    _un = _UB(_k_ra, NODES)
    check("%s is not a dead end: something really does need it" % _k_ra,
          bool(_un), _un)
check("...and what rests on it is counted, not reported as nothing",
      all(len(_DS(node_id, NODES)) >= 1 for node_id in _ra_cases),
      {node_id: len(_DS(node_id, NODES)) for node_id in _ra_cases})
# THE REASON THE CACHED INDEX CANNOT DO THIS. The tree is a directed acyclic
# graph on `pre` and is NOT acyclic once req_any options are edges too: one
# example is hydrochloric_acid, whose sulfuric_acid_supply group offers
# chm_contact_sulfuric as an alternative to lead_chamber, and
# chm_contact_sulfuric needs cap_pure_4N, which needs analytical_chemistry,
# which needs hydrochloric_acid back again - a real cycle if that branch of
# the substitution is the one walked, even though a player who takes the
# other branch (lead_chamber) never sees it. A bitmask descendant index that
# assumes a DAG runs out of memory on cycles like this, which is exactly what
# happened when this fix was first attempted in data.py, so the walk that
# answers a player carries a visited set instead.
#
# naive14's point_contact_transistor/single_crystal fix (TOP_PROBLEMS #1)
# removed a DIFFERENT cycle that used to live here - junction_transistor ->
# point_contact_transistor -> (req_any option) silicon_path ->
# junction_transistor - because that edge was itself the bug: the node's own
# note said it did not need single_crystal or its silicon_path alternative at
# all. Losing that cycle is the fix working, not a regression, which is why
# the check below no longer hardcodes a path through junction_transistor.
def _cycle_on(edges_of):
    """Any node reachable from itself, following whatever edges are given."""
    seen_all = set()
    for root in sorted(NODES):
        if root in seen_all:
            continue
        stack, seen = [root], set()
        while stack:
            cur = stack.pop()
            for nxt in edges_of(cur):
                if nxt == root:
                    return root
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
        seen_all |= seen
    return None

check("the tree is acyclic on hard prerequisites, which is what closure() "
      "walks and why it must not follow substitutions",
      _cycle_on(lambda k: [prereq_id for prereq_id in NODES[k]["pre"] if prereq_id in NODES]) is None,
      _cycle_on(lambda k: [prereq_id for prereq_id in NODES[k]["pre"] if prereq_id in NODES]))

def _pre_and_single_option_any(node_id):
    node = NODES[node_id]
    out = [prereq_id for prereq_id in node["pre"] if prereq_id in NODES]
    for req_group in (node.get("req_any") or []):
        opts = req_group.get("options") or {}
        if len(opts) == 1:
            (opt,) = opts.keys()
            if opt in NODES:
                out.append(opt)
    return out
check("pre plus every single-option req_any edge is still acyclic over the "
      "whole tree - the safety margin the single-option walk rests on, since "
      "a multi-option group (two or more real alternatives) walked the same "
      "way genuinely can cycle (hydrochloric_acid -> chm_contact_sulfuric -> "
      "cap_pure_4N -> analytical_chemistry -> hydrochloric_acid is real) and "
      "must never be",
      _cycle_on(_pre_and_single_option_any) is None,
      _cycle_on(_pre_and_single_option_any))

def _pre_and_any(node_id):
    # req_any OPTIONS ARE NOT ALL NODES. A group can offer a MATERIAL as an
    # alternative to a technology ("any of lead_kg, mat_lead_sheet ..."), so a
    # walk over these edges has to skip anything that is not a node or it dies
    # on KeyError: 'lead_kg'. _unlocked_by is safe from this by construction,
    # because it only ever asks whether a node's options mention a given
    # node id, never walking through one.
    out = [prereq_id for prereq_id in NODES[node_id]["pre"] if prereq_id in NODES]
    for req_group in (NODES[node_id].get("req_any") or []):
        out.extend(option for option in sorted(req_group.get("options") or {}) if option in NODES)
    return out

# _cycle_on (above) is a root-reachability check that skips any node once it
# has been SEEN from an earlier root, so it can miss a cycle that does not
# happen to include whichever root sorted(NODES) tries first - it is safe
# for the two checks above because pre and pre-plus-single-option are both
# genuinely acyclic there (nothing to miss), but not a safe way to CONFIRM a
# cycle exists, so this checks direct reachability from the one node the
# cycle above was traced through instead.
def _reaches(start, target, edges_of):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        for nxt in edges_of(cur):
            if nxt == target:
                return True
            if nxt not in seen:
                seen.add(nxt); stack.append(nxt)
    return False

check("...and NOT acyclic once every substitution option counts as an edge, "
      "which is why the cached bitmask index cannot answer this and a "
      "visited set must",
      _reaches("hydrochloric_acid", "hydrochloric_acid", _pre_and_any),
      "no cycle found through hydrochloric_acid")

