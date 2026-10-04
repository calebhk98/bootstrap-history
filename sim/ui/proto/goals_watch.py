"""Progress toward the formal goal and any goals the player chooses to watch (Complaint 268).

A watched goal is tracked here only; `sim.goal`, the score and the end text stay with the formal
goal (Complaint 404). Under fog a goal the player cannot know is a count, never a name."""
from sim.engine import ui_port
from sim.ui import memory
from .nodes import _norm_name

TOPIC = "goals_watch"
MAX_WATCHED = 25
_TREE = []   # the tree is read once, on first use


def _watched_ids(sim):
    return memory.remembered(sim, TOPIC).setdefault("ids", [])


def _catalog(sim):
    if not _TREE:
        _TREE.append(ui_port.load()[0])
    return [goal for goal in ui_port.selectable_goals(_TREE[0], sim.nodes) if goal["node"] in sim.nodes]


def _knowable(sim, node_id):
    return not sim.fog or sim.is_visible(node_id)


def _progress(sim, node_id):
    needed = ui_port.closure(sim.nodes, node_id)
    return {"done": len(needed & sim.done), "total": len(needed), "reached": node_id in sim.done}


def _row(sim, node_id):
    row = {"id": None, "name": None, **_progress(sim, node_id)}
    if _knowable(sim, node_id):
        row["id"], row["name"] = node_id, sim.nodes[node_id].get("name", node_id)
    return row


def resolve_goal_reference(sim, text, among=None):
    """(node_id, None) for the one goal whose id or name is `text`, else (None, error).

    Only goals the player can know are matched, so a refusal never confirms a fogged name."""
    wanted = _norm_name(text)
    goals = [goal for goal in _catalog(sim) if _knowable(sim, goal["node"])
             and (among is None or goal["node"] in among)]
    for matches in (
            [goal for goal in goals if wanted in (_norm_name(goal["node"]), _norm_name(goal.get("name", "")))],
            [goal for goal in goals if len(wanted) >= 3 and _norm_name(goal.get("name", "")).startswith(wanted)]):
        if len(matches) == 1:
            return matches[0]["node"], None
        if matches:
            return None, "%r matches several goals: %s" % (text, ", ".join(goal["node"] for goal in matches))
    return None, "no goal called %r that you know of. 'goals' lists the ones you can watch" % text


def watched_rows(sim):
    return [_row(sim, node_id) for node_id in _watched_ids(sim) if node_id in sim.nodes]


def goals_report(sim):
    formal = _row(sim, sim.goal) if sim.goal in sim.nodes else {"id": None, "name": None, "done": 0, "total": 0, "reached": False}
    formal["year_reached"] = sim.goal_year
    watched = set(_watched_ids(sim))
    unknown = 0
    choices = []
    for goal in _catalog(sim):
        if goal["node"] == sim.goal or goal["node"] in watched:
            continue
        if _knowable(sim, goal["node"]):
            choices.append(_row(sim, goal["node"]))
        else:
            unknown += 1
    return {"ok": True, "formal": formal, "watched": watched_rows(sim), "choices": choices,
            "unknown_goals": unknown, "fog": bool(sim.fog),
            "note": "The formal goal is the one the score and the end text use. A watched goal is "
                    "tracked here only; reaching it changes nothing else."}


def watch(sim, text):
    node_id, error = resolve_goal_reference(sim, text)
    if error:
        return {"ok": False, "error": error}
    if node_id == sim.goal:
        return {"ok": False, "error": "that is already the formal goal"}
    ids = _watched_ids(sim)
    if node_id not in ids:
        if len(ids) >= MAX_WATCHED:
            return {"ok": False, "error": "watching too many goals; 'goals unwatch <goal>' first"}
        ids.append(node_id)
    return {**goals_report(sim), "changed": "watching %s" % sim.nodes[node_id].get("name", node_id)}


def unwatch(sim, text):
    ids = _watched_ids(sim)
    node_id, error = resolve_goal_reference(sim, text, among=ids)
    if error:
        return {"ok": False, "error": "you are not watching a goal called %r" % text}
    ids.remove(node_id)
    return {**goals_report(sim), "changed": "no longer watching %s" % sim.nodes[node_id].get("name", node_id)}
