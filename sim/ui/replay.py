"""Replay carry-over (Complaint 267): start a new run knowing the routes an earlier run built.

Only fog is lifted for the carried ids (they join `sim.revealed`); nothing is completed or paid for.
The ids live in the new game's save through `revealed`; UI memory records which were carried.
"""
import json
import os

from .memory import remembered

TOPIC = "replay"


def built_routes(sim):
    """Ids the player built themselves, not what their society already had."""
    return sorted(set(sim.done) - set(sim.granted))


def routes_path(session):
    return session + ".routes.json"


def read_known_routes(path):
    """The id list in a known-routes file; empty when missing or unreadable."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    return [item for item in data if isinstance(item, str)] if isinstance(data, list) else []


def write_known_routes(sim, path):
    """Write what this run built plus what it was carrying, so lessons accumulate across runs."""
    carried = remembered(sim, TOPIC).get("carried", [])
    ids = sorted(set(built_routes(sim)) | set(carried))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(ids, handle)
    return ids


def record_end_of_run(sim, session):
    """Write the known-routes file beside the session. Returns the ids, or None with no session."""
    return write_known_routes(sim, routes_path(session)) if session else None


def apply_known_routes(sim, route_ids, node_ids):
    """Lift fog for the ids this game's tree has. Returns the ids applied (none when fog is off)."""
    if not sim.fog:
        return []
    applied = sorted(set(route_ids) & set(node_ids))
    sim.revealed = set(sim.revealed) | set(applied)
    remembered(sim, TOPIC)["carried"] = applied
    return applied


def fog_off_note():
    return "Known routes only lift fog, and this game has none, so there is nothing to carry over."
